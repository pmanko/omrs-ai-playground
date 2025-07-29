# Proof of Concept Summary

## What This Service Does

A FastAPI service that creates a WhatsApp bot for medical appointment scheduling:
1. **Receives** WhatsApp messages via webhook
2. **Conducts** AI-powered triage conversations using Google's Gemini/MedGemma
3. **Creates** appointments and medical records in OpenMRS via FHIR
4. **Maintains** conversation state in Redis

## Required External Services & Credentials

### 1. WhatsApp Business API
You need:
- WhatsApp Business API access (Meta/Facebook)
- Phone Number ID
- Access Token  
- API Key
- A webhook verification token (you create this)

### 2. Google Cloud
You need:
- Google Cloud API Key with Gemini API access

### 3. Public URL
You need:
- A public HTTPS URL for WhatsApp to send messages to
- For testing: Use ngrok (`ngrok http 8000`)
- For production: Use your domain with SSL

## Infrastructure Requirements

The service expects these to be available on the Docker network:
- **OpenMRS** at `http://openmrs:8080` with FHIR module
- **Redis** at `redis://redis:6379`

## Step-by-Step Deployment

### 1. Get the Code
```bash
cd projects/omrs-whatsapp
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

### 3. Build Docker Image
```bash
docker build -t omrs-whatsapp:latest .
```

### 4. Run the Service
```bash
# Make sure you're on the same network as OpenMRS and Redis
docker run -d \
  --name omrs-whatsapp \
  --network instant_default \
  -p 8000:8000 \
  --env-file .env \
  omrs-whatsapp:latest
```

### 5. Configure WhatsApp Webhook
In WhatsApp Business API settings:
- **Webhook URL**: `https://[your-public-url]/api/webhook/whatsapp`
- **Verify Token**: The token you set in `.env`
- **Subscribe to**: messages, message_status

### 6. Test
- Send a WhatsApp message to your business number
- Check health: `curl http://localhost:8000/health`
- View logs: `docker logs omrs-whatsapp`

## How the Conversation Flow Works

1. **Patient**: Sends any message
2. **Bot**: "Hello! I'm MedGemma... What's your name?"
3. **Patient**: Provides name and describes symptoms
4. **Bot**: Asks follow-up questions, assesses severity
5. **Bot**: Offers appointment times
6. **Patient**: Selects time
7. **Bot**: Confirms and creates records in OpenMRS

## Key Endpoints

- `GET /health` - Check if service is running
- `GET/POST /api/webhook/whatsapp` - WhatsApp integration
- `GET /api/stats` - Service statistics

## File Structure

```
omrs-whatsapp/
├── src/                    # Application code
│   ├── main.py            # FastAPI app
│   ├── webhooks.py        # WhatsApp webhook handlers
│   ├── whatsapp_client.py # Send WhatsApp messages
│   ├── medgemma_client.py # Google AI integration
│   ├── openmrs_client.py  # OpenMRS FHIR client
│   └── ...                # Other modules
├── Dockerfile             # Container definition
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
└── README.md             # Documentation
```

## Common Issues & Solutions

1. **Can't connect to Redis/OpenMRS**
   - Ensure services are on same Docker network
   - Check service names match (redis, openmrs)

2. **WhatsApp not sending messages**
   - Verify webhook URL is publicly accessible
   - Check webhook verification succeeded
   - Ensure all WhatsApp credentials are correct

3. **Google API errors**
   - Verify API key has Gemini access
   - Check quotas haven't been exceeded

## Next Steps for Production

1. Add proper error handling for network failures
2. Implement retry logic for external services
3. Add monitoring and alerting
4. Set up proper logging aggregation
5. Implement rate limiting
6. Add authentication for admin endpoints