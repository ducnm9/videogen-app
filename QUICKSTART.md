# 🚀 Quick Start - Deploy to VPS in 5 Minutes

## Step 1: Prepare VPS

### Minimum Requirements:
- **RAM**: 2GB (4GB recommended)
- **CPU**: 2 cores
- **Disk**: 20GB
- **OS**: Ubuntu 20.04 or 22.04

### Login to VPS:
```bash
ssh root@YOUR_VPS_IP
# or
ssh user@YOUR_VPS_IP
```

## Step 2: Install Docker (1-2 minutes)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt update
sudo apt install docker-compose -y

# Verify installation
docker --version
docker-compose --version
```

## Step 3: Upload Code to VPS

### Method A: Using Git (Recommended)
```bash
cd ~
git clone YOUR_REPO_URL
cd videogen-main
```

### Method B: Using SCP from local machine
```bash
# Run this on your local machine (not on VPS)
cd videogen-main
scp -r ./* user@YOUR_VPS_IP:~/videogen-main/
```

### Method C: Using FileZilla/WinSCP
1. Connect to VPS via SFTP
2. Upload the entire `videogen-main` folder

## Step 4: Deploy (30 seconds)

```bash
# Navigate to project directory
cd videogen-main

# Run deploy script (or manual deployment in Step 5)
chmod +x deploy.sh
./deploy.sh
```

**OR** Manual deployment:

```bash
# Create directories for uploads and videos
mkdir -p uploads videos

# Build and run containers
docker-compose up -d

# View logs
docker-compose logs -f
```

## Step 5: Open Firewall Port

```bash
# If using UFW (Uncomplicated Firewall)
sudo ufw allow 9000/tcp
sudo ufw status

# If using iptables
sudo iptables -A INPUT -p tcp --dport 9000 -j ACCEPT
sudo iptables-save
```

## Step 6: Test API ✅

### Test from VPS:
```bash
curl http://localhost:9000/
```

### Test from local machine:
```bash
curl http://YOUR_VPS_IP:9000/
```

### Test convert API endpoint:
```bash
# Send POST request to convert endpoint with audio and images
curl -X POST http://YOUR_VPS_IP:9000/convert \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "image_urls": [
      "https://picsum.photos/1280/720?random=1",
      "https://picsum.photos/1280/720?random=2"
    ]
  }' \
  --output test-video.mp4

# If successful, you'll get a test-video.mp4 file
```

## ✅ Done! Your API is now running

- **URL**: `http://YOUR_VPS_IP:9000`
- **Endpoint**: `POST /convert`

---

## 🔧 Common Commands

```bash
# View logs in real-time
docker-compose logs -f

# Restart containers
docker-compose restart

# Stop containers
docker-compose down

# Start containers again
docker-compose up -d

# Check container status
docker-compose ps

# Update to new code
git pull                    # If using Git
docker-compose down         # Stop running containers
docker-compose build        # Rebuild images with new code
docker-compose up -d        # Start containers in detached mode
```

---

## 🌐 Setup Domain & HTTPS (Optional - 5 minutes)

### 1. Point Domain to VPS
Create an A Record:
```
Type: A
Name: api (or @)
Value: YOUR_VPS_IP
TTL: 300
```

### 2. Install Nginx
```bash
sudo apt update
sudo apt install nginx -y
```

### 3. Configure Nginx
```bash
# Open Nginx configuration file
sudo nano /etc/nginx/sites-available/videogen
```

Paste this configuration:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    # Allow large file uploads (100MB max)
    client_max_body_size 100M;

    location / {
        # Proxy all requests to local Docker container on port 9000
        proxy_pass http://localhost:9000;
        
        # Pass original host header
        proxy_set_header Host $host;
        
        # Pass real client IP address
        proxy_set_header X-Real-IP $remote_addr;
        
        # Pass forwarded IP chain
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Set timeouts for long-running video processing
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

Activate configuration:
```bash
# Create symbolic link to enable the site
sudo ln -s /etc/nginx/sites-available/videogen /etc/nginx/sites-enabled/

# Test Nginx configuration for syntax errors
sudo nginx -t

# Restart Nginx to apply changes
sudo systemctl restart nginx
```

### 4. Install SSL Certificate (HTTPS)
```bash
# Install Certbot for automatic SSL certificate
sudo apt install certbot python3-certbot-nginx -y

# Obtain and install SSL certificate
sudo certbot --nginx -d api.yourdomain.com
```

Select `2` to redirect HTTP to HTTPS automatically.

**Done!** Your API is now accessible via:
- `https://api.yourdomain.com`

---

## 🐛 Troubleshooting

### ❌ Port 9000 is already in use
```bash
# Find process using the port
sudo lsof -i :9000

# Kill the process (replace <PID> with actual process ID)
sudo kill -9 <PID>
```

### ❌ Container won't start
```bash
# View detailed logs
docker-compose logs

# Check Docker service status
sudo systemctl status docker
```

### ❌ Cannot connect from outside
```bash
# Check firewall status
sudo ufw status

# Check if port is open and listening
sudo netstat -tulpn | grep 9000

# Open the port if needed
sudo ufw allow 9000/tcp
```

### ❌ FFmpeg errors
```bash
# Enter the container
docker-compose exec videogen bash

# Test FFmpeg installation
ffmpeg -version
```

### ❌ Out of memory errors
```bash
# Reduce workers in Dockerfile (CMD line)
# Change from: --workers 4
# To: --workers 2

# Rebuild container with new settings
docker-compose down
docker-compose build
docker-compose up -d
```

---

## 📊 Monitoring

### View resource usage:
```bash
# View Docker container resource usage in real-time
docker stats

# View server resources (interactive)
htop
# or (basic view)
top

# Check disk space
df -h
```

### Auto cleanup:
```bash
# Clean up old Docker images and containers
docker system prune -a

# Setup auto cleanup (runs weekly on Sunday at midnight)
echo "0 0 * * 0 docker system prune -f" | sudo crontab -
```

---

## 🔐 Security Recommendations

1. **Change default port** (from 9000 to another port)
2. **Add authentication** to the API
3. **Rate limiting** to prevent spam/abuse
4. **Firewall**: Only open necessary ports
5. **Regular updates**:
   ```bash
   # Update system packages regularly
   sudo apt update && sudo apt upgrade -y
   ```

---

## 💡 Tips

- **Regular backups**: `tar -czf backup.tar.gz uploads/ videos/`
- **Monitor logs**: `docker-compose logs -f`
- **Auto restart**: Containers automatically restart when VPS reboots (already configured)
- **Scale up**: Increase workers if your VPS has more RAM

---

## 📞 Need Help?

1. View logs: `docker-compose logs -f`
2. Read [DEPLOY.md](DEPLOY.md) for more details
3. Check container status: `docker-compose ps`
4. Test API: `curl http://localhost:9000/`

---

**🎉 Congratulations! Your API is now online!**
