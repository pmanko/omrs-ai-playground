# WhatsApp-OpenMRS-MedGemma Integration Service

AI-powered appointment scheduling and medical triage through WhatsApp, designed to work with Instant OpenHIE v2.

## Overview

This service provides:
- **WhatsApp-based patient interaction** for appointment scheduling
- **AI-powered triage** using Google's MedGemma model
- **Automated appointment creation** in OpenMRS via FHIR API
- **Triage report generation** for healthcare providers
- **Conversation state management** using Redis

## Prerequisites

- Instant OpenHIE v2 environment with:
  - OpenMRS with FHIR module (service name: `openmrs`)
  - Redis (service name: `redis`)
- WhatsApp Business API access
- Google Cloud API key (for MedGemma)
- Public URL for WhatsApp webhooks (e.g., via ngrok or reverse proxy)

## Quick Start

### 1. Configure Environment

Create `.env` file from template:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# WhatsApp Configuration
WHATSAPP_API_KEY=your_actual_api_key
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token
WHATSAPP_ACCESS_TOKEN=your_access_token

# Google MedGemma
GOOGLE_API_KEY=your_google_api_key

# Webhook URL (your public URL)
WEBHOOK_BASE_URL=https://your-public-url.com
```

### 2. Build Docker Image

```bash
docker build -t omrs-whatsapp:latest .
```

### 3. Deploy to Instant OpenHIE

Create a package configuration for Instant OpenHIE:

```yaml
# instant-openhie-config.yaml
packages:
  - name: omrs-whatsapp
    services:
      omrs-whatsapp:
        image: omrs-whatsapp:latest
        environment:
          - WHATSAPP_API_KEY=${WHATSAPP_API_KEY}
          - WHATSAPP_PHONE_NUMBER_ID=${WHATSAPP_PHONE_NUMBER_ID}
          - WHATSAPP_WEBHOOK_VERIFY_TOKEN=${WHATSAPP_WEBHOOK_VERIFY_TOKEN}
          - WHATSAPP_ACCESS_TOKEN=${WHATSAPP_ACCESS_TOKEN}
          - GOOGLE_API_KEY=${GOOGLE_API_KEY}
          - WEBHOOK_BASE_URL=${WEBHOOK_BASE_URL}
        networks:
          - instant
        ports:
          - "8000:8000"
```

Deploy with Instant OpenHIE:
```bash
instant package init -p omrs-whatsapp
instant package up -p omrs-whatsapp
```

### 4. Configure WhatsApp Webhook

1. Get your service URL (e.g., through ngrok or your public domain)
2. Configure webhook in WhatsApp Business API:
   - **Webhook URL**: `https://your-public-url.com/api/webhook/whatsapp`
   - **Verify Token**: Your `WHATSAPP_WEBHOOK_VERIFY_TOKEN` from `.env`
   - **Subscribe to**: messages, message_status

## Service Endpoints

- **Health Check**: `GET /health`
- **WhatsApp Webhook**: `GET/POST /api/webhook/whatsapp`
- **Service Stats**: `GET /api/stats`

## Conversation Flow

1. Patient sends any message to your WhatsApp Business number
2. AI collects patient name and symptoms
3. Triage assessment determines urgency (1-5 scale)
4. Patient selects appointment time
5. Confirmation sent with appointment details
6. Records created in OpenMRS

## Required Network Services

The service expects these services on the Docker network:
- `openmrs`: OpenMRS with FHIR API at port 8080
- `redis`: Redis at port 6379

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WHATSAPP_API_KEY` | WhatsApp Business API Key | Required |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp Phone Number ID | Required |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | Webhook verification token | Required |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp access token | Required |
| `GOOGLE_API_KEY` | Google API key for MedGemma | Required |
| `OPENMRS_BASE_URL` | OpenMRS FHIR endpoint | `http://openmrs:8080/openmrs/ws/fhir2/R4` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379` |

## Troubleshooting

### View Logs
```bash
docker logs omrs-whatsapp
```

### Test Health
```bash
curl http://localhost:8000/health
```

### Test Webhook Locally
```bash
curl -X POST http://localhost:8000/api/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "id": "test_msg",
            "from": "1234567890",
            "timestamp": "1234567890",
            "type": "text",
            "text": {"body": "Hello"}
          }]
        }
      }]
    }]
  }'
```

## License

[Specify your license]