# Test Suite Overview

Comprehensive testing for the multi-agent medical system with MCP tool integration.

## Test Categories

### Configuration & Connectivity Tests
-   **`test_config.py`**: Validates the `.env` configuration file and service connectivity
-   **`test_models_direct.py`**: Basic LLM and agent connectivity tests

### A2A Protocol Tests  
-   **`test_a2a_sdk.py`**: End-to-end A2A workflow validation including agent discovery
-   **`test_router_a2a.py`**: Router Agent orchestration logic testing
-   **`test_react_orchestrator.py`**: ReAct pattern multi-step reasoning validation

### MCP Tool Integration Tests
-   **`test_mcp_tools_direct.py`**: Direct MCP tool testing (works with mock data)
-   **`test_mcp_integration.py`**: Full agent integration tests using MCP tools

#### MCP Tool Coverage
- **Spark Analytics**: Population health statistics and patient longitudinal records
- **FHIR Search**: OpenMRS FHIR resource queries with authentication  
- **Medical Search**: Literature search placeholder (extensible to PubMed, etc.)
- **Appointment Management**: OpenMRS REST API integration

## Prerequisites

Ensure all development dependencies are installed:
```bash
poetry install --with dev
```

The integration tests require the agent services to be running:
```bash
poetry run python launch_a2a_agents.py
```

## Running Tests

### Integrated Test Runner (Recommended)

The test runner starts all required services, runs tests, and cleans up automatically:

```bash
# Run all tests (includes MCP integration)
./tests/run_tests.sh

# Run specific test suites
./tests/run_tests.sh config          # Configuration validation
./tests/run_tests.sh models          # LLM connectivity  
./tests/run_tests.sh a2a             # A2A protocol tests
./tests/run_tests.sh react           # ReAct orchestration
./tests/run_tests.sh mcp             # MCP tool tests (no agents needed)
./tests/run_tests.sh mcp-integration # Full integration tests

# Run specific test files
./tests/run_tests.sh tests/test_mcp_integration.py
```

### Mock Data Testing

MCP tools are designed to work with mock data when external services aren't configured:

- **Spark tools**: Return realistic mock patient data and statistics
- **FHIR tools**: Provide sample FHIR resources and responses  
- **Appointment tools**: Generate mock appointment data
- **Medical search**: Returns placeholder literature results

This allows testing the full system without requiring OpenMRS, Spark, or other external dependencies.

### Manual Testing

You can also run individual test files directly:

```bash
# Direct MCP tool tests (always works with mock data)
poetry run python tests/test_mcp_tools_direct.py

# Integration tests (requires agents running)  
poetry run honcho -f Procfile.dev start &  # In separate terminal
poetry run python tests/test_mcp_integration.py
```
