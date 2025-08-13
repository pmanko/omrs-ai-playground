"""Main Embedding Pipeline Script

This script orchestrates the extraction of OpenMRS concepts and generation 
of embeddings for storage in ChromaDB.
"""

import sys
import time
import schedule
import click
import chromadb
from chromadb.config import Settings
from loguru import logger
from datetime import datetime
import pandas as pd

from config import (
    mysql_config, 
    chromadb_config, 
    embedding_config, 
    pipeline_config
)
from concept_extractor import ConceptExtractor
from embedding_service import EmbeddingService


class EmbeddingPipeline:
    """Manages the complete embedding generation pipeline"""
    
    def __init__(self):
        """Initialize pipeline components"""
        # Configure logging
        logger.remove()
        logger.add(
            sys.stderr, 
            level=pipeline_config.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
        )
        logger.add(
            "/app/data/logs/pipeline_{time}.log",
            rotation="500 MB",
            retention="7 days",
            level=pipeline_config.log_level
        )
        
        self.extractor = None
        self.embedding_service = None
        self.chroma_client = None
        self.collection = None
        
    def initialize_components(self):
        """Initialize all pipeline components"""
        logger.info("Initializing pipeline components...")
        
        # Initialize concept extractor
        logger.info("Connecting to MySQL database...")
        self.extractor = ConceptExtractor(mysql_config)
        
        # Initialize embedding service
        logger.info(f"Loading embedding model: {embedding_config.model_name}")
        self.embedding_service = EmbeddingService(embedding_config)
        
        # Initialize ChromaDB client
        logger.info(f"Connecting to ChromaDB at {chromadb_config.host}:{chromadb_config.port}")
        self.chroma_client = chromadb.HttpClient(
            host=chromadb_config.host,
            port=chromadb_config.port,
            settings=Settings(
                chroma_client_auth_provider="chromadb.auth.token.TokenAuthClientProvider",
                chroma_client_auth_credentials=chromadb_config.auth_token
            )
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=chromadb_config.collection_name,
            metadata={"description": "OpenMRS concept embeddings"}
        )
        
        logger.info(f"Collection '{chromadb_config.collection_name}' ready. Current count: {self.collection.count()}")
        
    def extract_concepts(self) -> pd.DataFrame:
        """Extract concepts from OpenMRS database"""
        logger.info("Extracting concepts from OpenMRS...")
        
        limit = pipeline_config.concept_limit if pipeline_config.concept_limit > 0 else None
        concepts_df = self.extractor.extract_concepts(limit=limit)
        
        logger.info(f"Extracted {len(concepts_df)} concepts")
        return concepts_df
    
    def generate_embeddings(self, concepts_df: pd.DataFrame):
        """Generate and store embeddings for concepts"""
        if pipeline_config.dry_run:
            logger.info("DRY RUN: Would generate embeddings for {} concepts", len(concepts_df))
            return
            
        logger.info(f"Generating embeddings for {len(concepts_df)} concepts...")
        
        # Generate embeddings
        embeddings = self.embedding_service.embed_concepts_dataframe(
            concepts_df,
            show_progress=True
        )
        
        # Prepare metadata
        metadata = concepts_df.to_dict('records')
        
        # Clean metadata - remove any None values and convert to strings
        for meta in metadata:
            for key, value in list(meta.items()):
                if pd.isna(value) or value is None:
                    meta[key] = ""
                elif not isinstance(value, (str, int, float, bool)):
                    meta[key] = str(value)
        
        # Generate IDs
        ids = [str(row['concept_id']) for _, row in concepts_df.iterrows()]
        
        # Store in ChromaDB in batches
        batch_size = 100
        total_stored = 0
        
        for i in range(0, len(embeddings), batch_size):
            batch_end = min(i + batch_size, len(embeddings))
            
            self.collection.add(
                embeddings=embeddings[i:batch_end].tolist(),
                metadatas=metadata[i:batch_end],
                ids=ids[i:batch_end]
            )
            
            total_stored += (batch_end - i)
            logger.info(f"Stored {total_stored}/{len(embeddings)} embeddings...")
        
        logger.info(f"Successfully stored {total_stored} concept embeddings")
    
    def run_full_pipeline(self):
        """Execute the complete embedding pipeline"""
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("Starting Full Embedding Pipeline")
        logger.info("=" * 60)
        
        try:
            # Initialize components
            self.initialize_components()
            
            # Clear existing embeddings if running full pipeline
            if pipeline_config.mode == "full" and not pipeline_config.dry_run:
                logger.warning("Clearing existing embeddings for full pipeline run...")
                # Get all IDs and delete them
                existing_ids = []
                offset = 0
                limit = 1000
                
                while True:
                    batch = self.collection.get(
                        limit=limit,
                        offset=offset,
                        include=[]
                    )
                    if not batch['ids']:
                        break
                    existing_ids.extend(batch['ids'])
                    offset += limit
                
                if existing_ids:
                    self.collection.delete(ids=existing_ids)
                    logger.info(f"Deleted {len(existing_ids)} existing embeddings")
            
            # Extract concepts
            concepts_df = self.extract_concepts()
            
            if concepts_df.empty:
                logger.warning("No concepts found to process")
                return
            
            # Generate and store embeddings
            self.generate_embeddings(concepts_df)
            
            # Get statistics
            stats = self.extractor.get_statistics()
            logger.info(f"Database statistics: {stats}")
            
            elapsed_time = time.time() - start_time
            logger.info(f"Pipeline completed in {elapsed_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
        finally:
            # Cleanup
            if self.extractor:
                self.extractor.close()
    
    def run_incremental_pipeline(self):
        """Run incremental update for new/modified concepts"""
        logger.info("=" * 60)
        logger.info("Starting Incremental Embedding Pipeline")
        logger.info("=" * 60)
        
        # TODO: Implement incremental updates based on date_changed
        logger.warning("Incremental mode not yet implemented, running full pipeline instead")
        self.run_full_pipeline()
    
    def run_scheduled(self):
        """Run pipeline on a schedule"""
        logger.info(f"Scheduling pipeline to run {pipeline_config.schedule_interval} at {pipeline_config.schedule_time}")
        
        if pipeline_config.schedule_interval == "hourly":
            schedule.every().hour.do(self.run_full_pipeline)
        elif pipeline_config.schedule_interval == "daily":
            schedule.every().day.at(pipeline_config.schedule_time).do(self.run_full_pipeline)
        elif pipeline_config.schedule_interval == "weekly":
            schedule.every().week.at(pipeline_config.schedule_time).do(self.run_full_pipeline)
        else:
            logger.error(f"Unknown schedule interval: {pipeline_config.schedule_interval}")
            return
        
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


@click.command()
@click.option('--mode', default='full', help='Pipeline mode: full, incremental, or scheduled')
@click.option('--limit', default=0, help='Limit number of concepts to process (0 = no limit)')
@click.option('--dry-run', is_flag=True, help='Run without actually storing embeddings')
def main(mode, limit, dry_run):
    """OpenMRS Concept Embedding Pipeline"""
    
    # Override config with CLI arguments
    if limit > 0:
        pipeline_config.concept_limit = limit
    if dry_run:
        pipeline_config.dry_run = True
    pipeline_config.mode = mode
    
    # Create and run pipeline
    pipeline = EmbeddingPipeline()
    
    if mode == "full":
        pipeline.run_full_pipeline()
    elif mode == "incremental":
        pipeline.run_incremental_pipeline()
    elif mode == "scheduled":
        pipeline.run_scheduled()
    else:
        logger.error(f"Unknown mode: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()