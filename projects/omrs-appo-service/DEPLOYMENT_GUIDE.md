# Deployment Guide - WhatsApp-OpenMRS-MedGemma Service

## Quick Summary

This service is a containerized FastAPI application that:
1. Receives WhatsApp messages via webhook
2. Uses Google's MedGemma AI for medical triage conversations
3. Creates appointments and records in OpenMRS via FHIR API
4. Maintains conversation state in Redis

## Prerequisites

### 1. External Services Required
- **WhatsApp Business API Account** with:
  - Phone Number ID
  - Access Token
  - API Key
- **Google Cloud API Key** (for Gemini/MedGemma access)
- **Public URL** for webhooks (use ngrok for testing)

### 2. Infrastructure (via Instant OpenHIE)
- **OpenMRS** with FHIR module (accessible as `openmrs:8080` on Docker network)
- **Redis** (accessible as `redis:6379` on Docker network)

## Deployment Steps

### Step 1: Prepare Configuration

```bash
# Clone/copy the omrs-whatsapp folder
cd projects/omrs-whatsapp

# Create environment file
cp .env.example .env

# Edit .env with your actual credentials:
# - WHATSAPP_API_KEY
# - WHATSAPP_PHONE_NUMBER_ID
# - WHATSAPP_ACCESS_TOKEN
# - WHATSAPP_WEBHOOK_VERIFY_TOKEN (you create this)
# - GOOGLE_API_KEY
# - WEBHOOK_BASE_URL (your public URL)
```

### Step 2: Build Docker Image

```bash
docker build -t omrs-whatsapp:latest .
```

### Step 3: Deploy Container

#### Option A: Using Docker directly
```bash
docker run -d \
  --name omrs-whatsapp \
  --network instant_default \
  -p 8000:8000 \
  --env-file .env \
  omrs-whatsapp:latest
```

#### Option B: Using Instant OpenHIE package
Create a custom package configuration and deploy via Instant CLI.

### Step 4: Configure WhatsApp Webhook

1. **Get your public URL**:
   - Production: `https://your-domain.com`
   - Testing: Use ngrok: `ngrok http 8000`

2. **Configure in WhatsApp Business**:
   - Webhook URL: `https://[your-public-url]/api/webhook/whatsapp`
   - Verify Token: Use the value from your `.env` file
   - Subscribe to: `messages`, `message_status`

3. **Verify webhook**:
   WhatsApp will send a GET request to verify. The service handles this automatically.

## Testing the Service

### 1. Check Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "active_sessions": 0,
  "redis": "connected"
}
```

### 2. Send Test Message
Send any message to your WhatsApp Business number. You should receive a welcome message starting the triage flow.

## Service Endpoints

- `GET /` - Service info
- `GET /health` - Health check
- `GET /api/webhook/whatsapp` - WhatsApp webhook verification
- `POST /api/webhook/whatsapp` - WhatsApp message handler
- `GET /api/stats` - Service statistics

## Troubleshooting

### Common Issues

1. **"Redis not connected"**
   - Ensure Redis service is running on the Docker network
   - Check service name matches (`redis`)

2. **"OpenMRS connection failed"**
   - Verify OpenMRS is running with FHIR module
   - Check URL: `http://openmrs:8080/openmrs/ws/fhir2/R4`
   - Verify credentials in `.env`

3. **"Webhook not receiving messages"**
   - Ensure public URL is accessible
   - Verify webhook configuration in WhatsApp Business
   - Check logs: `docker logs omrs-whatsapp`

### View Logs
```bash
docker logs -f omrs-whatsapp
```

## Network Requirements

The service must be on the same Docker network as:
- OpenMRS (expects hostname: `openmrs`)
- Redis (expects hostname: `redis`)

Default Instant OpenHIE network: `instant_default`