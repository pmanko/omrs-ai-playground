"""Simplified OpenMRS client for patient authentication."""
import httpx
import base64
from typing import Optional, Dict, Any
from loguru import logger
from src.core.config import get_settings


class OpenMRSClient:
    """Simplified OpenMRS client for patient authentication."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.openmrs_base_url
        
        # Create basic auth header
        credentials = f"{self.settings.openmrs_username}:{self.settings.openmrs_password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        logger.info(f"OpenMRS client initialized with endpoint: {self.base_url}")
    
    async def get_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient by OpenMRS patient ID using REST API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/patient/{patient_id}",
                    headers=self.headers,
                    params={"v": "full"}  # Get full patient representation
                )
                
                if response.status_code == 404:
                    logger.info(f"Patient not found with ID: {patient_id}")
                    return None
                
                response.raise_for_status()
                patient_data = response.json()
                
                logger.info(f"Successfully retrieved patient {patient_id}")
                return patient_data
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"Patient not found with ID: {patient_id}")
                return None
            else:
                logger.error(f"HTTP error getting patient {patient_id}: {e}")
                return None
        except Exception as e:
            logger.error(f"Error getting patient {patient_id}: {e}")
            return None


# Singleton instance
openmrs_client = OpenMRSClient()