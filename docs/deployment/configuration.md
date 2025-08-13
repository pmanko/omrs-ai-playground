# Configuration Guide

## Overview
This project follows the Instant OpenHIE v2 configuration pattern with:
- A central `.env` file for all configuration
- Default values in `package-metadata.json` files
- Docker Compose files that reference environment variables with fallback defaults

## Configuration Setup

### 1. Create Environment File
Copy the example environment file and customize it:
```bash
cp .env.example .env
```

### 2. Edit Configuration
Edit the `.env` file with your specific settings:
```bash
nano .env
```

## Configuration Structure

### Central Configuration
All configuration is managed through a single `.env` file at the project root. This file is:
- **Not committed to git** (included in `.gitignore`)
- **Loaded by all packages** during deployment
- **Optional** - all services have sensible defaults

### Package Defaults
Each package includes a `package-metadata.json` file that defines:
- Default values for all environment variables
- Descriptions of each variable
- Service dependencies
- Port mappings
- Volume definitions

Example structure:
```json
{
  "name": "package-name",
  "environmentVariables": {
    "VAR_NAME": {
      "default": "default-value",
      "description": "What this variable does"
    }
  }
}
```

### Docker Compose Integration
Docker Compose files reference environment variables with inline defaults:
```yaml
environment:
  MY_VAR: ${MY_VAR:-default-value}
```

This ensures services can run even without a `.env` file.

## Key Configuration Sections

### Database Configuration
```bash
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=openmrs
MYSQL_USER=openmrs
MYSQL_PASSWORD=openmrs
```

### Vector Database Configuration
```bash
VECTOR_DB_PORT=8001
CHROMA_AUTH_TOKEN=your-secure-token
CHROMA_COLLECTION=openmrs_concepts
```

### Embedding Pipeline Configuration
```bash
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=32
PIPELINE_MODE=full
```

### Multiagent Chat Configuration
```bash
LLM_BASE_URL=http://localhost:1234
GENERAL_MODEL=llama-3-8b-instruct
MED_MODEL=medgemma-2
```

## Environment Variable Precedence

The order of precedence for configuration values:
1. **Environment variables** set in the shell
2. **Values in `.env` file**
3. **Docker Compose defaults** (${VAR:-default})
4. **Package metadata defaults**

## Package-Specific Configuration

### Vector Database Package
Located in `packages/vector-db/package-metadata.json`
- Defines ChromaDB settings
- Port mappings for vector search service
- Authentication configuration

### Embedding Pipeline Package
Located in `packages/embedding-pipeline/package-metadata.json`
- MySQL connection settings
- ChromaDB client configuration
- Pipeline execution parameters

### Multiagent Chat Package
Located in `packages/multiagent_chat/package-metadata.json`
- LLM configuration
- A2A settings
- FHIR endpoint configuration

## Deployment with Configuration

### Using Docker Compose
```bash
# Configuration is automatically loaded from .env
docker-compose up -d
```

### Using Swarm Scripts
```bash
# Swarm scripts load from central .env
cd packages/vector-db
./swarm.sh deploy
```

### Overriding Configuration
```bash
# Override specific variables at runtime
VECTOR_DB_PORT=8002 docker-compose up -d

# Or export to environment
export VECTOR_DB_PORT=8002
docker-compose up -d
```

## Security Considerations

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Use strong tokens** - Generate secure tokens for authentication
3. **Rotate credentials** - Regularly update passwords and tokens
4. **Limit access** - Restrict `.env` file permissions:
   ```bash
   chmod 600 .env
   ```

## Troubleshooting Configuration

### View Effective Configuration
```bash
# See what environment variables are set
docker-compose config

# Check specific service configuration
docker inspect <container-name> | grep -A 50 Env
```

### Common Issues

1. **Variable not loading**
   - Check `.env` file exists and is readable
   - Verify variable name matches exactly
   - Ensure no spaces around `=` in `.env`

2. **Wrong default used**
   - Check precedence order
   - Verify `.env` file is being loaded
   - Check for typos in variable names

3. **Service can't connect**
   - Verify hostname resolution
   - Check network configuration
   - Ensure services are on same network

## Related Documentation
- [Environment Variables Reference](./env-reference.md)
- [Package Metadata Specification](./package-metadata.md)
- [Docker Compose Guide](./docker-compose.md)