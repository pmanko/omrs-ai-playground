# Augmented RAG Implementation Plan for Multiagent Medical System

## Executive Summary
This document outlines the implementation plan for integrating an Augmented Retrieval-Augmented Generation (RAG) approach into the existing multiagent medical chat system. The plan focuses on leveraging OpenMRS concept embeddings to enhance clinical query responses through semantic search capabilities.

## Current State Analysis

### Existing Architecture
- **Multiagent System**: Already implemented with user_proxy_agent, medgemma_agent, and clinical_research_agent
- **FHIR Integration**: Functional connection to OpenMRS FHIR endpoints
- **Spark SQL**: Operational SQL-on-FHIR via Spark Thrift for Parquet data
- **LLM Integration**: Working with LM Studio and Gemini API support
- **A2A Layer**: Simulated Agent-to-Agent communication bus and registry

### Gap Analysis
1. **No Vector Database**: Need to integrate ChromaDB or FAISS for embedding storage
2. **No Embedding Pipeline**: Missing text-to-vector conversion capability
3. **No MySQL Connection**: Need direct access to OpenMRS MySQL for concept extraction
4. **No Semantic Search**: Current system relies only on structured queries

## Implementation Architecture

### Phase 1: Infrastructure Setup

#### 1.1 Dependencies Installation
```python
# New dependencies to add to pyproject.toml
dependencies = {
    "chromadb": "^0.4.24",  # Vector database
    "sentence-transformers": "^2.5.1",  # Embedding models
    "pymysql": "^1.1.0",  # MySQL connector
    "sqlalchemy": "^2.0.0",  # ORM for database operations
    "pandas": "^2.0.0",  # Data processing
    "tqdm": "^4.66.0",  # Progress bars for batch processing
}
```

#### 1.2 Configuration Extensions
```python
# Add to server/config.py
@dataclass
class MySQLConfig:
    host: str = os.getenv("MYSQL_HOST", "localhost")
    port: int = int(os.getenv("MYSQL_PORT", "3306"))
    database: str = os.getenv("MYSQL_DATABASE", "openmrs")
    username: str = os.getenv("MYSQL_USER", "openmrs")
    password: str = os.getenv("MYSQL_PASSWORD", "openmrs")

@dataclass
class VectorDBConfig:
    provider: str = os.getenv("VECTOR_DB_PROVIDER", "chromadb")
    persist_directory: str = os.getenv("VECTOR_DB_DIR", "./data/vector_db")
    collection_name: str = os.getenv("VECTOR_COLLECTION", "openmrs_concepts")
    
@dataclass
class EmbeddingConfig:
    model_name: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    dimension: int = int(os.getenv("EMBEDDING_DIM", "384"))
    batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
```

### Phase 2: Core Components Implementation

#### 2.1 OpenMRS Concept Extractor
**File**: `server/services/concept_extractor.py`

```python
class ConceptExtractor:
    """Extract concepts from OpenMRS MySQL database"""
    
    def __init__(self, mysql_config: MySQLConfig):
        self.config = mysql_config
        self.engine = self._create_engine()
    
    def extract_concepts(self) -> pd.DataFrame:
        """
        Extract concepts with their names, descriptions, and mappings
        Returns DataFrame with: concept_id, name, description, synonyms, mappings
        """
        query = """
        SELECT 
            c.concept_id,
            cn.name as concept_name,
            cn.locale,
            cd.description,
            c.class_id,
            c.datatype_id,
            GROUP_CONCAT(DISTINCT cs.name SEPARATOR '|') as synonyms,
            GROUP_CONCAT(DISTINCT 
                CONCAT(crs.source, ':', crm.source_code) 
                SEPARATOR '|'
            ) as mappings
        FROM concept c
        LEFT JOIN concept_name cn ON c.concept_id = cn.concept_id 
            AND cn.locale = 'en' 
            AND cn.concept_name_type = 'FULLY_SPECIFIED'
        LEFT JOIN concept_description cd ON c.concept_id = cd.concept_id 
            AND cd.locale = 'en'
        LEFT JOIN concept_name cs ON c.concept_id = cs.concept_id 
            AND cs.locale = 'en' 
            AND cs.concept_name_type = 'SYNONYM'
        LEFT JOIN concept_reference_map crm ON c.concept_id = crm.concept_id
        LEFT JOIN concept_reference_source crs ON crm.concept_source_id = crs.concept_source_id
        WHERE c.retired = 0
        GROUP BY c.concept_id
        """
        return pd.read_sql(query, self.engine)
    
    def extract_concept_sets(self) -> pd.DataFrame:
        """Extract concept set relationships"""
        # Implementation for concept hierarchies
        pass
```

#### 2.2 Embedding Service
**File**: `server/services/embedding_service.py`

```python
class EmbeddingService:
    """Handle text-to-vector embeddings using sentence-transformers"""
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.model = SentenceTransformer(config.model_name)
        
    def create_concept_text(self, row: pd.Series) -> str:
        """
        Create searchable text from concept data
        Combines name, description, synonyms for rich semantic representation
        """
        parts = [
            f"Concept: {row['concept_name']}",
            f"Description: {row.get('description', '')}",
            f"Synonyms: {row.get('synonyms', '')}",
            f"Mappings: {row.get('mappings', '')}"
        ]
        return " ".join(filter(None, parts))
    
    def batch_embed(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for batch of texts"""
        return self.model.encode(
            texts, 
            batch_size=self.config.batch_size,
            show_progress_bar=True
        )
    
    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query for search"""
        return self.model.encode(query)
```

#### 2.3 Vector Database Manager
**File**: `server/services/vector_db_manager.py`

```python
import chromadb
from chromadb.config import Settings

class VectorDBManager:
    """Manage vector database operations"""
    
    def __init__(self, config: VectorDBConfig):
        self.config = config
        self.client = chromadb.PersistentClient(
            path=config.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = None
        
    def initialize_collection(self):
        """Create or get collection for OpenMRS concepts"""
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"description": "OpenMRS concept embeddings"}
        )
    
    def add_embeddings(self, 
                      embeddings: np.ndarray,
                      metadata: List[dict],
                      ids: List[str]):
        """Store embeddings with metadata"""
        self.collection.add(
            embeddings=embeddings.tolist(),
            metadatas=metadata,
            ids=ids
        )
    
    def search(self, query_embedding: np.ndarray, n_results: int = 10) -> dict:
        """Semantic search for similar concepts"""
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results,
            include=['metadatas', 'distances', 'documents']
        )
        return results
```

#### 2.4 Hybrid RAG Module
**File**: `server/services/hybrid_rag.py`

```python
class HybridRAG:
    """
    Implements hybrid retrieval combining semantic search with structured queries
    """
    
    def __init__(self, 
                 vector_db: VectorDBManager,
                 embedding_service: EmbeddingService,
                 spark_conn: Optional[Any] = None):
        self.vector_db = vector_db
        self.embedding_service = embedding_service
        self.spark_conn = spark_conn
        
    async def semantic_search(self, query: str, scope: dict = None) -> List[dict]:
        """
        Step 1: Semantic search over concept embeddings
        Returns relevant concept IDs and metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_query(query)
        
        # Search vector database
        results = self.vector_db.search(query_embedding, n_results=20)
        
        # Filter by scope if provided
        if scope and scope.get('facility_id'):
            # Apply facility-specific filtering
            pass
            
        return self._format_semantic_results(results)
    
    async def augmented_retrieval(self, 
                                 query: str, 
                                 semantic_results: List[dict]) -> dict:
        """
        Step 2: Use semantic results to enhance structured queries
        """
        # Extract concept IDs from semantic search
        concept_ids = [r['concept_id'] for r in semantic_results]
        
        # Build enhanced SQL query with concept constraints
        enhanced_sql = self._build_enhanced_query(query, concept_ids)
        
        # Execute against Spark/Parquet
        structured_data = await self._execute_sql(enhanced_sql)
        
        return {
            'semantic_context': semantic_results,
            'structured_data': structured_data,
            'query_metadata': {
                'original_query': query,
                'concepts_found': len(concept_ids),
                'enhanced_sql': enhanced_sql
            }
        }
    
    def _build_enhanced_query(self, 
                             original_query: str, 
                             concept_ids: List[str]) -> str:
        """
        Enhance SQL query with semantic concept constraints
        """
        # Implementation to inject concept filters into SQL
        base_sql = f"""
        SELECT * FROM observation 
        WHERE concept_id IN ({','.join(map(str, concept_ids))})
        ORDER BY date DESC
        LIMIT 50
        """
        return base_sql
```

### Phase 3: Integration with Clinical Research Agent

#### 3.1 Enhanced FHIR Agent
**File**: `server/agents/fhir_agent_enhanced.py`

```python
# Enhance existing fhir_agent.py

def run_enhanced_clinical_research_agent():
    """Enhanced version with RAG capabilities"""
    
    # Initialize RAG components
    vector_db = VectorDBManager(vector_db_config)
    embedding_service = EmbeddingService(embedding_config)
    hybrid_rag = HybridRAG(vector_db, embedding_service)
    
    # ... existing agent setup ...
    
    def process_message(msg):
        payload = msg.get("payload", {})
        query = payload.get("query", "")
        use_rag = payload.get("use_rag", True)  # Default to using RAG
        
        if use_rag:
            # Step 1: Semantic search for relevant concepts
            semantic_results = hybrid_rag.semantic_search(query)
            
            # Step 2: Enhanced retrieval with concept context
            augmented_data = hybrid_rag.augmented_retrieval(
                query, 
                semantic_results
            )
            
            # Step 3: Generate response with MedGemma
            synthesis_prompt = _build_synthesis_prompt(
                query,
                augmented_data['semantic_context'],
                augmented_data['structured_data']
            )
            
            response = llm_client.generate_chat(
                llm_config.med_model,
                synthesis_prompt,
                temperature=0.2
            )
        else:
            # Fallback to original implementation
            response = _original_process(query)
            
        return response
```

### Phase 4: Embedding Pipeline Management

#### 4.1 Batch Processing Pipeline
**File**: `server/pipelines/embedding_pipeline.py`

```python
class EmbeddingPipeline:
    """Manage the offline embedding generation process"""
    
    def __init__(self):
        self.extractor = ConceptExtractor(mysql_config)
        self.embedding_service = EmbeddingService(embedding_config)
        self.vector_db = VectorDBManager(vector_db_config)
        
    def run_full_pipeline(self):
        """Execute complete embedding pipeline"""
        print("Starting OpenMRS Concept Embedding Pipeline...")
        
        # Step 1: Extract concepts from MySQL
        print("Extracting concepts from OpenMRS...")
        concepts_df = self.extractor.extract_concepts()
        print(f"Extracted {len(concepts_df)} concepts")
        
        # Step 2: Prepare text for embedding
        print("Preparing concept texts...")
        concept_texts = concepts_df.apply(
            self.embedding_service.create_concept_text, 
            axis=1
        ).tolist()
        
        # Step 3: Generate embeddings in batches
        print("Generating embeddings...")
        embeddings = self.embedding_service.batch_embed(concept_texts)
        
        # Step 4: Prepare metadata
        metadata = concepts_df.to_dict('records')
        ids = [str(row['concept_id']) for _, row in concepts_df.iterrows()]
        
        # Step 5: Store in vector database
        print("Storing in vector database...")
        self.vector_db.initialize_collection()
        self.vector_db.add_embeddings(embeddings, metadata, ids)
        
        print(f"Pipeline complete! Stored {len(embeddings)} concept embeddings")
        
    def update_incremental(self, since_date: str):
        """Update embeddings for new/modified concepts"""
        # Implementation for incremental updates
        pass
```

#### 4.2 API Endpoints for Pipeline Management
**File**: `server/api/rag_endpoints.py`

```python
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/rag", tags=["RAG"])

class PipelineRequest(BaseModel):
    mode: str = "full"  # full or incremental
    since_date: Optional[str] = None

@router.post("/pipeline/run")
async def run_embedding_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
):
    """Trigger embedding pipeline execution"""
    pipeline = EmbeddingPipeline()
    
    if request.mode == "full":
        background_tasks.add_task(pipeline.run_full_pipeline)
    else:
        background_tasks.add_task(
            pipeline.update_incremental, 
            request.since_date
        )
    
    return {"status": "Pipeline started", "mode": request.mode}

@router.get("/stats")
async def get_rag_stats():
    """Get statistics about the RAG system"""
    vector_db = VectorDBManager(vector_db_config)
    vector_db.initialize_collection()
    
    stats = {
        "total_concepts": vector_db.collection.count(),
        "embedding_model": embedding_config.model_name,
        "vector_dimension": embedding_config.dimension,
        "last_update": "TODO: Track this"
    }
    return stats

@router.post("/search")
async def semantic_search(query: str, limit: int = 10):
    """Test semantic search directly"""
    embedding_service = EmbeddingService(embedding_config)
    vector_db = VectorDBManager(vector_db_config)
    vector_db.initialize_collection()
    
    query_embedding = embedding_service.embed_query(query)
    results = vector_db.search(query_embedding, n_results=limit)
    
    return {
        "query": query,
        "results": results
    }
```

### Phase 5: Testing & Validation

#### 5.1 Unit Tests
```python
# tests/test_rag_components.py

def test_concept_extraction():
    """Test MySQL concept extraction"""
    extractor = ConceptExtractor(test_mysql_config)
    concepts = extractor.extract_concepts()
    assert len(concepts) > 0
    assert 'concept_id' in concepts.columns

def test_embedding_generation():
    """Test embedding service"""
    service = EmbeddingService(test_embedding_config)
    text = "Diabetes mellitus type 2"
    embedding = service.embed_query(text)
    assert embedding.shape[0] == test_embedding_config.dimension

def test_semantic_search():
    """Test vector database search"""
    # Test implementation
    pass

def test_hybrid_rag():
    """Test complete RAG pipeline"""
    # Test implementation
    pass
```

#### 5.2 Integration Tests
```python
# tests/test_integration.py

async def test_enhanced_clinical_agent():
    """Test clinical research agent with RAG"""
    # Send test query through agent
    # Verify semantic enhancement
    # Check response quality
    pass
```

### Phase 6: Deployment Configuration

#### 6.1 Docker Updates
```dockerfile
# Add to existing Dockerfile
RUN pip install chromadb sentence-transformers pymysql sqlalchemy pandas

# Create volume for vector database
VOLUME ["/app/data/vector_db"]
```

#### 6.2 Environment Variables
```bash
# Add to .env file
# MySQL Configuration
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=openmrs
MYSQL_USER=openmrs
MYSQL_PASSWORD=openmrs

# Vector Database
VECTOR_DB_PROVIDER=chromadb
VECTOR_DB_DIR=/app/data/vector_db
VECTOR_COLLECTION=openmrs_concepts

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM=384
EMBEDDING_BATCH_SIZE=32
```

### Phase 7: Monitoring & Optimization

#### 7.1 Performance Metrics
- Embedding generation time
- Search latency
- Memory usage
- Cache hit rates

#### 7.2 Quality Metrics
- Semantic search relevance scores
- Clinical accuracy validation
- User satisfaction metrics

## Implementation Timeline

### Week 1: Infrastructure Setup
- [ ] Install dependencies
- [ ] Configure MySQL connection
- [ ] Set up ChromaDB
- [ ] Initialize embedding model

### Week 2: Core Development
- [ ] Implement concept extractor
- [ ] Build embedding service
- [ ] Create vector DB manager
- [ ] Develop hybrid RAG module

### Week 3: Integration
- [ ] Enhance clinical research agent
- [ ] Create API endpoints
- [ ] Build pipeline management

### Week 4: Testing & Deployment
- [ ] Unit testing
- [ ] Integration testing
- [ ] Performance optimization
- [ ] Documentation

## Risk Mitigation

### Technical Risks
1. **Memory constraints**: Use smaller embedding models initially
2. **Query latency**: Implement caching layer
3. **Data freshness**: Schedule regular re-indexing

### Operational Risks
1. **MySQL access**: Ensure proper credentials and network access
2. **Storage requirements**: Monitor vector DB growth
3. **Model availability**: Have fallback to non-RAG mode

## Success Metrics

1. **Retrieval Accuracy**: >85% relevant concept matches
2. **Query Latency**: <500ms for semantic search
3. **System Uptime**: >99.9% availability
4. **User Adoption**: >70% queries using RAG enhancement

## Conclusion

This implementation plan provides a structured approach to integrating augmented RAG capabilities into the existing multiagent medical system. The hybrid approach combining semantic search with structured queries will significantly enhance the system's ability to understand and respond to complex clinical queries.

## Next Steps

1. Review and approve implementation plan
2. Set up development environment
3. Begin Phase 1 infrastructure setup
4. Create project tracking dashboard