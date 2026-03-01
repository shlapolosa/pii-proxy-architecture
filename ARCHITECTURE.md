# PII-Aware Model Routing Architecture

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                 │
│  ┌─────────────────┐    ┌──────────────────┐    ┌────────────────────────┐ │
│  │   Claude Code   │────│   Model Selector │────│   Model Indicator      │ │
│  │   Frontend      │    │   Component      │    │   Component            │ │
│  └─────────────────┘    └──────────────────┘    └────────────────────────┘ │
│                                    │                                       │
│                                    ▼                                       │
│                         ┌─────────────────────┐                            │
│                         │   Notification      │                            │
│                         │   Banner            │                            │
│                         └─────────────────────┘                            │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND PROXY SERVER                              │
│                                                                             │
│  ┌─────────────────┐    ┌──────────────────┐    ┌────────────────────────┐ │
│  │   API Gateway   │────│   PII Detection  │────│   Model Router         │ │
│  │   (Caddy)       │    │   Middleware     │    │   Middleware           │ │
│  └─────────────────┘    └──────────────────┘    └────────────────────────┘ │
│            │                        │                       │               │
│            ▼                        ▼                       ▼               │
│  ┌─────────────────┐    ┌──────────────────┐    ┌────────────────────────┐ │
│  │   Auth Module   │    │   Notification   │    │   Performance          │ │
│  │                 │    │   Handler        │    │   Optimizer            │ │
│  └─────────────────┘    └──────────────────┘    └────────────────────────┘ │
│            │                        │                       │               │
│            ▼                        ▼                       ▼               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                             LiteLLM Proxy                            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
         ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
         │  Cloud Models   │ │  Local Models   │ │   Audit Logs    │
         │  (Anthropic,    │ │  (Ollama)       │ │  (PostgreSQL)   │
         │   OpenAI)       │ │                 │ │                 │
         └─────────────────┘ └─────────────────┘ └─────────────────┘
                    │                │
                    ▼                ▼
         ┌─────────────────┐ ┌─────────────────┐
         │    Internet     │ │    Local Net    │
         └─────────────────┘ └─────────────────┘
```

## Data Flow

1. **User Request**: User submits a request through Claude Code frontend
2. **Frontend Processing**: Frontend sends request to backend proxy with user-selected model preference
3. **PII Detection**: Backend proxy analyzes content for PII using Microsoft Presidio
4. **Model Routing Decision**:
   - If PII detected → Route to local Ollama model
   - If no PII → Route to user-selected cloud model
5. **Request Execution**: Send request to appropriate model provider
6. **Response Processing**: Add PII/mode metadata to response
7. **User Notification**: Notify user of any model switching or PII detection
8. **Audit Logging**: Log request details for compliance

## Security Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER ENVIRONMENT                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Claude Code Frontend                     │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┬───────────────────────────────┘
                                  │ HTTPS/TLS
┌─────────────────────────────────▼───────────────────────────────┐
│                    BACKEND PROXY (Secure)                       │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   PII Detection Layer                      │ │
│  │  • Content Analysis                                        │ │
│  │  • Risk Scoring                                            │ │
│  │  • Model Routing Decision                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Model Access Layer                       │ │
│  │  • Cloud Models (External Network)                         │ │
│  │  • Local Models (Internal Network)                         │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components Explained

### Frontend Layer
- **Claude Code Interface**: User interaction point with model selection
- **Model Selector**: Allows user to choose preferred model/provider
- **Model Indicator**: Shows currently active model and fallback status
- **Notification Banner**: Displays PII alerts and model switching notices

### Backend Proxy Layer
- **Caddy Reverse Proxy**: HTTPS termination, rate limiting, security headers
- **LiteLLM Proxy**: Unified interface to multiple LLM providers
- **PII Detection Middleware**: Microsoft Presidio integration for content analysis
- **Model Router**: Intelligent routing logic based on PII detection
- **Authentication Module**: Secure API access control
- **Performance Optimizer**: Caching and batching for efficiency

### Model Providers
- **Cloud Models**: Anthropic Claude, OpenAI GPT (external access)
- **Local Models**: Ollama (internal/local access only)
- **Dynamic Selection**: User preference with automatic PII-based fallback

### Infrastructure
- **Cloudflare Tunnel**: Secure external access without exposing ports
- **Docker Compose**: Container orchestration for all services
- **PostgreSQL**: Audit logging and metadata storage
- **Redis**: Caching layer for performance optimization