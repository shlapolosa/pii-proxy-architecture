#!/bin/bash

# Startup script for PII Proxy Architecture Backend

set -e

echo "Starting PII Proxy Architecture Backend..."

# Check if required environment variables are set
required_vars=("LITELLM_MASTER_KEY" "ANTHROPIC_API_KEY" "OPENAI_API_KEY" "CLOUDFLARE_TUNNEL_TOKEN")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Environment variable $var is not set"
        exit 1
    fi
done

# Create necessary directories
mkdir -p logs
mkdir -p data

# Start services with Docker Compose
echo "Starting Docker services..."
docker-compose up -d

# Wait for services to start
echo "Waiting for services to initialize..."
sleep 10

# Check service status
echo "Checking service status..."
docker-compose ps

echo "Backend services started successfully!"
echo "API available at: https://api.pii-proxy.yourdomain.com"
echo "Frontend available at: https://app.pii-proxy.yourdomain.com"