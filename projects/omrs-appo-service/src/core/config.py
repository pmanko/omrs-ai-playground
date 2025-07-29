"""Configuration module for the WhatsApp-OpenMRS-MedGemma service."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # WhatsApp Configuration
    whatsapp_api_key: str = Field(..., description="WhatsApp API Key")
    whatsapp_phone_number_id: str = Field(..., description="WhatsApp Phone Number ID")
    whatsapp_webhook_verify_token: str = Field(..., description="Webhook verification token")
    whatsapp_access_token: str = Field(..., description="WhatsApp Access Token")
    
    # OpenMRS Configuration
    openmrs_base_url: str = Field(
        default="http://localhost:8080/openmrs/ws/fhir2/R4",
        description="OpenMRS FHIR API base URL"
    )
    openmrs_username: str = Field(default="admin", description="OpenMRS username")
    openmrs_password: str = Field(default="Admin123", description="OpenMRS password")
    
    # Google MedGemma Configuration
    google_api_key: str = Field(..., description="Google API Key for MedGemma")
    medgemma_model: str = Field(
        default="gemini-1.5-flash",
        description="MedGemma model name"
    )
    
    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    redis_db: int = Field(default=0, description="Redis database number")
    
    # Service Configuration
    service_port: int = Field(default=8000, description="Service port")
    service_host: str = Field(default="0.0.0.0", description="Service host")
    log_level: str = Field(default="INFO", description="Logging level")
    environment: str = Field(default="development", description="Environment name")
    
    # Webhook Configuration
    webhook_base_url: str = Field(..., description="Base URL for webhooks")
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of {valid_levels}")
        return v.upper()
    
    @validator("openmrs_base_url")
    def validate_openmrs_url(cls, v):
        """Ensure OpenMRS URL ends with proper FHIR path."""
        if not v.endswith("/"):
            v += "/"
        if "fhir" not in v.lower():
            raise ValueError("OpenMRS URL must point to FHIR endpoint")
        return v.rstrip("/")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()