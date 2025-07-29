"""WhatsApp Cloud API client for sending messages."""
import httpx
from typing import List, Dict, Any, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import get_settings


class WhatsAppClient:
    """Client for WhatsApp Cloud API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = f"https://graph.facebook.com/v18.0/{self.settings.whatsapp_phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {self.settings.whatsapp_access_token}",
            "Content-Type": "application/json"
        }
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def send_text_message(
        self, 
        to: str, 
        text: str,
        preview_url: bool = False
    ) -> Dict[str, Any]:
        """Send a text message to a WhatsApp number."""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {
                    "preview_url": preview_url,
                    "body": text
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                logger.debug(f"Text message sent to {to}")
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to send text message to {to}: {e}")
            raise
    
    async def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: List[Dict[str, str]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send interactive button message."""
        try:
            interactive = {
                "type": "button",
                "body": {"text": body_text}
            }
            
            if header_text:
                interactive["header"] = {"type": "text", "text": header_text}
            
            if footer_text:
                interactive["footer"] = {"text": footer_text}
            
            # Format buttons for WhatsApp API
            interactive["action"] = {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": btn.get("id", f"btn_{i}"),
                            "title": btn["title"][:20]  # WhatsApp limits button text to 20 chars
                        }
                    }
                    for i, btn in enumerate(buttons[:3])  # Max 3 buttons
                ]
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "interactive",
                "interactive": interactive
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                logger.debug(f"Interactive buttons sent to {to}")
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to send interactive buttons to {to}: {e}")
            raise
    
    async def send_list_message(
        self,
        to: str,
        body_text: str,
        button_text: str,
        sections: List[Dict[str, Any]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send interactive list message."""
        try:
            interactive = {
                "type": "list",
                "body": {"text": body_text},
                "action": {
                    "button": button_text[:20],
                    "sections": sections
                }
            }
            
            if header_text:
                interactive["header"] = {"type": "text", "text": header_text}
            
            if footer_text:
                interactive["footer"] = {"text": footer_text}
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "interactive",
                "interactive": interactive
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                logger.debug(f"List message sent to {to}")
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to send list message to {to}: {e}")
            raise
    
    async def mark_message_as_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                logger.debug(f"Message {message_id} marked as read")
                return True
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to mark message {message_id} as read: {e}")
            return False
    
    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send a template message."""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language_code}
                }
            }
            
            if components:
                payload["template"]["components"] = components
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                logger.debug(f"Template message '{template_name}' sent to {to}")
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to send template message to {to}: {e}")
            raise


# Singleton instance
whatsapp_client = WhatsAppClient()