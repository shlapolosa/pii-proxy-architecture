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
./start.sh                # Auto-detects standalone vs integrated mode
docker compose ps         # Check status
docker compose logs -f    # View logs

# Explicit mode override:
PII_INTEGRATED=false ./start.sh   # Force standalone (postgres + redis + litellm-proxy)
PII_INTEGRATED=true ./start.sh    # Force integrated (litellm-proxy only, joins external network)
```

### Run tests
```bash
cd backend
source venv/bin/activate

# Tier 1: Unit tests (fast, no spaCy needed, mocked Presidio)
pytest -m unit                                  # Runs in seconds

# Tier 2: Integration tests (requires spaCy model via ./install.sh)
pytest -m integration                           # ~30s

# Tier 3: System smoke tests (requires live Docker stack)
docker-compose up -d
pytest -m system --system                       # Needs LITELLM_MASTER_KEY env var

# Coverage report
pytest -m unit --cov=. --cov-report=term-missing

# Legacy standalone script (still works)
python test_pii_detection.py
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
1. Client sends request to **LiteLLM Proxy** (port 8080 externally, 8000 internally)
2. **PIIRoutingHook** (`litellm_pii_hook.py`) intercepts via LiteLLM's `async_pre_call_hook`:
   - Extracts text from the **last user message only** (skips system prompts, conversation history, XML framework tags)
   - Calls **PIIDetectionService** (`pii_detection_service.py`) which uses Microsoft Presidio
   - Filters detected entities — only **sensitive PII types** trigger rerouting (see below)
   - If sensitive PII detected and `PII_REROUTE_ENABLED=true` (default) → mutates `data["model"]` to `local-model` (Ollama)
   - If sensitive PII detected and `PII_REROUTE_ENABLED=false` → logs PII but passes through to original model (passthrough mode)
   - If no sensitive PII → passes through to user's preferred cloud model
   - Fail-safe: routes to local model on any detection error
3. Response is enriched with PII metadata (`pii_detected`, `pii_risk_score` in usage field)

### PII Entity Types That Trigger Rerouting
Only these high-sensitivity types cause rerouting to the local model:
- **`EMAIL_ADDRESS`** — e.g. `john@example.com`
- **`PHONE_NUMBER`** — e.g. `555-123-4567`
- **`US_SSN`** — e.g. `123-45-6789`
- **`CREDIT_CARD`** — e.g. `4111-1111-1111-1111`
- **`US_BANK_NUMBER`** — bank account numbers
- **`IBAN_CODE`** — international bank account numbers
- **`IP_ADDRESS`** — e.g. `192.168.1.100`
- **`US_PASSPORT`** — passport numbers
- **`US_DRIVER_LICENSE`** — driver's license numbers
- **`CRYPTO`** — cryptocurrency wallet addresses
- **`MEDICAL_LICENSE`** — medical license numbers
- **`CUSTOMER_ID`** — custom recognizer: `CUST-######`
- **`EMPLOYEE_ID`** — custom recognizer: `EMP-#####`

These entity types are detected but **do NOT trigger rerouting** (low-risk):
- `PERSON`, `ORGANIZATION`, `DATE_TIME`, `NRP`, `URL`, `LOCATION`

### What Is NOT Detected
- Freeform tokens, API keys, or authentication codes (no standard format)
- Passwords or secrets embedded in natural language
- Custom internal identifiers not matching the patterns above

### Key Backend Modules
- **`litellm_pii_hook.py`** — LiteLLM `CustomLogger` hook. `async_pre_call_hook` scans for PII and reroutes. Handles `call_type` values: `completion`, `acompletion`, `text_completion`, `anthropic_messages`. Module-level instance: `proxy_handler_instance`.
- **`pii_detection_service.py`** — Wraps Microsoft Presidio. `detect_pii()` returns `(has_pii, entities, risk_score)`. Global instance: `pii_service`.
- **`custom_recognizers.py`** — Domain-specific Presidio recognizers: customer IDs (`CUST-######`), employee IDs (`EMP-#####`), project codes (`PROJ-XX-###`), internal hostnames, medical terms, financial accounts.
- **`litellm_middleware.py`** — Legacy middleware orchestrator (superseded by `litellm_pii_hook.py` for in-process hook).
- **`error_handler.py`** — Fallback strategies when PII detection fails: block, sanitize, warn, or route-to-local (default).
- **`notification_handler.py`** — Generates user-facing alerts for PII detection, model switches, errors.

### Infrastructure (Docker Compose)
Dual-mode deployment using Docker Compose profiles:

**Standalone mode** (default) — three services on `pii-proxy-network` bridge:
- **litellm-proxy** (port 8080→8000) — Custom Docker image with Presidio + spaCy + PII hook, configured via `config.yaml`
- **pii-postgres** (expose 5432, profile `standalone`) — Audit logs (`pii_proxy_db`, user `pii_user`)
- **pii-redis** (expose 6379, profile `standalone`) — Caching layer

**Integrated mode** — only litellm-proxy starts, joins external Docker network via `docker network connect`. Reuses external postgres/redis containers. Configured via `PII_INTEGRATED=true` + `EXTERNAL_NETWORK` env vars.

`start.sh` auto-detects mode by checking if external postgres/redis containers are running, or accepts explicit `PII_INTEGRATED=true/false`. DB/Redis hosts are env-var-driven (`PII_DB_HOST`, `PII_REDIS_HOST`, etc.) with sensible defaults per mode.

Local model: **Ollama** `qwen3-coder:480b` hosted externally (configured via `OLLAMA_API_BASE` env var).

### Frontend (`/frontend`)
React/TypeScript components (not a full app scaffold — individual component files):
- **`App.tsx`** — Chat interface with integrated model selection and notifications
- **`api_client.ts`** — TypeScript API client for the proxy
- **`ModelSelector.tsx`** / **`ModelIndicator.tsx`** — Model selection and status display
- **`NotificationBanner.tsx`** — PII detection and model-switch alerts

### LiteLLM Model Config (`backend/config.yaml`)
Models: `claude-opus-4-6`, `claude-sonnet-4-6` (Anthropic), `gpt-4` (OpenAI), `local-model` → `ollama/qwen3-coder:480b` (Ollama). All API keys read from environment variables. `drop_params: true` set to handle unsupported provider params.
