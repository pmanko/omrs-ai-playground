# OMRS AI Playground

A comprehensive healthcare AI research platform demonstrating multi-agent architectures, Agent2Agent (A2A) protocols, Model Context Protocol (MCP) tool integration, and medical AI applications.

## Key Features

### 🤖 Multi-Agent Medical Chat (`med-agent-hub`)
- **A2A-compliant agents** with semantic routing and ReAct orchestration
- **MCP tool integration** for structured data access and API interactions
- **Enhanced clinical capabilities**:
  - Population health analytics via Spark SQL queries
  - Patient longitudinal records (IPS-like comprehensive health history)
  - FHIR resource search and retrieval
  - Medical literature search (extensible to PubMed, UpToDate, etc.)
  - Appointment management via OpenMRS REST API

### 🏥 Healthcare Data Integration
- **OpenMRS FHIR R4** - Live EMR data access with role-based security
- **Parquet-on-FHIR analytics** - SQL queries on healthcare data via Spark
- **Synthetic data pipeline** - Realistic test data generation with Synthea
- **FHIR Info Gateway** - Role-based access control for patient data

### 🧠 AI Model Architecture
- **Mixture of Experts** approach with specialized models:
  - Router: Llama-3.1 8B for orchestration and semantic routing
  - Medical: MedGemma 4B for clinical expertise and synthesis  
  - Clinical: Gemma-3 1B for research queries and data analysis
  - Administrative: Llama-3 8B for operational tasks

## Getting Started

1. **Initialize the system:**
   ```bash
   ./mk.sh  # Build and configure all packages
   ```

2. **Start core services:**
   ```bash
   ./instant package up -n database-mysql -d
   ./instant package up -n emr-openmrs -d  
   ./instant package up -n analytics-ohs-data-pipes -d  # For Spark analytics
   ./instant package up -n med-agent-hub -d
   ```

3. **Access applications:**
   - Multi-agent chat: http://localhost:8091
   - OpenMRS EMR: http://localhost:8090
   - Spark SQL interface: http://localhost:4041

## Development & Testing

```bash
cd projects/med-agent-hub/

# Setup environment
cp env.recommended .env  # Configure LLM, FHIR, Spark endpoints

# Development mode 
poetry install --with dev --extras "spark duckdb"
poetry run honcho -f Procfile.dev start

# Run comprehensive tests
./tests/run_tests.sh              # All tests including MCP integration
./tests/run_tests.sh mcp          # MCP tool tests only
./tests/run_tests.sh mcp-integration  # Full agent integration tests
```

## Example Queries

The system can handle complex medical queries like:

- **Population Analytics**: "Is diabetes becoming more common in our patient population?"
- **Patient Records**: "Show me John Doe's complete health history in timeline format"
- **Clinical Research**: "What does recent research say about metformin for diabetes?"
- **FHIR Search**: "Get the latest HbA1c results for patient 12345"
- **Appointments**: "Schedule a follow-up for patient 789 next Tuesday at 2 PM"
- **Multi-agent orchestration**: "I'm diabetic - check my recent results, explain what they mean, and book my next appointment"

## Documentation

- [Architecture overview](CLAUDE.md) - Comprehensive system documentation
- [Multi-agent chat docs](projects/med-agent-hub/docs/docs.md) - Agent setup and configuration  
- [Testing guide](docs/med-agent-hub/testing.md) - Test suite and validation
- [Getting started guide](docs/README.md) - Package overview

## Tech Stack

- **Agents**: A2A protocol, MCP tools, Python FastAPI, ReAct orchestration
- **LLMs**: MedGemma, Llama-3, Gemma via LM Studio (local) or cloud APIs
- **EMR**: OpenMRS, MySQL, FHIR R4 with Info Gateway RBAC
- **Analytics**: Apache Spark, Parquet-on-FHIR, PyHive integration
- **Infrastructure**: Docker Compose, Instant OpenHIE v2

Licensed under MIT.