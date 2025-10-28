# Agenta Prompt Management Package

Self-hosted prompt management and testing platform for AI agents.

## Overview

This package deploys [Agenta](https://github.com/Agenta-AI/agenta) as an Instant OpenHIE infrastructure service, providing:

- Web-based prompt editing and version control
- Interactive playground for testing prompts with LM Studio models
- Prompt comparison and A/B testing capabilities
- Collaborative prompt engineering for team workflows
- Full prompt history with rollback support

## Architecture

The package includes:

- **agenta-backend**: API server for prompt management
- **agenta-frontend**: Web UI for prompt editing and testing
- **agenta-redis**: Cache layer for performance
- **Database**: Uses shared postgres-1 from database-postgres package

## Dependencies

This package requires:
- `database-postgres` - PostgreSQL database (shared)
- `redis` - Redis cache (optional, uses internal redis if not available)

## Deployment

### Quick Start

```bash
# Deploy prerequisites
./instant package init -n database-postgres -d
./instant package init -n redis -d

# Deploy Agenta
./instant package init -n agenta -d

# Verify deployment
curl http://localhost:8001/api/v1/health
open http://localhost:8002
```

### Development Mode

Development mode exposes ports for external access:

```bash
./instant package init -n agenta -d  # -d flag enables dev mode
```

Ports:
- `8001` - Agenta API (backend)
- `8002` - Agenta Web UI (frontend)

## Configuration

### Environment Variables

Set in package metadata or via `.env`:

```env
# Agenta images
AGENTA_BACKEND_IMAGE=agenta/agenta-backend:latest
AGENTA_WEB_IMAGE=agenta/agenta-web:latest

# Ports (dev mode)
AGENTA_API_PORT=8001
AGENTA_WEB_PORT=8002

# Database connection (uses database-postgres)
POSTGRES_SERVICE=postgres-1
POSTGRES_PORT=5432
AGENTA_POSTGRESQL_DATABASE=agenta
AGENTA_POSTGRESQL_USERNAME=agenta
AGENTA_POSTGRESQL_PASSWORD=agenta123

# Redis connection
REDIS_SERVICE=redis
REDIS_PORT=6379
```

### Initial Setup

After deployment, configure LM Studio integration:

1. Access Agenta UI: `http://localhost:8002`
2. Navigate to **Models** → **Add Custom Model**
3. Add your LM Studio models:
   - Name: `meta-llama-3.1-8b-instruct`
   - Base URL: `http://host.docker.internal:1234/v1`
   - (Repeat for other models)

## Usage with Med Agent Hub

Med Agent Hub agents automatically integrate with Agenta:

1. **Deploy Agenta** (this package)
2. **Migrate prompts** from YAML:
   ```bash
   cd projects/med-agent-hub
   poetry run python -m server.prompt_management.migrate_to_agenta
   ```
3. **Deploy med-agent-hub**:
   ```bash
   ./instant package init -n med-agent-hub -d
   ```

Agents will load prompts from Agenta with YAML fallback.

## Operations

### Lifecycle Commands

```bash
# Initialize (creates database, starts services)
./instant package init -n agenta -d

# Start (if stopped)
./instant package up -n agenta -d

# Stop (keeps data)
./instant package down -n agenta

# Destroy (removes everything)
./instant package destroy -n agenta
```

### Logs

```bash
# View backend logs
docker logs -f <agenta-backend-container-id>

# View frontend logs
docker logs -f <agenta-frontend-container-id>
```

### Health Checks

```bash
# API health
curl http://localhost:8001/api/v1/health

# Frontend
curl http://localhost:8002

# Database connection
docker exec -it <postgres-container> psql -U agenta -d agenta
```

## Troubleshooting

### Services Not Starting

1. Check prerequisites are running:
   ```bash
   docker ps | grep postgres-1
   ```

2. Check database initialization:
   ```bash
   docker ps -a | grep agenta_db_config
   docker logs <agenta_db_config-container>
   ```

3. Restart package:
   ```bash
   ./instant package down -n agenta
   ./instant package up -n agenta -d
   ```

### Database Issues

Reinitialize database:

```bash
# Destroy and recreate
./instant package destroy -n agenta
./instant package init -n agenta -d
```

### Connection Issues from Agents

If med-agent-hub agents can't reach Agenta:

1. Check networks:
   ```bash
   docker network inspect multiagent_public
   ```

2. Verify backend is accessible:
   ```bash
   docker exec <med-agent-hub-server> curl http://agenta-backend:8000/api/v1/health
   ```

3. Check logs for connection errors

## Integration

This package integrates with:

- **med-agent-hub**: Agents load prompts from Agenta API
- **database-postgres**: Shared PostgreSQL database
- **redis**: Optional shared cache

## Documentation

See med-agent-hub documentation for prompt management workflows:
- [Prompt Management Guide](../../projects/med-agent-hub/docs/prompt-management.md)
- [Agent Reference](../../projects/med-agent-hub/docs/architecture/agents.md)

## Resources

- [Agenta Official Documentation](https://docs.agenta.ai/)
- [Agenta GitHub Repository](https://github.com/Agenta-AI/agenta)
- [Agenta API Reference](https://docs.agenta.ai/reference/api)

