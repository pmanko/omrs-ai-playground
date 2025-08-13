# Embedding Pipeline Package

## Overview
The embedding-pipeline package is a batch processing system that extracts medical concepts from the OpenMRS MySQL database and generates vector embeddings for semantic search. It populates the ChromaDB vector database with concept embeddings.

## Architecture
- **Concept Extraction**: Connects to OpenMRS MySQL to extract concepts
- **Embedding Generation**: Uses sentence-transformers to create vector representations
- **Batch Processing**: Efficiently processes large volumes of concepts
- **Scheduled Execution**: Supports scheduled runs for keeping embeddings up-to-date

## Features
- Full pipeline execution (complete refresh)
- Incremental updates (coming soon)
- Scheduled runs (daily, weekly, hourly)
- Dry-run mode for testing
- Progress tracking and logging

## Configuration

Configuration is managed through the central `.env` file at the project root. Default values are defined in `packages/embedding-pipeline/package-metadata.json`.

### Key Environment Variables

**MySQL Configuration:**
- `MYSQL_HOST` - Database host (default: `mysql`)
- `MYSQL_PORT` - Database port (default: `3306`)
- `MYSQL_DATABASE` - Database name (default: `openmrs`)
- `MYSQL_USER` - Database user (default: `openmrs`)
- `MYSQL_PASSWORD` - Database password (default: `openmrs`)

**ChromaDB Configuration:**
- `CHROMADB_HOST` - Vector DB host (default: `vector-db`)
- `CHROMADB_PORT` - Vector DB port (default: `8000`)
- `CHROMA_AUTH_TOKEN` - Auth token (default: `test-token`)
- `CHROMA_COLLECTION` - Collection name (default: `openmrs_concepts`)

**Embedding Configuration:**
- `EMBEDDING_MODEL` - Model name (default: `sentence-transformers/all-MiniLM-L6-v2`)
- `EMBEDDING_DIM` - Embedding dimensions (default: `384`)
- `EMBEDDING_BATCH_SIZE` - Batch size (default: `32`)

**Pipeline Settings:**
- `PIPELINE_MODE` - Execution mode: full/incremental/scheduled (default: `full`)
- `SCHEDULE_INTERVAL` - For scheduled mode: daily/weekly/hourly (default: `daily`)
- `SCHEDULE_TIME` - Schedule time (default: `02:00`)
- `CONCEPT_LIMIT` - Limit concepts, 0=no limit (default: `0`)
- `LOG_LEVEL` - Logging level (default: `INFO`)
- `DRY_RUN` - Test mode without storage (default: `false`)

See `.env.example` for complete configuration.

## Deployment

### Build Docker Image
```bash
cd packages/embedding-pipeline
docker build -t embedding-pipeline:latest .
```

### Run with Docker Compose
```bash
cd packages/embedding-pipeline
docker-compose up
```

### Run Standalone
```bash
docker run --rm \
  --network instant \
  -e MYSQL_HOST=mysql \
  -e CHROMADB_HOST=vector-db \
  embedding-pipeline:latest
```

## Usage

### Full Pipeline Run
```bash
docker run --rm embedding-pipeline:latest python src/main.py --mode full
```

### Limited Test Run
```bash
docker run --rm embedding-pipeline:latest python src/main.py --mode full --limit 100
```

### Dry Run (No Storage)
```bash
docker run --rm embedding-pipeline:latest python src/main.py --mode full --dry-run
```

### Scheduled Execution
```bash
docker run -d embedding-pipeline:latest python src/main.py --mode scheduled
```

## Pipeline Workflow

1. **Initialize Components**
   - Connect to MySQL database
   - Load embedding model
   - Connect to ChromaDB

2. **Extract Concepts**
   - Query OpenMRS concept tables
   - Retrieve names, descriptions, synonyms, mappings
   - Process concept hierarchies

3. **Generate Embeddings**
   - Create searchable text from concept data
   - Generate vector embeddings in batches
   - Normalize for cosine similarity

4. **Store in Vector Database**
   - Clear existing embeddings (if full mode)
   - Store embeddings with metadata
   - Verify storage success

## Monitoring

### Logs
```bash
# View container logs
docker logs embedding-pipeline

# Access log files
docker exec embedding-pipeline ls -la /app/data/logs/
```

### Progress Tracking
The pipeline provides real-time progress updates:
- Concept extraction count
- Embedding generation progress bar
- Storage batch updates

## Performance Optimization

### Batch Size
Adjust `EMBEDDING_BATCH_SIZE` based on available memory:
- Small (16): < 2GB RAM
- Medium (32): 2-4GB RAM  
- Large (64): > 4GB RAM

### Model Selection
Choose embedding model based on requirements:
- `all-MiniLM-L6-v2`: Fast, lightweight (384 dims)
- `all-mpnet-base-v2`: Better quality (768 dims)
- `all-MiniLM-L12-v2`: Balanced (384 dims)

### Concept Limits
For testing or resource-constrained environments:
```bash
CONCEPT_LIMIT=1000  # Process only first 1000 concepts
```

## Troubleshooting

### Common Issues

1. **MySQL Connection Failed**
   ```
   Error: Failed to connect to MySQL database
   ```
   - Verify MySQL is running
   - Check network connectivity
   - Validate credentials

2. **ChromaDB Connection Failed**
   ```
   Error: Cannot connect to ChromaDB
   ```
   - Ensure vector-db service is running
   - Check authentication token
   - Verify network configuration

3. **Out of Memory**
   ```
   Error: CUDA out of memory / Process killed
   ```
   - Reduce EMBEDDING_BATCH_SIZE
   - Increase Docker memory limits
   - Use smaller embedding model

4. **Model Download Issues**
   ```
   Error: Cannot download model
   ```
   - Check internet connectivity
   - Verify MODEL_CACHE_DIR is writable
   - Pre-download model to cache directory

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python src/main.py --mode full --limit 10 --dry-run
```

### Testing
```bash
# Test concept extraction
python src/concept_extractor.py

# Test embedding generation
python src/embedding_service.py
```

## Data Schema

### Input (MySQL Concepts)
```sql
concept_id: INT
concept_name: VARCHAR
description: TEXT
synonyms: TEXT (pipe-separated)
mappings: TEXT (pipe-separated)
class_id: INT
datatype_id: INT
```

### Output (ChromaDB Embeddings)
```json
{
  "id": "concept_123",
  "embedding": [0.1, 0.2, ...],
  "metadata": {
    "concept_id": 123,
    "concept_name": "Hypertension",
    "description": "High blood pressure",
    "synonyms": "HTN|High BP",
    "mappings": "SNOMED:38341003",
    "class_id": 1
  }
}
```

## Related Documentation
- [Vector Database](./vector-db.md)
- [Augmented RAG Implementation](../AUGMENTED_RAG_IMPLEMENTATION_PLAN.md)
- [OpenMRS Documentation](https://wiki.openmrs.org/)