import os
import subprocess
import uuid
import requests
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from flask_cors import CORS
from PIL import Image, ImageOps
from io import BytesIO

# Initialize Flask application
app = Flask(__name__)

# Enable CORS to allow cross-origin requests from web browsers
CORS(app)

# Set up upload folders (temporary storage for the files)
UPLOAD_FOLDER = 'uploads'  # Temporary storage for downloaded audio and images
VIDEO_FOLDER = 'videos'    # Output folder for generated videos
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'jpg', 'png', 'jpeg', 'webp'}

# Make sure the folders exist, create them if they don't
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)

# Configure the Flask app with upload folder path
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def resize_image_exact(image_url: str, new_width: int, new_height: int, output_filename: str = "resized_exact.jpg") -> str | None:
    """
    Downloads an image from a URL and resizes it to the exact new_width and new_height.
    Note: This might distort the image if the aspect ratio is not maintained.

    :param image_url: The URL of the input image.
    :param new_width: The desired new width in pixels.
    :param new_height: The desired new height in pixels.
    :param output_filename: The filename to save the resized image.
    :return: The saved file path or None if an error occurs.
    """

    output_filename = str(uuid.uuid4()) + "_" + output_filename

    try:
        # 1. Download the image data
        response = requests.get(image_url)
        response.raise_for_status() # Check for HTTP errors

        # 2. Open the image using Pillow from byte content
        image_data = BytesIO(response.content)
        img = Image.open(image_data)

        # 3. Resize the image to the exact dimensions
        new_size = (new_width, new_height)
        # Use Image.Resampling.LANCZOS for high-quality resampling, especially for downscaling
        # resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
        cropped_and_resized_img = ImageOps.fit(
            img,
            new_size,
            method=Image.Resampling.LANCZOS,  # Use LANCZOS for best quality
            centering=(0.5, 0.5)  # Centering tuple (x, y) - 0.5 means center
        )
        
        # 4. Save the resized image
        output_format = img.format if img.format else "JPEG"
        cropped_and_resized_img.save(output_filename, format=output_format)

        print(f"Image successfully resized and saved at: {output_filename}")
        print(f"Original size: {img.size}, New size: {cropped_and_resized_img.size}")

        return output_filename
    
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None
    except Exception as e:
        print(f"Error processing image: {e}")
        return None


# Function to check if file extension is allowed
def allowed_file(filename):
    """
    Check if the file has an allowed extension.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        Boolean: True if extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Function to get the audio duration using ffmpeg
def get_audio_duration(audio_path):
    """
    Extract audio duration from an audio file using FFmpeg.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        float: Duration in seconds, or 0 if unable to determine
    """
    # Run FFmpeg command to get file information
    cmd = ['ffmpeg', '-i', audio_path]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    
    # Parse the duration from the ffmpeg output
    # FFmpeg outputs format: Duration: HH:MM:SS.ms
    for line in result.stderr.splitlines():
        if 'Duration' in line:
            duration_str = line.split('Duration:')[1].split(',')[0].strip()
            hours, minutes, seconds = map(float, duration_str.split(':'))
            # Convert to total seconds
            return hours * 3600 + minutes * 60 + seconds
    return 0


# Function to resize images (Fix FFmpeg issue: height must be divisible by 2)
def resize_image(image_path):
    """
    Resize image to ensure width and height are even numbers.
    This is required by FFmpeg's H.264 encoder which needs dimensions divisible by 2.
    
    Args:
        image_path: Path to the image file to resize
    """
    with Image.open(image_path) as img:
        width, height = img.size
        
        # Ensure both width and height are even (divisible by 2)
        # Add 1 pixel if dimension is odd
        if width % 2 != 0:
            width += 1
        if height % 2 != 0:
            height += 1

        # Resize and save the image with corrected dimensions
        resized_img = img.resize((width, height))
        resized_img.save(image_path)


# Function to download files from a given URL and save them
def download_file(url, extension, folder):
    """
    Download a file from URL and save it to the specified folder.
    Images are automatically resized to meet FFmpeg requirements.
    
    Args:
        url: URL of the file to download
        extension: File extension (mp3, jpg, etc.)
        folder: Destination folder to save the file
        
    Returns:
        str: Path to the downloaded file, or None if download failed
    """
    try:
        # Stream download to handle large files efficiently
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            # Generate unique filename using UUID to avoid conflicts
            filename = f"{uuid.uuid4()}.{extension}"
            file_path = os.path.join(folder, filename)
            
            # Write file in chunks to avoid memory issues with large files
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)

            # Resize if it's an image to ensure compatibility with FFmpeg
            if extension in {"jpg", "png", "jpeg", "webp"}:
                resize_image(file_path)

            return file_path
    except Exception as e:
        print(f"Error downloading file from {url}: {e}")
    return None


# Route to convert audio and images (from URLs) into a video
@app.route('/convert', methods=['POST'])
def convert_to_video():
    """
    API endpoint to create a video from audio and images.
    
    Expected JSON payload:
    {
        "audio_url": "URL to audio file (mp3, wav)",
        "image_urls": ["URL1", "URL2", ...] - Array of image URLs
    }
    
    Returns:
        MP4 video file on success, or JSON error message on failure
    """
    data = request.json

    # Validate required fields
    if 'audio_url' not in data or 'image_urls' not in data:
        return jsonify({"error": "audio_url and image_urls are required."}), 400

    # Download audio file from provided URL
    audio_url = data['audio_url']
    audio_path = download_file(audio_url, "mp3", UPLOAD_FOLDER)
    if not audio_path:
        return jsonify({"error": "Failed to download audio file."}), 400

    # Download all image files from provided URLs
    image_urls = data['image_urls']
    image_paths = []
    for img_url in image_urls:
        img_path = download_file(img_url, "jpg", UPLOAD_FOLDER)
        if img_path:
            image_paths.append(img_path)

    # Validate that at least one image was downloaded successfully
    if not image_paths:
        return jsonify({"error": "No valid images downloaded."}), 400

    # Get the audio duration to calculate how many images are needed
    audio_duration = get_audio_duration(audio_path)
    if audio_duration == 0:
        return jsonify({"error": "Could not determine the audio duration."}), 500

    # Calculate if we need to repeat images to cover entire audio duration
    # Each image displays for 3 seconds
    num_images = len(image_paths)
    if num_images * 3 < audio_duration:  # If images can't cover entire duration with 3 sec per image
        repeat_count = int(audio_duration // 3) + 1  # Calculate how many times to repeat images
        image_paths = image_paths * repeat_count  # Repeat the images list

    # Generate unique filenames using UUID to avoid conflicts
    video_filename = str(uuid.uuid4()) + "_output_video.mp4"
    video_path = os.path.join(VIDEO_FOLDER, video_filename)

    img_sequence_filename = str(uuid.uuid4()) + "_img_sequence.txt"
    img_sequence_file = os.path.join(UPLOAD_FOLDER, img_sequence_filename)

    # Create the video using ffmpeg
    try:
        # Create a concat demuxer file for FFmpeg
        # This file lists all images and their display duration
        with open(img_sequence_file, "w") as f:
            for image in image_paths:
                f.write(f"file '{os.path.abspath(image)}'\n")  # Use absolute path for images
                f.write(f"duration 3\n")  # Each image lasts 3 seconds

        # Prepare the ffmpeg command to create the video with images and audio
        # Command breakdown:
        # -y: Overwrite output file if it exists
        # -f concat: Use concat demuxer to read image sequence
        # -safe 0: Allow absolute file paths
        # -i img_sequence_file: Input image sequence
        # -i audio_path: Input audio file
        # -c:v libx264: Use H.264 video codec
        # -preset medium: Balance between encoding speed and compression
        # -r 30: Set frame rate to 30 fps
        # -pix_fmt yuv420p: Pixel format for maximum compatibility
        # -vf scale=1280:720: Scale video to 1280x720 resolution
        # -t audio_duration: Limit video duration to match audio
        # -threads 4: Use 4 threads for faster encoding
        # -max_muxing_queue_size 1024: Increase buffer to prevent sync issues
        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', img_sequence_file,
            '-i', audio_path,
            '-c:v', 'libx264', '-preset', 'medium', '-r', '25', '-pix_fmt', 'yuv420p',
            '-vf', 'scale=720:1280', '-t', str(audio_duration), '-threads', '4',
            '-max_muxing_queue_size', '1024', video_path
        ]
        # Execute FFmpeg command
        subprocess.run(cmd, check=True)

        # Return the generated video file as an attachment for download
        return send_file(video_path, as_attachment=True)

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Error during video generation: {e}"}), 500
    finally:
        # Clean up temporary files after success or error
        # This ensures we don't fill up disk space with temp files
        os.remove(audio_path)
        for image_path in image_paths:
            if os.path.exists(image_path):  # Only remove image if it exists
                os.remove(image_path)
        if os.path.exists(img_sequence_file):
            os.remove(img_sequence_file)


# Route to delete video by filename
@app.route('/delete', methods=['POST', 'DELETE'])
def delete_video():
    """
    API endpoint to delete a video file by filename.
    
    Expected JSON payload:
    {
        "filename": "video_filename.mp4"
    }
    
    Returns:
        JSON response with status message
    """
    data = request.json
    
    # Validate required field
    if 'filename' not in data:
        return jsonify({
            "status": "error",
            "message": "filename is required."
        }), 400
    
    filename = data['filename']
    
    # Secure the filename to prevent directory traversal attacks
    filename = secure_filename(filename)
    
    # Construct the full path to the video file
    video_path = os.path.join(VIDEO_FOLDER, filename)
    
    # Check if the file exists
    if not os.path.exists(video_path):
        return jsonify({
            "status": "error",
            "message": f"Video file '{filename}' not found."
        }), 404
    
    # Check if the path is actually a file (not a directory)
    if not os.path.isfile(video_path):
        return jsonify({
            "status": "error",
            "message": f"'{filename}' is not a valid file."
        }), 400
    
    # Try to delete the file
    try:
        os.remove(video_path)
        return jsonify({
            "status": "success",
            "message": f"Video file '{filename}' has been deleted successfully."
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to delete video file: {str(e)}"
        }), 500

# make router get resize-image
@app.route('/resize-image', methods=['GET'])
def resize_image():
    """
    API endpoint to resize an image to exact dimensions.

    Query parameters:
    - width: The target width (in pixels)
    - height: The target height (in pixels)

    Returns:
        JSON response with status message
    """
    width = request.args.get('width', type=int)
    height = request.args.get('height', type=int)
    url = request.args.get('url', type=str)

    # Validate required parameters
    if not width or not height or not url:
        return jsonify({
            "status": "error",
            "message": "Both width and height are required."
        }), 400

    result = resize_image_exact(url, width, height)
    if not result:
        return jsonify({
            "status": "error",
            "message": "Failed to resize image."
        }), 500
    return send_file(result)

# Run the Flask application
if __name__ == '__main__':
    # Debug mode enabled for development
    # Port 9000 is the default port for this application
    app.run(debug=True, port=9000)
