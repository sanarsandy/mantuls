#!/bin/bash

# Deployment Script for ManTuls Production
# Usage: ./deploy_prod.sh [API_URL]

echo "🚀 Starting ManTuls Production Deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Created .env from .env.example (mock) or ask admin for secrets."
    echo "Please create .env with OCR_SECRET_KEY and JWT_SECRET first."
    exit 1
fi

# Define API URL (default to localhost if not provided)
API_BASE_URL=${1:-"http://localhost:8000"}
echo "ℹ️  Using API Base URL: $API_BASE_URL"

# Export vars to ensuring they are picked up
export NUXT_PUBLIC_API_BASE=$API_BASE_URL

# Ensure JSON data files exist to prevent Docker from creating directories
if [ ! -f backend/config.json ]; then
    echo "📄 Creating initial backend/config.json..."
    echo "{}" > backend/config.json
    chmod 666 backend/config.json
fi

if [ ! -f backend/api_keys.json ]; then
    echo "🔑 Creating initial backend/api_keys.json..."
    echo "[]" > backend/api_keys.json
    chmod 666 backend/api_keys.json
fi

echo "📦 Building and Starting Containers..."
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d --build

# Check status
if [ $? -eq 0 ]; then
    echo "✅ Deployment Successful!"
    echo "🌐 Frontend running at: http://localhost:3011"
    echo "🔌 Backend running at: http://localhost:8011"
    echo ""
    echo "To monitor logs:"
    echo "  docker compose -f docker-compose.prod.yml logs -f"
else
    echo "❌ Deployment Failed!"
    exit 1
fi
