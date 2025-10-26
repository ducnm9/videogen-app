#!/bin/bash

# Quick API test script
# Usage: ./test-api.sh [SERVER_IP]

# Set server address (default to localhost if not provided)
SERVER=${1:-localhost}
PORT=9000
URL="http://${SERVER}:${PORT}"

echo "========================================="
echo "  VideoGen API Test Script"
echo "========================================="
echo ""
echo "Testing API at: $URL"
echo ""

# Test 1: Health check
echo "📋 Test 1: Health Check..."
response=$(curl -s -o /dev/null -w "%{http_code}" $URL/)
if [ "$response" != "000" ]; then
    echo "✅ Server is responding (HTTP $response)"
else
    echo "❌ Cannot connect to server"
    exit 1
fi
echo ""

# Test 2: API Convert with sample data
echo "📋 Test 2: Convert API..."
echo "Sending request to $URL/convert"
echo ""

# Send POST request with sample audio and images
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST $URL/convert \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "image_urls": [
      "https://picsum.photos/1280/720?random=1",
      "https://picsum.photos/1280/720?random=2",
      "https://picsum.photos/1280/720?random=3"
    ]
  }' \
  --output test-video.mp4 \
  -D test-headers.txt)

# Extract HTTP status code from response
http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)

# Extract filename from Content-Disposition header if available
video_filename=""
if [ -f "test-headers.txt" ]; then
    video_filename=$(grep -i "Content-Disposition" test-headers.txt | sed -n 's/.*filename="\?\([^"]*\)"\?.*/\1/p' | tr -d '\r\n')
    rm -f test-headers.txt
fi

if [ "$http_code" == "200" ]; then
    echo "✅ Video created successfully!"
    echo "📁 Video saved as: test-video.mp4"
    if [ -n "$video_filename" ]; then
        echo "📝 Original filename: $video_filename"
    fi
    # Check if file exists and display size
    if [ -f "test-video.mp4" ]; then
        size=$(du -h test-video.mp4 | cut -f1)
        echo "📊 File size: $size"
    fi
else
    echo "❌ API returned error (HTTP $http_code)"
    echo "Response: $response"
fi
echo ""

# Test 3: Test with invalid data to check error handling
echo "📋 Test 3: Error Handling (Convert API)..."
response=$(curl -s -X POST $URL/convert \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}')

if echo "$response" | grep -q "error"; then
    echo "✅ Error handling works correctly"
else
    echo "⚠️  Unexpected response: $response"
fi
echo ""

# Test 4: Delete API with valid filename
echo "📋 Test 4: Delete API (Valid Filename)..."
if [ -n "$video_filename" ]; then
    echo "Attempting to delete: $video_filename"
    response=$(curl -s -X POST $URL/delete \
      -H "Content-Type: application/json" \
      -d "{\"filename\": \"$video_filename\"}")
    
    if echo "$response" | grep -q "success"; then
        echo "✅ Video deleted successfully!"
        echo "Response: $response"
    else
        echo "⚠️  Delete response: $response"
    fi
else
    echo "⚠️  Skipping: No video filename available from previous test"
fi
echo ""

# Test 5: Delete API with non-existent file (error handling)
echo "📋 Test 5: Delete API Error Handling..."
response=$(curl -s -X POST $URL/delete \
  -H "Content-Type: application/json" \
  -d '{"filename": "non-existent-video-12345.mp4"}')

if echo "$response" | grep -q "error"; then
    echo "✅ Error handling works correctly (file not found)"
    echo "Response: $response"
else
    echo "⚠️  Unexpected response: $response"
fi
echo ""

# Test 6: Delete API with missing filename field
echo "📋 Test 6: Delete API Validation..."
response=$(curl -s -X POST $URL/delete \
  -H "Content-Type: application/json" \
  -d '{}')

if echo "$response" | grep -q "filename is required"; then
    echo "✅ Input validation works correctly"
else
    echo "⚠️  Unexpected response: $response"
fi
echo ""

echo "========================================="
echo "  All tests completed! ✅"
echo "========================================="
echo ""
echo "📖 API Usage Examples:"
echo ""
echo "1. Convert video:"
echo "   curl -X POST $URL/convert \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{"
echo "       \"audio_url\": \"YOUR_AUDIO_URL\","
echo "       \"image_urls\": [\"IMAGE_1\", \"IMAGE_2\"]"
echo "     }' \\"
echo "     --output my-video.mp4"
echo ""
echo "2. Delete video:"
echo "   curl -X POST $URL/delete \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"filename\": \"video_filename.mp4\"}'"
echo ""
