"""Logging configuration for the service."""
import sys
from loguru import logger
from .config import get_settings


def setup_logging():
    """Configure loguru for the application."""
    settings = get_settings()
    
    # Remove default logger
    logger.remove()
    
    # Add console logger with custom format
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # Add file logger for production
    if settings.environment == "production":
        logger.add(
            "logs/omrs-whatsapp.log",
            rotation="10 MB",
            retention="7 days",
            level=settings.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )
    
    return logger