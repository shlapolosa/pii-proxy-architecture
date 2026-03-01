# PII-Aware Model Routing Architecture - Deployment Guide

## Overview

This guide explains how to deploy and use the PII-aware model routing architecture that ensures sensitive data never leaves your environment while still providing access to powerful cloud models for non-sensitive tasks.

## Prerequisites

Before deploying, ensure you have:

1. **Docker and Docker Compose** installed
2. **Python 3.9+** installed
3. **Node.js 16+** installed (for frontend development)
4. **API keys** for cloud model providers:
   - Anthropic API key
   - OpenAI API key (optional)
5. **Cloudflare account** for tunnel setup

## Deployment Steps

### 1. Clone the Repository

```bash
cd ~/Development
git clone <repository-url> pii-proxy-architecture
cd pii-proxy-architecture
```

### 2. Set Environment Variables

Create a `.env` file in the backend directory:

```bash
cd backend
cp .env.example .env  # If .env.example exists, otherwise create manually
```

Add the following to your `.env` file:

```env
LITELLM_MASTER_KEY=your-secret-master-key
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
CLOUDFLARE_TUNNEL_TOKEN=your-cloudflare-tunnel-token
POSTGRES_PASSWORD=your-postgres-password
```

### 3. Install Backend Dependencies

```bash
cd backend
chmod +x install.sh
./install.sh
```

### 4. Set Up Cloudflare Tunnel

1. Create a Cloudflare Tunnel in your dashboard
2. Copy the tunnel token
3. Update the `CLOUDFLARE_TUNNEL_TOKEN` in your `.env` file
4. Update the `cloudflared-config.yml` with your tunnel ID and domain names

### 5. Configure Domain Names

Update the following files with your actual domain names:

- `backend/Caddyfile`: Replace `yourdomain.com` with your domain
- `cloudflare/cloudflared-config.yml`: Replace `yourdomain.com` with your domain

### 6. Start the Services

```bash
cd backend
chmod +x start.sh
./start.sh
```

This will:
- Start all Docker containers
- Initialize the LiteLLM proxy
- Start Ollama for local models
- Set up the PostgreSQL database
- Configure Redis caching
- Establish the Cloudflare tunnel
- Start the Caddy reverse proxy

### 7. Pull Local Models (Ollama)

```bash
# Connect to the Ollama container
docker exec -it ollama ollama pull llama3
docker exec -it ollama ollama pull mistral
```

### 8. Verify Installation

Check that all services are running:

```bash
docker-compose ps
```

You should see all services in the "Up" state.

## Usage Guide

### Frontend Interface

1. **Access the Application**
   - Navigate to `https://app.yourdomain.com` in your browser
   - The Claude Code interface will load

2. **Model Selection**
   - Use the dropdown to select your preferred model:
     - Cloud models (Claude 3, GPT-4) for non-sensitive tasks
     - Local models (Llama 3, Mistral) for sensitive tasks
   - The system will automatically switch to local models when PII is detected

3. **Interacting with the Assistant**
   - Type your message in the input box
   - Press Enter or click Send
   - View responses in the chat history

### PII Detection Features

1. **Automatic Detection**
   - The system automatically scans all requests for PII
   - Includes names, addresses, emails, SSNs, credit cards, etc.
   - Domain-specific patterns (customer IDs, employee IDs, etc.)

2. **Model Switching Notifications**
   - When PII is detected, you'll see:
     - A warning notification explaining what was detected
     - The model switching indicator will show a warning icon
     - The model selector will highlight the switch

3. **Risk Scoring**
   - Each request receives a risk score (0.0 to 1.0)
   - Higher scores indicate more sensitive content
   - Scores are displayed in notifications

### Security Features

1. **Data Protection**
   - Sensitive data is automatically routed to local models
   - Content sanitization available when needed
   - All traffic encrypted with HTTPS

2. **Access Control**
   - API key authentication for programmatic access
   - Session management for web interface
   - Role-based permissions (read/write access)

3. **Audit Logging**
   - All requests logged for compliance
   - PII detection events recorded
   - Model routing decisions tracked

## API Usage

You can also interact with the system programmatically:

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

The API will automatically:
- Detect PII in your request
- Route to appropriate model
- Return response with PII metadata
- Log the interaction

## Monitoring and Maintenance

### Checking Service Status

```bash
cd backend
docker-compose ps
```

### Viewing Logs

```bash
# View LiteLLM proxy logs
docker-compose logs -f litellm-proxy

# View all service logs
docker-compose logs -f
```

### Updating Models

```bash
# Update Ollama models
docker exec -it ollama ollama pull llama3

# Restart services if needed
docker-compose restart
```

### Backup and Recovery

```bash
# Backup PostgreSQL database
docker exec postgres-db pg_dump -U pii_user pii_proxy_db > backup.sql

# Restore PostgreSQL database
docker exec -i postgres-db psql -U pii_user pii_proxy_db < backup.sql
```

## Troubleshooting

### Common Issues

1. **Services Not Starting**
   - Check that all environment variables are set
   - Verify Docker has sufficient resources
   - Check logs with `docker-compose logs`

2. **PII Detection Not Working**
   - Ensure spaCy language model is installed
   - Check that presidio libraries are properly installed
   - Verify the Python virtual environment is activated

3. **Model Routing Issues**
   - Check LiteLLM configuration in `config.yaml`
   - Verify API keys are correct
   - Ensure local models are pulled in Ollama

4. **Connection Problems**
   - Verify Cloudflare tunnel is active
   - Check domain DNS settings
   - Ensure firewall allows required ports

### Testing PII Detection

```bash
cd backend
python test_pii_detection.py
```

This will run a series of tests to verify PII detection is working correctly.

## Scaling and Performance

### Horizontal Scaling

- The architecture supports multiple instances behind a load balancer
- PostgreSQL can be scaled separately
- Redis provides caching for performance

### Performance Optimization

- Adjust batch sizes in `performance_optimizer.py`
- Tune Redis memory settings
- Monitor and optimize database queries

### Monitoring

- Prometheus metrics endpoint available
- Grafana dashboards can be configured
- Health checks at `/health` endpoint

## Compliance and Security

### GDPR Compliance

- Data minimization: Only necessary data is processed
- Privacy by design: PII detection and routing built-in
- Right to erasure: Database records can be deleted

### HIPAA Considerations

- PHI automatically routed to local models
- Encryption in transit and at rest
- Audit logging of all access

### SOC 2 Readiness

- Security controls implemented
- Monitoring and alerting configured
- Regular security assessments

## Extending the Architecture

### Adding New Models

1. Update `config.yaml` with new model configuration
2. Add model to frontend selector in `ModelSelector.tsx`
3. Update model type detection in `ModelIndicator.tsx`

### Custom PII Patterns

1. Add new patterns to `custom_recognizers.py`
2. Register recognizer in `presidio_config.py`
3. Test with `test_pii_detection.py`

### Additional Providers

1. Add provider configuration to `config.yaml`
2. Update authentication in `auth.py` if needed
3. Add provider to frontend model list

## Conclusion

This PII-aware model routing architecture provides a secure way to leverage powerful cloud AI models while ensuring sensitive data remains protected. The hybrid approach gives users the flexibility to choose their preferred models while maintaining security through automatic fallback when PII is detected.

For support, contact your system administrator or refer to the documentation in the `README.md` file.