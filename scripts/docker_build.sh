#!/bin/bash

# Docker build and test script

echo "========================================="
echo "Building Docker Image"
echo "========================================="
echo ""

# Build the image
echo "Building university-hub:latest..."
docker build -t university-hub:latest .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker build failed"
    exit 1
fi

echo ""
echo "========================================="
echo "Docker image ready!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Test locally: docker-compose up"
echo "2. Push to registry: docker tag university-hub:latest your-registry/university-hub:latest"
echo "3. Deploy to Hamravesh"
echo ""

