# WhatsApp-OpenMRS-MedGemma Architecture

## System Overview

This service implements an AI-powered appointment scheduling and triage system that interfaces between WhatsApp users, Google's MedGemma AI model, and OpenMRS FHIR endpoints.

## Component Architecture

### Core Components

#### 1. **WhatsApp Integration** (`whatsapp_client.py`, `webhooks.py`)
- Handles incoming WhatsApp messages via webhook
- Sends text messages, interactive buttons, and lists
- Manages message acknowledgments and status updates

#### 2. **AI Integration** (`medgemma_client.py`)
- Interfaces with Google's MedGemma model
- Generates contextual medical responses
- Performs triage analysis and severity assessment
- Creates conversation summaries

#### 3. **OpenMRS Integration** (`openmrs_client.py`)
- FHIR-compliant patient management
- Appointment creation
- Encounter and observation recording
- Practitioner and location queries

#### 4. **Conversation Management** (`conversation_manager.py`)
- State machine implementation
- Workflow orchestration
- Message routing and processing
- Scheduling logic

#### 5. **Session Management** (`session_manager.py`)
- Redis-based session persistence
- Conversation state tracking
- TTL-based session expiry
- Active session monitoring

#### 6. **Report Generation** (`report_generator.py`)
- Triage report creation
- Medical record formatting
- Appointment note generation

### Data Flow

```
1. Patient sends WhatsApp message
   ↓
2. Webhook receives and validates message
   ↓
3. Session Manager retrieves/creates session
   ↓
4. Conversation Manager processes based on state
   ↓
5. MedGemma AI generates response
   ↓
6. Response sent back via WhatsApp
   ↓
7. State updated in Redis
   ↓
8. (On completion) OpenMRS records created
```

### State Machine

```
INITIAL
  ↓
COLLECTING_SYMPTOMS
  ↓
TRIAGE_ASSESSMENT
  ↓
SCHEDULING_APPOINTMENT
  ↓
CONFIRMING_DETAILS
  ↓
COMPLETED / CANCELLED
```

## File Structure

```
projects/omrs-whatsapp/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration management
│   ├── logging_config.py        # Logging setup
│   ├── main.py                  # FastAPI application
│   ├── models.py                # Pydantic data models
│   ├── webhooks.py              # WhatsApp webhook handlers
│   ├── whatsapp_client.py       # WhatsApp API client
│   ├── medgemma_client.py       # MedGemma AI client
│   ├── openmrs_client.py        # OpenMRS FHIR client
│   ├── conversation_manager.py  # Conversation orchestration
│   ├── session_manager.py       # Redis session management
│   └── report_generator.py      # Medical report generation
├── tests/                       # Test suite (to be implemented)
├── config/                      # Configuration files
├── docs/                        # Documentation
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container definition
├── docker-compose.yml          # Multi-container setup
├── .env.example                # Environment template
├── run.sh                      # Service management script
├── run_local.py               # Local development runner
└── README.md                   # Project documentation
```

## Key Design Decisions

### 1. **Asynchronous Architecture**
- FastAPI with async/await for high concurrency
- Non-blocking I/O for external API calls
- Background task processing

### 2. **Session Persistence**
- Redis for fast, reliable session storage
- 24-hour TTL for conversation sessions
- JSON serialization for complex data structures

### 3. **FHIR Compliance**
- Using fhir.resources library for data models
- Standard FHIR resource types (Patient, Appointment, Encounter)
- RESTful FHIR API interactions

### 4. **Modular Design**
- Single responsibility principle for each module
- Dependency injection pattern
- Singleton instances for stateful components

### 5. **Error Handling**
- Graceful degradation for external service failures
- Comprehensive logging for debugging
- User-friendly error messages

## Security Considerations

1. **Authentication**
   - WhatsApp webhook verification token
   - Basic auth for OpenMRS API
   - API key for Google services

2. **Data Protection**
   - TLS encryption for all external communications
   - Session data expires after 24 hours
   - No persistent storage of sensitive data

3. **Input Validation**
   - Pydantic models for request validation
   - Sanitization of user inputs
   - Rate limiting considerations

## Scalability Considerations

1. **Horizontal Scaling**
   - Stateless service design
   - Redis for shared state
   - Load balancer compatible

2. **Performance Optimization**
   - Connection pooling for Redis
   - Async I/O for external calls
   - Efficient session lookup

3. **Monitoring Points**
   - Health check endpoint
   - Statistics endpoint
   - Structured logging

## Extension Points

1. **Additional Messaging Platforms**
   - Abstract message interface
   - Platform-specific adapters

2. **Alternative AI Models**
   - Pluggable AI interface
   - Model-specific implementations

3. **Enhanced Scheduling**
   - Real-time availability checking
   - Multi-provider support
   - Calendar integration

4. **Analytics**
   - Conversation metrics
   - Triage outcomes tracking
   - Appointment completion rates