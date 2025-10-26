# Use Python 3.11 slim as base image
# Slim version is smaller and more efficient for production use
FROM python:3.11-slim

# Install FFmpeg and necessary system dependencies
# FFmpeg is required for video processing
# Clean up apt cache to reduce image size
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy requirements.txt first (for better Docker layer caching)
# If requirements don't change, this layer will be cached
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir reduces image size by not storing pip cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire source code into container
COPY . .

# Create necessary directories for file storage
# uploads: temporary storage for downloaded audio and images
# videos: output directory for generated video files
RUN mkdir -p uploads videos

# Expose port 9000 to allow external connections
EXPOSE 9000

# Install Gunicorn as production WSGI server
# Gunicorn is more robust than Flask's built-in development server
RUN pip install gunicorn

# Command to run the application
# --bind 0.0.0.0:9000: Listen on all network interfaces on port 9000
# --workers 4: Use 4 worker processes for handling concurrent requests
# --timeout 300: Set 5-minute timeout for long video processing operations
# video:app: Import 'app' from 'video.py'
CMD ["gunicorn", "--bind", "0.0.0.0:9000", "--workers", "4", "--timeout", "300", "video:app"]
