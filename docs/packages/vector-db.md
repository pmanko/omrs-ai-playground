# Vector Database Package

## Overview
The vector-db package provides a ChromaDB instance for storing and retrieving vector embeddings. It serves as the semantic search backend for the RAG (Retrieval-Augmented Generation) system.

## Architecture
- **ChromaDB**: High-performance vector database optimized for semantic similarity search
- **Persistent Storage**: Data persisted in Docker volumes
- **Authentication**: Token-based authentication for secure access
- **REST API**: HTTP interface for cross-service communication

## Configuration

Configuration is managed through the central `.env` file at the project root. Default values are defined in `packages/vector-db/package-metadata.json`.

### Key Environment Variables
- `VECTOR_DB_IMAGE` - Docker image (default: `chromadb/chroma:latest`)
- `VECTOR_DB_PORT` - External port (default: `8001`) 
- `CHROMA_AUTH_TOKEN` - Authentication token (default: `test-token`)
- `CHROMA_AUTH_PROVIDER` - Auth provider class
- `CHROMA_TELEMETRY` - Enable telemetry (default: `false`)
- `PERSIST_DIRECTORY` - Storage path in container (default: `/chroma/chroma`)
- `IS_PERSISTENT` - Enable persistence (default: `TRUE`)
- `CHROMA_THREAD_POOL` - Thread pool size (default: `40`)

See `.env.example` for all available options.

## Deployment

### Docker Compose
```bash
cd packages/vector-db
docker-compose up -d
```

### Docker Swarm
```bash
cd packages/vector-db
chmod +x swarm.sh
./swarm.sh deploy
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/api/v1/heartbeat
```

### Collection Management
- Create collection: `POST /api/v1/collections`
- List collections: `GET /api/v1/collections`
- Delete collection: `DELETE /api/v1/collections/{collection_name}`

### Embedding Operations
- Add embeddings: `POST /api/v1/collections/{collection_name}/add`
- Query embeddings: `POST /api/v1/collections/{collection_name}/query`
- Get by IDs: `POST /api/v1/collections/{collection_name}/get`

## Integration

### Python Client
```python
import chromadb

# Connect to ChromaDB
client = chromadb.HttpClient(
    host="vector-db",
    port=8000,
    settings=Settings(
        chroma_client_auth_provider="chromadb.auth.token.TokenAuthClientProvider",
        chroma_client_auth_credentials="your-token"
    )
)

# Create or get collection
collection = client.get_or_create_collection("openmrs_concepts")

# Add embeddings
collection.add(
    embeddings=[[0.1, 0.2, 0.3]],
    metadatas=[{"concept": "Hypertension"}],
    ids=["concept_1"]
)

# Query similar embeddings
results = collection.query(
    query_embeddings=[[0.1, 0.2, 0.3]],
    n_results=10
)
```

## Monitoring

### Logs
```bash
docker logs vector-db
```

### Metrics
- Collection count
- Total embeddings
- Query latency
- Memory usage

## Backup and Recovery

### Backup
```bash
docker run --rm -v vector-db-data:/data -v $(pwd):/backup alpine tar czf /backup/vector-db-backup.tar.gz /data
```

### Restore
```bash
docker run --rm -v vector-db-data:/data -v $(pwd):/backup alpine tar xzf /backup/vector-db-backup.tar.gz -C /
```

## Troubleshooting

### Common Issues

1. **Connection refused**
   - Check if service is running: `docker ps | grep vector-db`
   - Verify port mapping: `docker port vector-db`

2. **Authentication failed**
   - Verify CHROMA_AUTH_TOKEN is set correctly
   - Check token in client configuration

3. **Out of memory**
   - Increase memory limits in docker-compose.yml
   - Monitor with: `docker stats vector-db`

## Related Documentation
- [Embedding Pipeline](./embedding-pipeline.md)
- [Augmented RAG Implementation](../AUGMENTED_RAG_IMPLEMENTATION_PLAN.md)