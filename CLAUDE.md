# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PII-aware LLM routing proxy. Intercepts LLM requests, scans for PII using Microsoft Presidio, and routes sensitive requests to a local Ollama model instead of cloud providers (Anthropic/OpenAI). Non-sensitive requests go to the user's preferred cloud model.

## Commands

### Backend setup
```bash
cd backend
./install.sh              # Creates venv, installs deps, downloads spaCy model
source venv/bin/activate
```

### Run services (Docker)
```bash
cd backend
./start.sh                # Requires env vars: LITELLM_MASTER_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, CLOUDFLARE_TUNNEL_TOKEN
docker-compose up -d      # Or start individually
docker-compose ps         # Check status
docker-compose logs -f    # View logs
```

### Run tests
```bash
cd backend
python test_pii_detection.py        # PII detection unit tests (standalone script, not pytest)
pytest tests/integration            # Integration tests
```

### Linting/formatting
```bash
cd backend
black .
flake8
mypy .
```

## Architecture

### Request Flow
1. Client sends chat completion request to **Caddy** (HTTPS termination, auth)
2. Caddy forwards to **LiteLLM Proxy** (unified LLM API gateway, port 8000)
3. **PIIMiddleware** (`litellm_middleware.py`) intercepts the request:
   - Extracts all message content (including multi-modal)
   - Calls **PIIDetectionService** (`pii_detection_service.py`) which uses Microsoft Presidio
   - If PII detected → routes to local `llama3` (Ollama)
   - If no PII → routes to user's preferred cloud model
   - Fail-safe: routes to local model on any detection error
4. Response is enriched with PII metadata (`pii_detected`, `pii_risk_score`, `model_switched`)

### Key Backend Modules
- **`litellm_middleware.py`** — Central orchestrator. `PIIMiddleware` has `preprocess_request()` (PII scan + model routing) and `postprocess_response()` (metadata injection). Global instance: `pii_middleware`.
- **`pii_detection_service.py`** — Wraps Microsoft Presidio. `detect_pii()` returns `(has_pii, entities, risk_score)`. Global instance: `pii_service`.
- **`custom_recognizers.py`** — Domain-specific Presidio recognizers: customer IDs (`CUST-######`), employee IDs (`EMP-#####`), project codes (`PROJ-XX-###`), internal hostnames, medical terms, financial accounts.
- **`performance_optimizer.py`** — Caching (content hash → result), request batching, resource pooling, circuit breaker.
- **`error_handler.py`** — Fallback strategies when PII detection fails: block, sanitize, warn, or route-to-local (default).
- **`notification_handler.py`** — Generates user-facing alerts for PII detection, model switches, errors.
- **`auth.py`** — API key + JWT authentication, session management.

### Infrastructure (Docker Compose)
Six services on `pii-proxy-network` bridge:
- **litellm-proxy** (port 8000) — LLM gateway, configured via `config.yaml`
- **ollama** (port 11434) — Local model runner
- **postgres** (port 5432) — Audit logs (`pii_proxy_db`, user `pii_user`)
- **redis** (port 6379) — Caching layer
- **caddy** (ports 80/443) — Reverse proxy with TLS
- **cloudflared** — Cloudflare tunnel for external access

### Frontend (`/frontend`)
React/TypeScript components (not a full app scaffold — individual component files):
- **`App.tsx`** — Chat interface with integrated model selection and notifications
- **`api_client.ts`** — TypeScript API client for the proxy
- **`ModelSelector.tsx`** / **`ModelIndicator.tsx`** — Model selection and status display
- **`NotificationBanner.tsx`** — PII detection and model-switch alerts

### LiteLLM Model Config (`backend/config.yaml`)
Models: `claude-3-opus`, `claude-3-sonnet` (Anthropic), `gpt-4` (OpenAI), `llama3` (Ollama local). All API keys read from environment variables.
