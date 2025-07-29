# WhatsApp-OpenMRS-MedGemma Integration Service

A proof-of-concept service that enables AI-powered appointment scheduling and medical triage through WhatsApp, integrating with OpenMRS FHIR endpoints and Google's MedGemma model.

## Overview

This service provides:
- **WhatsApp-based patient interaction** for appointment scheduling
- **AI-powered triage** using Google's MedGemma model
- **Automated appointment creation** in OpenMRS via FHIR API
- **Triage report generation** for healthcare providers
- **Conversation state management** using Redis

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   WhatsApp  │────▶│   Service    │────▶│   OpenMRS    │
│    Users    │     │   (FastAPI)  │     │  FHIR API   │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────┴───────┐
                    │              │
              ┌─────▼─────┐ ┌─────▼─────┐
              │  MedGemma │ │   Redis   │
              │    AI     │ │  Session  │
              └───────────┘ └───────────┘
```

## Features

### 1. Conversational Triage
- Natural language symptom collection
- AI-powered follow-up questions
- Severity assessment (1-5 scale)
- Emergency detection and recommendations

### 2. Appointment Scheduling
- Date and time preference collection
- Integration with OpenMRS scheduling
- Automated confirmation messages

### 3. Medical Record Integration
- Patient creation/lookup in OpenMRS
- Triage encounter documentation
- FHIR-compliant data storage

## Prerequisites

- Docker and Docker Compose
- WhatsApp Business API access
- Google Cloud API key (for MedGemma)
- OpenMRS instance with FHIR module
- Ngrok (for local development)

## Setup Instructions

### 1. Clone the Repository
```bash
cd projects/omrs-whatsapp
```

### 2. Configure Environment Variables
Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# WhatsApp Configuration
WHATSAPP_API_KEY=your_api_key
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token
WHATSAPP_ACCESS_TOKEN=your_access_token

# Google MedGemma
GOOGLE_API_KEY=your_google_api_key

# Webhook URL (use ngrok for local development)
WEBHOOK_BASE_URL=https://your-domain.com
```

### 3. Start the Services
```bash
# Start all services
docker-compose up -d

# For development with ngrok
docker-compose --profile development up -d
```

### 4. Configure WhatsApp Webhook
1. Get your ngrok URL (if using ngrok):
   ```bash
   docker logs omrs-ngrok
   ```

2. Configure webhook in WhatsApp Business API:
   - Webhook URL: `https://your-ngrok-url.ngrok.io/api/webhook/whatsapp`
   - Verify Token: Your `WHATSAPP_WEBHOOK_VERIFY_TOKEN`

## Usage

### Patient Workflow

1. **Initiate Conversation**: Patient sends any message to your WhatsApp number
2. **Provide Information**: Patient responds to AI prompts about:
   - Name
   - Symptoms
   - Duration and severity
   - Medical history (if relevant)
3. **Schedule Appointment**: Patient selects from available time slots
4. **Receive Confirmation**: Patient gets appointment details

### Sample Conversation

```
Patient: Hi
Bot: Hello! I'm MedGemma, an AI assistant here to help you schedule a medical appointment...

Patient: John Smith
Bot: Thank you, John Smith. What brings you in today?

Patient: I've had a persistent headache for 3 days
Bot: I understand you've been experiencing headaches. Can you describe the pain?

[Conversation continues with triage questions]

Bot: Based on your symptoms, I recommend scheduling an appointment. Here are available times...
```

## API Endpoints

### Health Check
```
GET /health
```

### Service Statistics
```
GET /api/stats
```

### WhatsApp Webhook
```
GET /api/webhook/whatsapp  # Verification
POST /api/webhook/whatsapp # Message handling
```

## Development

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run with hot reload
python -m src.main
```

### Testing
```bash
# Run tests (to be implemented)
pytest tests/
```

## Configuration

### Conversation States
- `INITIAL`: Welcome message
- `COLLECTING_SYMPTOMS`: Gathering patient information
- `TRIAGE_ASSESSMENT`: AI analyzing symptoms
- `SCHEDULING_APPOINTMENT`: Selecting appointment times
- `CONFIRMING_DETAILS`: Final confirmation
- `COMPLETED`: Appointment scheduled
- `CANCELLED`: User cancelled

### Triage Categories
1. Non-urgent (Green)
2. Less urgent (Yellow)
3. Urgent (Orange)
4. Very urgent (Red)
5. Immediate/Resuscitation (Red)

## Security Considerations

- All patient data is encrypted in transit
- Redis sessions expire after 24 hours
- OpenMRS credentials should use secure passwords
- WhatsApp webhook verification prevents unauthorized access

## Troubleshooting

### Common Issues

1. **WhatsApp webhook not receiving messages**
   - Check ngrok is running and URL is correct
   - Verify webhook token matches configuration

2. **OpenMRS connection errors**
   - Ensure OpenMRS is running and FHIR module is installed
   - Check network connectivity between containers

3. **MedGemma API errors**
   - Verify Google API key is valid
   - Check API quotas and limits

### Logs
```bash
# View service logs
docker logs omrs-whatsapp -f

# View all logs
docker-compose logs -f
```

## Contributing

This is a proof-of-concept. For production use, consider:
- Adding comprehensive error handling
- Implementing retry logic for external services
- Adding monitoring and alerting
- Enhancing security measures
- Implementing proper testing

## License

[Specify your license]

## Acknowledgments

- OpenMRS community
- Google Health AI team
- WhatsApp Business Platform