#!/bin/bash

# Quick deployment script for VPS
# Usage: ./deploy.sh

echo "========================================="
echo "  VideoGen Docker Deployment Script"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo "Please install Docker first:"
    echo "curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "sudo sh get-docker.sh"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed!"
    echo "Please install Docker Compose:"
    echo "sudo apt install docker-compose -y"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create necessary directories
echo "📁 Creating uploads and videos directories..."
mkdir -p uploads videos
echo "✅ Directories created"
echo ""

# Build Docker image
echo "🔨 Building Docker image..."
docker-compose build
if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi
echo "✅ Build successful"
echo ""

# Stop old container if exists
echo "🛑 Stopping old container (if exists)..."
docker-compose down
echo ""

# Start new container
echo "🚀 Starting container..."
docker-compose up -d
if [ $? -ne 0 ]; then
    echo "❌ Failed to start container!"
    exit 1
fi
echo "✅ Container started"
echo ""

# Check container status
echo "📊 Container status:"
docker-compose ps
echo ""

# Wait for application to start
echo "⏳ Waiting for application to start (5 seconds)..."
sleep 5
echo ""

# Test API
echo "🧪 Testing API..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/)
if [ "$response" != "000" ]; then
    echo "✅ API is running! (HTTP Status: $response)"
else
    echo "⚠️  Cannot connect to API. Check logs:"
    echo "docker-compose logs -f"
fi
echo ""

# Display information
echo "========================================="
echo "  Deployment successful! 🎉"
echo "========================================="
echo ""
echo "📝 Information:"
echo "  - API URL: http://YOUR_SERVER_IP:9000"
echo "  - Endpoint: POST /convert"
echo ""
echo "📋 Useful commands:"
echo "  - View logs:      docker-compose logs -f"
echo "  - Restart:       docker-compose restart"
echo "  - Stop:          docker-compose down"
echo "  - View status:   docker-compose ps"
echo ""
echo "📖 See full guide at DEPLOY.md"
echo ""

# Display logs
echo "📊 Real-time logs (Ctrl+C to exit):"
echo ""
docker-compose logs -f
