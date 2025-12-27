#!/bin/bash

# Buckingham Conspiracy Hub - Docker Startup Script

# Default values
PORT=8502
IMAGE_NAME="buckingham-conspiracy-hub"
CONTAINER_NAME="buckingham-conspiracy-hub"
DATA_DIR=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -d|--data-dir)
            DATA_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [-p|--port PORT] [-d|--data-dir PATH]"
            exit 1
            ;;
    esac
done

echo "🎸 Buckingham Conspiracy Hub - Starting..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Navigate to the script directory
cd "$(dirname "$0")"

# Stop and remove existing container if running
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "🛑 Stopping existing container..."
    docker stop $CONTAINER_NAME > /dev/null 2>&1
    docker rm $CONTAINER_NAME > /dev/null 2>&1
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME .

if [ $? -ne 0 ]; then
    echo "❌ Failed to build Docker image"
    exit 1
fi

echo ""
echo "🚀 Starting application on port $PORT..."

# Run the container with volume mounts for data persistence
if [ -n "$DATA_DIR" ]; then
    mkdir -p "$DATA_DIR"
    docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:8501 \
        -e BCH_DATA_DIR=/data \
        -v "$DATA_DIR:/data" \
        --restart unless-stopped \
        $IMAGE_NAME
else
    docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:8501 \
        -v "$(pwd)/setlists:/app/setlists" \
        -v "$(pwd)/songlist:/app/songlist" \
        -v "$(pwd)/song_data:/app/song_data" \
        --restart unless-stopped \
        $IMAGE_NAME
fi

# Wait a moment for the container to start
sleep 3

# Check if container is running
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo ""
    echo "✅ Buckingham Conspiracy Hub is running!"
    echo ""
    echo "📱 Access the application at: http://localhost:$PORT"
    echo ""
    echo "Useful commands:"
    echo "  • View logs:        docker logs -f $CONTAINER_NAME"
    echo "  • Stop app:         docker stop $CONTAINER_NAME"
    echo "  • Remove container: docker rm $CONTAINER_NAME"
    echo "  • Restart app:      docker restart $CONTAINER_NAME"
    echo ""
else
    echo ""
    echo "❌ Failed to start the application. Check logs with:"
    echo "   docker logs $CONTAINER_NAME"
    exit 1
fi
