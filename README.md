# VideoGen - API to Create Videos from Audio and Images

Flask API to create videos from audio and multiple images using FFmpeg.

## Features

- Receive audio URL and image URLs via API
- Download and process audio & images
- Create videos with FFmpeg (each image displays for 3 seconds)
- Automatically resize images to be compatible with FFmpeg
- Return MP4 video file

## Requirements

- Python 3.11+
- FFmpeg
- Docker & Docker Compose (for deployment)

## Local Installation (Without Docker)

```bash
# Clone repository
git clone <repo-url>
cd videogen-main

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (if not already installed)
# Ubuntu/Debian:
sudo apt install ffmpeg

# macOS:
brew install ffmpeg

# Run application
python video.py
```

## Deploy with Docker (Recommended)

### Quick Start

```bash
# Build and run containers
docker-compose up -d

# View logs in real-time
docker-compose logs -f

# Stop containers
docker-compose down
```

### Deploy to VPS

See detailed guide at [DEPLOY.md](DEPLOY.md)

**Summary of steps:**

1. Install Docker on VPS
2. Upload code to VPS
3. Run `docker-compose up -d`
4. Configure firewall to open port 9000
5. (Optional) Configure Nginx reverse proxy

## API Usage

### Endpoint: POST /convert

```bash
curl -X POST http://localhost:9000/convert \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://example.com/audio.mp3",
    "image_urls": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg",
      "https://example.com/image3.jpg"
    ]
  }' \
  --output video.mp4
```

### Request Body

```json
{
  "audio_url": "URL of audio file (mp3, wav)",
  "image_urls": ["Array of image URLs (jpg, png, jpeg, webp)"]
}
```

### Response

- **Success**: Returns MP4 video file
- **Error**: JSON with error message

## Project Structure

```
videogen-main/
├── video.py              # Main Flask app
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
├── .dockerignore        # Docker ignore files
├── DEPLOY.md           # Detailed deployment guide
├── uploads/            # Temporary folder for audio & images
└── videos/             # Folder containing generated videos
```

## Configuration

### Port
- Default: `9000`
- Change in `video.py` or `docker-compose.yml`

### Workers (for Production)
- Default: 4 workers (in Dockerfile)
- Adjust in Dockerfile CMD line

### Timeout
- Default: 300 seconds
- Adjust in Dockerfile (gunicorn --timeout)

## Troubleshooting

### FFmpeg not found
```bash
# Check FFmpeg installation
ffmpeg -version

# Inside Docker container
docker-compose exec videogen ffmpeg -version
```

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8000:9000"  # host:container
```

### Memory/CPU errors
- Reduce number of workers
- Increase timeout
- Adjust resources in docker-compose.yml

## Development

```bash
# Run in development mode
python video.py

# App will run at http://localhost:9000
# Debug mode: enabled
```

## Production

```bash
# Use Docker Compose
docker-compose up -d

# Or with Gunicorn directly
gunicorn --bind 0.0.0.0:9000 --workers 4 --timeout 300 video:app
```

## Security

⚠️ **Important notes:**
- Add authentication for production
- Limit file upload size
- Implement rate limiting
- Use HTTPS
- Validate input URLs

## Performance

- Each image: 3 seconds in video
- Video output: 1280x720, 30fps, H.264
- FFmpeg preset: medium (balance between speed and quality)
- Threads: 4 (adjustable in video.py)

## License

MIT License

## Support

Having issues? Check [DEPLOY.md](DEPLOY.md) or open an issue.
