"""WhatsApp webhook handlers for receiving messages."""
from fastapi import APIRouter, Request, Response, HTTPException, Query
from fastapi.responses import PlainTextResponse
from loguru import logger
import uuid
from typing import Optional
from .config import get_settings
from .models import (
    WhatsAppWebhookData, 
    WhatsAppMessage, 
    ConversationSession,
    PatientProfile,
    ConversationState
)
from .session_manager import session_manager
from .conversation_manager import conversation_manager


router = APIRouter(prefix="/webhook", tags=["webhook"])
settings = get_settings()


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
) -> PlainTextResponse:
    """Verify WhatsApp webhook during setup."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_webhook_verify_token:
        logger.info("WhatsApp webhook verified successfully")
        return PlainTextResponse(content=hub_challenge)
    
    logger.warning(f"Invalid webhook verification attempt: {hub_verify_token}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp")
async def handle_whatsapp_webhook(request: Request) -> Response:
    """Handle incoming WhatsApp messages and status updates."""
    try:
        # Parse webhook data
        data = await request.json()
        webhook_data = WhatsAppWebhookData(**data)
        
        # Process each entry
        for entry in webhook_data.entry:
            await process_webhook_entry(entry)
        
        # Return 200 OK to acknowledge receipt
        return Response(status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Still return 200 to prevent retries
        return Response(status_code=200)


async def process_webhook_entry(entry: dict) -> None:
    """Process a single webhook entry."""
    changes = entry.get("changes", [])
    
    for change in changes:
        value = change.get("value", {})
        
        # Handle incoming messages
        if "messages" in value:
            for message_data in value["messages"]:
                await process_incoming_message(message_data, value.get("contacts", []))
        
        # Handle status updates
        if "statuses" in value:
            for status in value["statuses"]:
                await process_status_update(status)


async def process_incoming_message(message_data: dict, contacts: list) -> None:
    """Process an incoming WhatsApp message."""
    try:
        # Parse message
        message = WhatsAppMessage(**message_data)
        
        # Get contact info
        contact_info = next(
            (c for c in contacts if c.get("wa_id") == message.from_number), 
            {}
        )
        
        # Extract message content based on type
        content = extract_message_content(message)
        
        if not content:
            logger.warning(f"No content extracted from message {message.message_id}")
            return
        
        # Get or create session
        session = await get_or_create_session(message.from_number, contact_info)
        
        # Add message to conversation history
        session.add_message(
            role="user",
            content=content,
            metadata={
                "message_id": message.message_id,
                "message_type": message.type,
                "timestamp": message.timestamp
            }
        )
        
        # Save session
        await session_manager.save_session(session)
        
        # Process message through conversation manager
        await conversation_manager.process_message(session, content)
        
        logger.info(f"Processed message from {message.from_number}: {content[:50]}...")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")


def extract_message_content(message: WhatsAppMessage) -> Optional[str]:
    """Extract content from different message types."""
    if message.type == "text" and message.text:
        return message.text.get("body", "")
    
    elif message.type == "interactive" and message.interactive:
        # Handle button replies
        if message.interactive.get("type") == "button_reply":
            return message.interactive.get("button_reply", {}).get("title", "")
        
        # Handle list replies
        elif message.interactive.get("type") == "list_reply":
            return message.interactive.get("list_reply", {}).get("title", "")
    
    # For other message types, return a placeholder
    else:
        return f"[{message.type} message received]"
    
    return None


async def get_or_create_session(
    phone_number: str, 
    contact_info: dict
) -> ConversationSession:
    """Get existing session or create a new one."""
    # Try to get existing session
    session = await session_manager.get_session(phone_number)
    
    if session:
        return session
    
    # Create new session
    session_id = str(uuid.uuid4())
    
    # Create patient profile
    patient_profile = PatientProfile(
        phone_number=phone_number,
        name=contact_info.get("profile", {}).get("name"),
    )
    
    # Create new session
    session = ConversationSession(
        session_id=session_id,
        phone_number=phone_number,
        patient_profile=patient_profile,
        state=ConversationState.INITIAL
    )
    
    logger.info(f"Created new session for {phone_number}")
    return session


async def process_status_update(status: dict) -> None:
    """Process message status updates."""
    status_type = status.get("status")
    message_id = status.get("id")
    recipient = status.get("recipient_id")
    
    logger.debug(
        f"Status update: {status_type} for message {message_id} to {recipient}"
    )
    
    # Handle different status types if needed
    if status_type == "failed":
        errors = status.get("errors", [])
        logger.error(f"Message {message_id} failed: {errors}")