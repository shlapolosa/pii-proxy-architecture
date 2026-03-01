# PII-Aware Model Routing Architecture

A secure architecture that routes LLM requests through a backend proxy that filters for PII and sensitive information. If PII is found, the system automatically switches to a local Ollama model to ensure sensitive data never leaves the user's environment.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Components](#components)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Security](#security)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project implements a privacy-preserving LLM routing system that acts as an intelligent proxy between users and AI models. It automatically detects Personally Identifiable Information (PII) in requests and routes them to appropriate models:

- **Non-sensitive content** → Cloud models (Anthropic Claude, OpenAI GPT)
- **Sensitive content** → Local models (Ollama) for privacy protection

The system ensures that sensitive data never leaves your environment while still providing access to powerful cloud models when appropriate.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Claude Code   │────│  Web Interface   │────│ Mobile Clients  │
│   (CLI Client)  │    │   (React App)    │    │   (Future)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                   ┌─────────────────────────────┐
                   │    API Client Libraries     │
                   │  (Python, JavaScript, etc.) │
                   └─────────────────────────────┘
                                 │
                                 ▼
                   ┌─────────────────────────────┐
                   │    Caddy Reverse Proxy      │
                   │        (HTTPS, Auth)        │
                   └─────────────────────────────┘
                                 │
                                 ▼
                   ┌─────────────────────────────┐
                   │    LiteLLM Proxy Server     │
                   │   (Central Request Router)  │
                   └─────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
      ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
      │   PII Detection │ │ Model Selection │ │   Audit Logs    │
      │    Service      │ │     Engine      │ │  (PostgreSQL)   │
      │ (Microsoft      │ │                 │ │                 │
      │  Presidio)      │ │                 │ │                 │
      └─────────────────┘ └─────────────────┘ └─────────────────┘
                │                │
                ▼                ▼
      ┌─────────────────────────────────────────┐
      │           Model Providers               │
      ├─────────────────┐ ┌─────────────────────┤
      │ Cloud Models    │ │ Local Models        │
      │ (Anthropic,     │ │ (Ollama)            │
      │  OpenAI)        │ │                     │
      └─────────────────┘ └─────────────────────┘
```

## Features

### Extended PII Detection
- **Basic PII**: Social Security Numbers, credit cards, phone numbers, email addresses
- **Extended PII**: Names, addresses, medical terms, financial account numbers
- **Domain-specific PII**: Customer IDs, employee IDs, project codes, internal hostnames
- **Custom patterns**: Organization-specific sensitive data patterns

### Hybrid Model Routing
- **User preference**: Choose preferred model for non-sensitive requests
- **Automatic fallback**: Switch to local models when PII detected
- **Transparency**: Users always know which model is being used
- **Flexible providers**: Support for Anthropic, OpenAI, and local models

### Security & Privacy
- **Zero trust**: Sensitive data never leaves your environment
- **Encryption**: All traffic secured with HTTPS/TLS
- **Authentication**: API key and JWT support
- **Audit trails**: Complete logging for compliance
- **Content sanitization**: Options for cleaning sensitive data

### User Experience
- **Real-time notifications**: Immediate alerts when PII detected
- **Clear indicators**: Visual feedback on model switching
- **Resubmit options**: Ability to resend with sanitized content
- **Model transparency**: Always know which model is active

## Components

### Backend Services (`/backend`)

#### LiteLLM Proxy Server (`config.yaml`)
Central routing point that provides unified access to multiple LLM providers:
- Anthropic Claude models
- OpenAI GPT models
- Local Ollama models
- Secure environment variable management

#### PII Detection Service (`pii_detection_service.py`)
Core service implementing Microsoft Presidio for comprehensive PII detection:
- Content analysis using advanced NLP
- Risk scoring system for sensitivity assessment
- Integration with custom recognizers

#### Custom Recognizers (`custom_recognizers.py`)
Organization-specific PII pattern recognition:
- Customer ID patterns (CUST-######)
- Employee ID patterns (EMP-#####)
- Project code patterns (PROJ-XX-###)
- Internal hostname recognition
- Financial account patterns
- Medical term detection

#### LiteLLM Middleware (`litellm_middleware.py`)
Intelligent request processing and model routing:
- Preprocessing for PII detection
- Dynamic model selection logic
- Response postprocessing with metadata

#### Performance Optimizer (`performance_optimizer.py`)
Efficiency enhancements for high-volume usage:
- Content caching for repeated analysis
- Request batching for throughput
- Resource pooling for concurrency
- Circuit breaker for fault tolerance

#### Error Handler (`error_handler.py`)
Robust error management with fallback strategies:
- Block requests when detection fails
- Sanitize content as fallback
- Allow with warnings option
- Route to local models by default

#### Notification Handler (`notification_handler.py`)
User communication for system events:
- PII detection alerts
- Model switching notifications
- Error condition reporting
- Audit trail generation

#### Authentication Module (`auth.py`)
Secure access control for all services:
- API key generation and validation
- JWT token authentication
- Session management
- Permission-based access control

#### Infrastructure Configuration
- **Docker Compose** (`docker-compose.yml`): Complete service orchestration
- **Caddy Configuration** (`Caddyfile`): Reverse proxy with security
- **Startup Scripts** (`start.sh`, `install.sh`): Easy deployment
- **Requirements Files** (`requirements.txt`): Dependency management
- **Test Framework** (`test_pii_detection.py`): Verification suite

### Frontend Components (`/frontend`)

#### API Client (`api_client.ts`)
JavaScript/TypeScript library for programmatic access:
```javascript
import ApiClient from './api_client';

const client = new ApiClient('https://api.pii-proxy.yourdomain.com', 'your-api-key');

// Send request with automatic PII routing
const { response, notifications } = await client.sendRequest([
  { role: 'user', content: 'Hello, how can I help you?' }
]);
```

#### Model Selector (`ModelSelector.tsx`)
User interface for model selection:
- Dropdown with available models
- Visual indicators for cloud vs local
- Model switching notifications
- Responsive design

#### Notification Banner (`NotificationBanner.tsx`)
Real-time alert system:
- PII detection warnings
- Model switching notices
- Error notifications
- Dismissable alerts

#### Model Indicator (`ModelIndicator.tsx`)
Current model status display:
- Cloud vs local model indicators
- Fallback status visualization
- Security mode indicators
- Responsive design

#### Main Application (`App.tsx`)
Complete demonstration interface:
- Chat-style interaction
- Integrated model selection
- Notification system
- Real-time feedback

### Cloudflare Integration (`/cloudflare`)

#### Cloudflare Tunnel Configuration (`cloudflared-config.yml`)
Secure external access without exposing ports:
- Zero-trust network access
- Automatic TLS encryption
- Service routing rules
- Health check endpoints

## Prerequisites

Before installing, ensure you have:

### System Requirements
- **Docker** (v20.10+)
- **Docker Compose** (v1.29+)
- **Python** (v3.9+)
- **Node.js** (v16+ for frontend development)
- **6 GB RAM** minimum (8 GB recommended)
- **20 GB disk space** for models and logs

### API Keys
- **Anthropic API Key** (for Claude models)
- **OpenAI API Key** (optional, for GPT models)
- **Cloudflare Account** (for tunnel setup)

### Optional Dependencies
- **GPU support** (for accelerated local inference)
- **Domain name** (for production deployment)

## Installation

### Backend Setup

1. **Clone the repository:**
```bash
cd ~/Development
git clone <repository-url> pii-proxy-architecture
cd pii-proxy-architecture/backend
```

2. **Install dependencies:**
```bash
chmod +x install.sh
./install.sh
```

3. **Download language models:**
```bash
python -m spacy download en_core_web_lg
```

### Frontend Setup (Optional)

For web interface development:

1. **Navigate to frontend directory:**
```bash
cd ~/Development/pii-proxy-architecture/frontend
```

2. **Install Node dependencies:**
```bash
npm install
```

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
cd ~/Development/pii-proxy-architecture/backend
cp .env.example .env
```

Required variables:
```env
LITELLM_MASTER_KEY=your-secret-master-key
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
CLOUDFLARE_TUNNEL_TOKEN=your-cloudflare-tunnel-token
POSTGRES_PASSWORD=your-postgres-password
```

### LiteLLM Configuration (`config.yaml`)

Configure model providers:

```yaml
model_list:
  - model_name: claude-3-opus
    litellm_params:
      model: anthropic/claude-3-opus-20240229
      api_key: os.environ/ANTHROPIC_API_KEY

  - model_name: gpt-4
    litellm_params:
      model: openai/gpt-4
      api_key: os.environ/OPENAI_API_KEY

  - model_name: llama3
    litellm_params:
      model: ollama/llama3
      api_base: http://ollama:11434
```

### Docker Compose (`docker-compose.yml`)

Adjust service configurations as needed:

```yaml
services:
  litellm-proxy:
    ports:
      - "8000:8000"
    environment:
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
```

### Domain Configuration

Update domain names in:
- `backend/Caddyfile`
- `cloudflare/cloudflared-config.yml`

## Usage

### Starting the Services

```bash
cd ~/Development/pii-proxy-architecture/backend
chmod +x start.sh
./start.sh
```

This will:
1. Start all Docker containers
2. Initialize services
3. Establish Cloudflare tunnel
4. Begin listening for requests

### Claude Code Integration

Claude Code can interact with the system using the standard Anthropic API:

```bash
# Claude Code will automatically route through the proxy
# when you configure your API endpoint to point to the proxy
```

### Programmatic Access

Using the API client library:

```python
import requests

# Direct API access
response = requests.post(
    'https://api.yourdomain.com/chat/completions',
    headers={'Authorization': 'Bearer YOUR_API_KEY'},
    json={
        'model': 'claude-3-opus',
        'messages': [{'role': 'user', 'content': 'Hello world'}]
    }
)
```

### Web Interface

Access the React frontend at:
```
https://app.yourdomain.com
```

### Monitoring Services

Check service status:
```bash
docker-compose ps
```

View logs:
```bash
docker-compose logs -f
```

## API Reference

### Chat Completions Endpoint

**POST** `/chat/completions`

```bash
curl -X POST https://api.yourdomain.com/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-opus",
    "messages": [
      {"role": "user", "content": "Hello, how can you help me?"}
    ]
  }'
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "I can help you with..."
    }
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30,
    "pii_detected": false,
    "pii_risk_score": 0.0,
    "model_switched": false
  }
}
```

### Model Management

**GET** `/models`

List available models:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.yourdomain.com/models
```

### Health Check

**GET** `/health`

System health status:
```bash
curl https://api.yourdomain.com/health
```

## Security

### Data Protection

- **PII Detection**: Automatic scanning using Microsoft Presidio
- **Model Routing**: Sensitive data routed to local models only
- **Encryption**: All traffic secured with HTTPS/TLS
- **Access Control**: API key and JWT authentication
- **Audit Logging**: Complete request tracking for compliance

### Compliance Features

#### GDPR Compliance
- Data minimization principles
- Privacy by design implementation
- Right to erasure support
- Consent management capabilities

#### HIPAA Considerations
- PHI automatically routed locally
- Encryption at rest and in transit
- Access logging and monitoring
- Business Associate Agreement support

#### SOC 2 Readiness
- Security controls implemented
- Monitoring and alerting configured
- Regular security assessments
- Incident response procedures

### Security Best Practices

1. **Regular Updates**: Keep all components updated
2. **Key Rotation**: Rotate API keys periodically
3. **Network Security**: Use firewalls and network segmentation
4. **Monitoring**: Enable logging and alerting
5. **Backup**: Regular database backups
6. **Testing**: Periodic security assessments

## Testing

### Unit Tests

Run PII detection tests:
```bash
cd backend
python test_pii_detection.py
```

### Integration Tests

Test full system functionality:
```bash
pytest tests/integration
```

### End-to-End Tests

Complete workflow testing:
```bash
pytest tests/e2e
```

### Performance Tests

Load and stress testing:
```bash
pytest tests/performance
```

## Monitoring

### Metrics Collection

- **Request Volume**: Requests per second
- **PII Detection Rate**: Percentage of requests with PII
- **Model Distribution**: Cloud vs local model usage
- **Latency**: Response time metrics
- **Error Rates**: Failure patterns and trends

### Logging

Structured JSON logging for all services:
- Request tracing
- Security events
- Performance metrics
- Debug information

### Alerting

Configurable alerts for:
- High error rates
- Service downtime
- Security events
- Performance degradation
- Resource constraints

## Contributing

We welcome contributions to improve the PII-aware model routing architecture!

### Getting Started

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Guidelines

- Follow existing code style
- Add tests for new features
- Update documentation
- Maintain backward compatibility
- Security-first approach

### Areas for Contribution

- Additional PII recognizers
- New model providers
- Enhanced UI components
- Performance optimizations
- Security enhancements
- Documentation improvements

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please:
1. Check the documentation
2. Review existing issues
3. Open a new issue for bugs
4. Contact maintainers for security concerns

---

*This system ensures your sensitive data stays private while still giving you access to powerful AI capabilities.*