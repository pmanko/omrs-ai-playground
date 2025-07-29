from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """WhatsApp message types."""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    INTERACTIVE = "interactive"


class WhatsAppMessage(BaseModel):
    """WhatsApp incoming message model."""
    message_id: str = Field(..., alias="id")
    from_number: str = Field(..., alias="from")
    timestamp: str
    type: MessageType
    text: Optional[Dict[str, str]] = None
    interactive: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True


class WhatsAppWebhookData(BaseModel):
    """WhatsApp webhook payload model."""
    object: str
    entry: List[Dict[str, Any]]
