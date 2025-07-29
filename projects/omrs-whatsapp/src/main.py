"""Main application entry point for WhatsApp-OpenMRS-MedGemma service."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .config import get_settings
from .logging_config import setup_logging
from .session_manager import session_manager
from .webhooks import router as webhook_router


# Setup logging
setup_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting WhatsApp-OpenMRS-MedGemma service...")
    
    # Connect to Redis
    await session_manager.connect()
    
    # Start background tasks
    asyncio.create_task(periodic_cleanup())
    
    logger.info("Service started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down service...")
    
    # Disconnect from Redis
    await session_manager.disconnect()
    
    logger.info("Service stopped.")


# Create FastAPI app
app = FastAPI(
    title="WhatsApp-OpenMRS-MedGemma Service",
    description="AI-powered appointment scheduling and triage via WhatsApp",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhook_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "WhatsApp-OpenMRS-MedGemma",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check Redis connection
        active_sessions = await session_manager.get_active_sessions_count()
        
        return {
            "status": "healthy",
            "active_sessions": active_sessions,
            "redis": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/api/stats")
async def get_stats():
    """Get service statistics."""
    try:
        active_sessions = await session_manager.get_active_sessions_count()
        
        return {
            "active_sessions": active_sessions,
            "service_uptime": "N/A",  # Would implement proper uptime tracking
            "total_processed": "N/A"   # Would implement message counting
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"error": str(e)}


async def periodic_cleanup():
    """Periodically clean up expired sessions."""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            await session_manager.cleanup_expired_sessions()
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )