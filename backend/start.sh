#!/bin/bash

# Startup script for PII Proxy Architecture Backend
# Supports two modes:
#   Standalone  — brings up its own postgres + redis (default)
#   Integrated  — reuses external postgres/redis from an existing Docker stack

set -e

echo "Starting PII Proxy Architecture Backend..."

# Ensure we're in the backend directory
cd "$(dirname "$0")"

# Load .env file if present
if [ -f .env ]; then
    echo "Loading environment from .env file..."
    set -a
    source .env
    set +a
fi

# Check required environment variables
required_vars=("ANTHROPIC_API_KEY" "POSTGRES_PASSWORD" "OLLAMA_API_BASE" "OLLAMA_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Environment variable $var is not set"
        echo "Copy .env.example to .env and fill in your values: cp .env.example .env"
        exit 1
    fi
done

# Warn about optional variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY is not set — OpenAI models will be unavailable"
fi

# Create necessary directories
mkdir -p logs
mkdir -p data

# Ensure pii-events.jsonl exists as a file (prevents Docker from creating it as a directory)
touch pii-events.jsonl

# ---------------------------------------------------------------------------
# Mode detection: integrated vs standalone
# ---------------------------------------------------------------------------
EXTERNAL_POSTGRES_CONTAINER="${EXTERNAL_POSTGRES_CONTAINER:-postgres}"
EXTERNAL_REDIS_CONTAINER="${EXTERNAL_REDIS_CONTAINER:-redis}"

detect_integrated_mode() {
    # Check if both external containers exist and are running
    local pg_running redis_running
    pg_running=$(docker inspect -f '{{.State.Running}}' "$EXTERNAL_POSTGRES_CONTAINER" 2>/dev/null || echo "false")
    redis_running=$(docker inspect -f '{{.State.Running}}' "$EXTERNAL_REDIS_CONTAINER" 2>/dev/null || echo "false")

    if [ "$pg_running" = "true" ] && [ "$redis_running" = "true" ]; then
        return 0  # integrated mode detected
    fi
    return 1  # standalone mode
}

# Determine mode: explicit override or auto-detect
if [ -n "$PII_INTEGRATED" ]; then
    if [ "$PII_INTEGRATED" = "true" ]; then
        MODE="integrated"
    else
        MODE="standalone"
    fi
else
    if detect_integrated_mode; then
        MODE="integrated"
        echo "Auto-detected external postgres + redis — using integrated mode"
    else
        MODE="standalone"
    fi
fi

echo "Mode: $MODE"

# ---------------------------------------------------------------------------
# Start services
# ---------------------------------------------------------------------------
if [ "$MODE" = "integrated" ]; then
    # Validate required integrated-mode settings
    if [ -z "$EXTERNAL_NETWORK" ]; then
        echo "Error: EXTERNAL_NETWORK must be set in integrated mode"
        echo "Set it to the Docker network of your external stack (e.g. homelab_default)"
        exit 1
    fi

    # Default DB/Redis hosts to external container names
    export PII_DB_HOST="${PII_DB_HOST:-$EXTERNAL_POSTGRES_CONTAINER}"
    export PII_DB_USER="${PII_DB_USER:-postgres}"
    export PII_DB_NAME="${PII_DB_NAME:-postgres}"
    export PII_REDIS_HOST="${PII_REDIS_HOST:-$EXTERNAL_REDIS_CONTAINER}"

    echo "Connecting to external postgres ($PII_DB_HOST) and redis ($PII_REDIS_HOST)"
    echo "External network: $EXTERNAL_NETWORK"

    # Start only litellm-proxy (no profile = no standalone services)
    docker compose up -d --build

    # Attach litellm-proxy to the external network (idempotent — ignores if already connected)
    echo "Connecting litellm-proxy to external network $EXTERNAL_NETWORK..."
    docker network connect "$EXTERNAL_NETWORK" litellm-proxy 2>/dev/null || true
else
    # Standalone: start everything including postgres + redis
    echo "Starting all services (standalone mode)..."
    COMPOSE_PROFILES=standalone docker compose up -d --build
fi

# ---------------------------------------------------------------------------
# Wait for services to become healthy
# ---------------------------------------------------------------------------
echo "Waiting for services to become healthy..."
max_wait=60
elapsed=0
while [ $elapsed -lt $max_wait ]; do
    # Check if all services are running/healthy
    unhealthy=$(docker compose ps --format json 2>/dev/null | grep -c '"Health":"starting"' || true)
    exited=$(docker compose ps --format json 2>/dev/null | grep -c '"State":"exited"' || true)

    if [ "$exited" -gt 0 ]; then
        echo "Error: One or more services exited unexpectedly"
        docker compose ps
        docker compose logs --tail=20
        exit 1
    fi

    if [ "$unhealthy" -eq 0 ]; then
        break
    fi

    sleep 2
    elapsed=$((elapsed + 2))
    echo "  ...waiting ($elapsed/${max_wait}s)"
done

if [ $elapsed -ge $max_wait ]; then
    echo "Warning: Timed out waiting for services to become healthy"
fi

# Check service status
echo ""
echo "Service status:"
docker compose ps

echo ""
echo "Backend services started successfully! (mode: $MODE)"
echo "API available at: http://localhost:8080"
echo "Health check:     curl http://localhost:8080/health"
