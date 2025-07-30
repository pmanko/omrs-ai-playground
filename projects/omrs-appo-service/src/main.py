"""Main FastAPI application for WhatsApp-OpenMRS-MedGemma service."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.core.config import get_settings
from src.core.logging_config import setup_logging
from src.api.v1.webhooks import router as webhook_router
from src.api.v1.auth import router as auth_router
from src.services.session_manager import session_manager


settings = get_settings()
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting WhatsApp-OpenMRS-MedGemma service...")
    
    # Initialize session manager
    await session_manager.connect()
    logger.info("Session manager connected")
    
    # Start background tasks
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    try:
        yield
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down service...")
        cleanup_task.cancel()
        await session_manager.disconnect()
        logger.info("Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="WhatsApp-OpenMRS-MedGemma Service",
    description="AI-powered appointment scheduling and medical triage via WhatsApp",
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
app.include_router(webhook_router, prefix="/api/webhook/whatsapp")
app.include_router(auth_router, prefix="/api/auth")


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "WhatsApp-OpenMRS-MedGemma Integration",
        "version": "0.1.0",
        "status": "running"
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
            "service_status": "running"
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"error": "Unable to get statistics"}


async def periodic_cleanup():
    """Periodic cleanup of expired sessions."""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            await session_manager.cleanup_expired_sessions()
            logger.debug("Periodic cleanup completed")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=True,
        log_level=settings.log_level.lower()
    )