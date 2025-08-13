"""Configuration for Embedding Pipeline"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class MySQLConfig:
    """Configuration for OpenMRS MySQL database connection"""
    host: str = os.getenv("MYSQL_HOST", "mysql")
    port: int = int(os.getenv("MYSQL_PORT", "3306"))
    database: str = os.getenv("MYSQL_DATABASE", "openmrs")
    username: str = os.getenv("MYSQL_USER", "openmrs")
    password: str = os.getenv("MYSQL_PASSWORD", "openmrs")


@dataclass
class ChromaDBConfig:
    """Configuration for ChromaDB connection"""
    host: str = os.getenv("CHROMADB_HOST", "vector-db")
    port: int = int(os.getenv("CHROMADB_PORT", "8000"))
    auth_token: str = os.getenv("CHROMA_AUTH_TOKEN", "test-token")
    collection_name: str = os.getenv("CHROMA_COLLECTION", "openmrs_concepts")
    

@dataclass 
class EmbeddingConfig:
    """Configuration for embedding model and generation"""
    model_name: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    dimension: int = int(os.getenv("EMBEDDING_DIM", "384"))
    batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    cache_dir: str = os.getenv("MODEL_CACHE_DIR", "/app/data/cache")


@dataclass
class PipelineConfig:
    """Configuration for the embedding pipeline"""
    mode: str = os.getenv("PIPELINE_MODE", "full")  # full, incremental, scheduled
    schedule_interval: str = os.getenv("SCHEDULE_INTERVAL", "daily")  # daily, weekly, hourly
    schedule_time: str = os.getenv("SCHEDULE_TIME", "02:00")  # Time for scheduled runs
    concept_limit: int = int(os.getenv("CONCEPT_LIMIT", "0"))  # 0 = no limit
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    dry_run: bool = os.getenv("DRY_RUN", "false").lower() == "true"


# Initialize configurations
mysql_config = MySQLConfig()
chromadb_config = ChromaDBConfig()
embedding_config = EmbeddingConfig()
pipeline_config = PipelineConfig()