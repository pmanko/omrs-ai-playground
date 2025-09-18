# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **OMRS AI Playground** - a comprehensive healthcare AI research platform that demonstrates advanced multi-agent architectures, Agent2Agent (A2A) protocols, and medical AI applications. The codebase consists of multiple interconnected projects and packages for building AI-powered healthcare systems.

## Key Architecture Components

### 1. Multi-Agent Medical Chat System (`projects/med-agent-hub/`)
- **A2A-enabled multi-agent system** with semantic routing between specialized AI agents
- **MCP-compliant tool integration** for data access via Model Context Protocol
- **MedGemma integration** for medical expertise via Google's healthcare AI model
- **FHIR integration** with OpenMRS for live healthcare data queries
- **Parquet-on-FHIR** support for local analytics via Spark SQL
- **Enhanced agent capabilities**:
  - Population health analytics via Spark SQL
  - Patient longitudinal records (IPS-like comprehensive health history)
  - FHIR resource search and retrieval
  - Medical literature search (placeholder for future resources)
  - Appointment management via OpenMRS REST API
- **Mixture of Experts** approach using different LLMs for different tasks:
  - Generalist LLMs (Llama-3, Gemma) for query generation and routing
  - MedGemma for clinical synthesis and medical responses

### 2. OpenMRS EMR Integration (`packages/emr-openmrs/`)
- Full OpenMRS deployment with FHIR R4 support
- MySQL database backend
- Dockerized deployment via Instant OpenHIE

### 3. WhatsApp Medical Assistant (`projects/omrs-appo-service/`)
- WhatsApp webhook integration for patient communication
- AI-powered triage and appointment scheduling
- MedGemma client for medical assessments
- OpenMRS FHIR client for patient records
- Redis session management with conversation state tracking

### 4. Synthetic Data Pipeline (`projects/synthetic-data-uploader/`)
- Synthea-based synthetic patient data generation
- FHIR resource generation and validation
- Batch and incremental data upload to OpenMRS
- HIV/TB care modules with specialized clinical workflows

### 5. FHIR Analytics (`packages/analytics-ohs-data-pipes/`)
- FHIR Data Pipes integration for Parquet-on-FHIR analytics
- Apache Spark backend for SQL queries on healthcare data
- Flink streaming support for real-time analytics

## Development Commands

### Project Initialization and Build
```bash
# Initialize and build all packages
./mk.sh

# Build custom Docker images (for projects with custom code)
./build-custom-images.sh

# Build specific project images
./build-custom-images.sh med-agent-hub
./build-custom-images.sh omrs-appo-service

# Initialize specific packages via Instant OpenHIE
./instant package init -n database-mysql -d
./instant package init -n emr-openmrs -d
./instant package init -n med-agent-hub -d
```

### Multi-Agent Chat Development
```bash
cd projects/med-agent-hub/

# Install dependencies (includes MCP tools)
poetry install --with dev --extras "spark duckdb"

# Development mode (A2A agents with MCP tools)
cp env.recommended .env  # Configure LLM endpoints, FHIR, and Spark
poetry run honcho -f Procfile.dev start

# Individual agent services (for debugging)
poetry run uvicorn server.sdk_agents.router_server:app --host 0.0.0.0 --port 9100
poetry run uvicorn server.sdk_agents.medgemma_server:app --host 0.0.0.0 --port 9101  
poetry run uvicorn server.sdk_agents.clinical_server:app --host 0.0.0.0 --port 9102
poetry run uvicorn server.sdk_agents.administrative_server:app --host 0.0.0.0 --port 9103

# Testing (includes MCP tool tests)
./tests/run_tests.sh              # All tests
./tests/run_tests.sh mcp          # MCP tool tests only  
./tests/run_tests.sh mcp-integration  # Full integration tests

# Code quality
poetry run black .
poetry run isort .
poetry run flake8 .
```

### Synthetic Data Operations
```bash
cd projects/synthetic-data-uploader/

# Run tests
python -m pytest uploader/  # All tests
python -m pytest uploader/main_test.py  # Specific test file

# Generate and upload synthetic data
python uploader/main.py --help
```

### Package Management with Instant OpenHIE
```bash
# Package operations
./instant package up -n <package-name> -d     # Start package
./instant package down -n <package-name>      # Stop package  
./instant package destroy -n <package-name>   # Remove package
./instant package init -n <package-name> -d   # Initialize package

# Available packages: database-mysql, emr-openmrs, med-agent-hub, 
# redis, omrs-appo-service, reverse-proxy-nginx, fhir-datastore-hapi-fhir
```

## Configuration Management

### Centralized Port Configuration
The platform uses a centralized environment-based port configuration system following OpenHIE Instant v2 standards:

- **`.env.example`**: Template with all available port configurations and defaults
- **`.env`**: Local environment file (gitignored) - copy from `.env.example` and customize
- **Package metadata**: `packages/*/package-metadata.json` contains port environment variables with defaults
- **Docker Compose dev files**: Use `${PORT_VAR:-default}` syntax for configurable ports

#### Available Port Environment Variables
```bash
# OpenMRS EMR Ports
OMRS_BACKEND_PORT=8888          # OpenMRS backend API
OMRS_GATEWAY_PORT=8090          # OpenMRS gateway/proxy

# Multi-Agent Chat Ports  
MED_AGENT_HUB_SERVER_PORT=3000    # Chat server API
MED_AGENT_HUB_CLIENT_PORT=8091    # Web client interface

# A2A Service Ports (native A2A mode)
A2A_ROUTER_PORT=9100            # Semantic router service
A2A_MEDGEMMA_PORT=9101          # MedGemma agent service
A2A_CLINICAL_PORT=9102          # Clinical research agent (with MCP tools)
A2A_ADMIN_PORT=9103             # Administrative agent (appointments)

# FHIR & Analytics Ports
HAPI_FHIR_PORT=3447             # HAPI FHIR server
ANALYTICS_CONTROLLER_PORT=8092   # Data pipeline controller
ANALYTICS_SPARK_THRIFT_PORT=10001 # Spark Thrift server
ANALYTICS_SPARK_UI_PORT=4041     # Spark web UI

# Application Services
OMRS_APPO_SERVICE_PORT=3050     # WhatsApp service
REDIS_PORT=6379                 # Redis cache
MYSQL_PORT=3336                 # MySQL database
```

### Environment Variables
- **Root-level `.env`**: Global configuration variables including all port definitions
- **Package metadata**: `packages/*/package-metadata.json` contains default environment variables
- **Project-specific**: Each project has its own environment configuration

### Key Configuration Files
- `config.yaml`: Main project configuration with package dependencies
- `packages/*/package-metadata.json`: Package-specific metadata and environment variables
- `projects/*/env.example`: Environment templates for individual projects

## Project Structure Patterns

### Package Structure (`packages/`)
Each package follows the Instant OpenHIE pattern:
- `docker-compose.yml`: Main service definition
- `docker-compose.dev.yml`: Development overrides
- `package-metadata.json`: Package metadata and environment variables
- `swarm.sh`: Docker Swarm deployment script

### Project Structure (`projects/`)
Application projects with custom code:
- `Dockerfile`: Container definition
- `README.md`: Project-specific documentation
- `requirements.txt` or `pyproject.toml`: Dependency management
- Language-specific structure (Python packages, Node.js apps, etc.)

## FHIR and Healthcare Data

### FHIR R4 Resources
- **Patient demographics and identifiers**
- **Clinical encounters and observations**
- **Medications and treatment plans**
- **Appointments and scheduling**

### Data Sources
- **Live OpenMRS FHIR Server**: `https://fhir.openmrs.org/`
- **Local Parquet-on-FHIR**: Spark SQL-queryable analytics data
- **Synthetic Patients**: Generated via Synthea with realistic clinical workflows

### Clinical Specializations
- **HIV/AIDS care workflows** with antiretroviral treatment tracking
- **Tuberculosis screening and treatment** protocols
- **Maternal health** and family planning services
- **General primary care** encounters and vitals

## Agent2Agent (A2A) Protocol Implementation

### Core A2A Concepts
- **Agent Registry**: Service discovery mechanism for available agents and skills
- **Message Bus**: Decoupled communication between agents via standardized messages
- **Skills-based Interactions**: Agents expose capabilities as discoverable skills with typed input schemas
- **Semantic Routing**: Orchestrator selects appropriate agents based on query analysis

### Agent Types
- **Router Agent**: Orchestrates and routes queries to specialist agents
- **MedGemma Agent**: Medical expertise and clinical synthesis
- **Clinical Research Agent**: FHIR API and Parquet-on-FHIR data queries with dual-prompt capabilities

## Testing Strategy

### Python Projects
- Use `pytest` for test execution
- Test files follow `*_test.py` naming convention
- Unit tests for core functionality, integration tests for external APIs

### Docker Testing
- `docker-compose.dev.yml` files for development environments
- Health checks and service dependencies defined in compose files

## AI Model Integration

### LLM Endpoints
- **LM Studio**: Local model serving with headless mode
- **OpenAI-compatible APIs**: For cloud and local model inference
- **Google Vertex AI**: MedGemma deployment via Model Garden
- **Gemini API**: For orchestration and general tasks

### Model Specialization
- **MedGemma**: Clinical synthesis, medical question answering
- **Llama-3/Gemma**: Query generation, semantic routing, general reasoning
- **Text embedding models**: Future hybrid RAG implementation for semantic search

## Common Development Workflows

### Adding New Healthcare Data
1. Generate synthetic data with Synthea modules
2. Validate FHIR resources using `uploader/resources.py`
3. Upload to OpenMRS via FHIR API using `uploader/main.py`
4. Verify data availability in analytics pipeline

### Extending Multi-Agent System
1. Define new agent skills in agent registry
2. Implement agent logic with standardized A2A message handling
3. Update orchestrator prompts to recognize new capabilities
4. Test end-to-end workflow through web UI

### Healthcare Workflow Implementation
1. Design clinical workflow with FHIR resource mapping
2. Implement state machine in conversation manager
3. Add MedGemma prompts for clinical assessment
4. Create OpenMRS integration for data persistence