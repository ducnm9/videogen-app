# Deployment Guide for VPS with Docker

## Requirements
- VPS with Linux OS (Ubuntu/Debian recommended)
- Docker and Docker Compose installed
- Port 9000 open on firewall

## Step 1: Install Docker on VPS

### On Ubuntu/Debian:
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker using the official script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Add user to docker group (to run docker without sudo)
sudo usermod -aG docker $USER

# Logout and login again to apply group changes
```

## Step 2: Upload Code to VPS

### Method 1: Using Git (Recommended)
```bash
# On VPS
cd ~
git clone <repository-url>
cd videogen-main
```

### Method 2: Using SCP
```bash
# On local machine
scp -r videogen-main user@your-vps-ip:/home/user/
```

### Method 3: Using SFTP or FileZilla
- Connect to VPS via SFTP
- Upload entire project folder

## Step 3: Build and Run Docker

```bash
# Navigate to project directory
cd videogen-main

# Build Docker image
docker-compose build

# Run container in detached mode
docker-compose up -d

# Check container status
docker-compose ps

# View logs in real-time
docker-compose logs -f
```

## Step 4: Test the Application

```bash
# Test API from VPS (local request)
curl -X POST http://localhost:9000/convert \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "URL_TO_AUDIO",
    "image_urls": ["URL_TO_IMAGE1", "URL_TO_IMAGE2"]
  }'
```

Or test from external network:
```bash
# Test API from your local machine
curl -X POST http://YOUR_VPS_IP:9000/convert \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "URL_TO_AUDIO",
    "image_urls": ["URL_TO_IMAGE1", "URL_TO_IMAGE2"]
  }'
```

## Step 5: Configure Firewall (if needed)

```bash
# Open port 9000 for TCP connections
sudo ufw allow 9000/tcp

# Check firewall status
sudo ufw status
```

## Useful Docker Commands

```bash
# Stop container
docker-compose down

# Restart container
docker-compose restart

# View logs in real-time
docker-compose logs -f

# Rebuild and restart (after code changes)
docker-compose down
docker-compose build
docker-compose up -d

# Remove everything (including volumes)
docker-compose down -v

# Enter container shell for debugging
docker-compose exec videogen bash

# View resource usage (CPU, memory)
docker stats
```

## Configure Nginx Reverse Proxy (Recommended for production)

Create file `/etc/nginx/sites-available/videogen`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Allow large file uploads (100MB max)
    client_max_body_size 100M;

    location / {
        # Proxy requests to Docker container on port 9000
        proxy_pass http://localhost:9000;
        
        # Enable HTTP/1.1 for better connection handling
        proxy_http_version 1.1;
        
        # WebSocket support headers
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        
        # Pass original host header to backend
        proxy_set_header Host $host;
        
        # Cache bypass for upgraded connections
        proxy_cache_bypass $http_upgrade;
        
        # Pass real client IP address
        proxy_set_header X-Real-IP $remote_addr;
        
        # Pass forwarded IP chain
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Pass protocol (http or https)
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings for long video processing operations
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

Enable Nginx configuration:
```bash
# Create symbolic link to enable site
sudo ln -s /etc/nginx/sites-available/videogen /etc/nginx/sites-enabled/

# Test Nginx configuration for syntax errors
sudo nginx -t

# Restart Nginx to apply changes
sudo systemctl restart nginx
```

## Install SSL with Let's Encrypt (Optional)

```bash
# Install Certbot for automatic SSL certificate management
sudo apt install certbot python3-certbot-nginx -y

# Obtain and install SSL certificate for your domain
sudo certbot --nginx -d your-domain.com
```

## Backup and Restore

### Backup
```bash
# Stop container to ensure data consistency
docker-compose down

# Create compressed backup with date stamp
tar -czf backup-$(date +%Y%m%d).tar.gz uploads/ videos/

# Start container again
docker-compose up -d
```

### Restore
```bash
# Stop container
docker-compose down

# Extract backup (replace YYYYMMDD with actual date)
tar -xzf backup-YYYYMMDD.tar.gz

# Start container with restored data
docker-compose up -d
```

## Auto-start on VPS Reboot

Docker Compose already has `restart: unless-stopped` configured, so containers will automatically restart when VPS reboots.

## Monitoring and Logs

```bash
# View logs in real-time (last 100 lines)
docker-compose logs -f --tail=100

# Check disk space
df -h

# Check RAM usage
free -h

# Clean up old Docker images and containers
docker system prune -a
```

## Troubleshooting

### Container won't start:
```bash
# View detailed container logs
docker-compose logs videogen
```

### Port already in use:
```bash
# Find process using port 9000
sudo lsof -i :9000
# Or
sudo netstat -tulpn | grep 9000
```

### Not enough RAM/CPU:
- Reduce number of workers in Dockerfile (CMD line)
- Adjust `deploy.resources` in docker-compose.yml

### FFmpeg errors:
```bash
# Enter container and test ffmpeg
docker-compose exec videogen bash
ffmpeg -version
```

## Security

1. **Use environment variables for sensitive information**
2. **Implement rate limiting** (using Nginx or Flask-Limiter)
3. **Regular updates**:
   ```bash
   # Pull latest images
   docker-compose pull
   # Restart with new images
   docker-compose up -d
   ```
4. **Use HTTPS** (SSL certificate)
5. **Firewall**: Only open necessary ports

## Performance Tuning

To optimize performance, you can:
1. Increase number of workers in Gunicorn (if VPS has enough RAM)
2. Use Redis for caching
3. Optimize FFmpeg parameters in video.py
4. Use CDN to serve videos

## Contact & Support

If you encounter issues, check logs:
```bash
docker-compose logs -f
```
