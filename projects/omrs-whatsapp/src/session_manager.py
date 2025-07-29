"""Session management using Redis for conversation state persistence."""
import json
import redis.asyncio as redis
from typing import Optional
from datetime import timedelta
from loguru import logger
from .models import ConversationSession, ConversationState
from .config import get_settings


class SessionManager:
    """Manages conversation sessions in Redis."""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client = None
        self.session_ttl = timedelta(hours=24)  # Sessions expire after 24 hours
        
    async def connect(self):
        """Connect to Redis."""
        self.redis_client = await redis.from_url(
            self.settings.redis_url,
            db=self.settings.redis_db,
            decode_responses=True
        )
        logger.info("Connected to Redis")
        
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    def _get_session_key(self, phone_number: str) -> str:
        """Generate Redis key for a session."""
        return f"whatsapp_session:{phone_number}"
    
    async def get_session(self, phone_number: str) -> Optional[ConversationSession]:
        """Retrieve a session from Redis."""
        try:
            key = self._get_session_key(phone_number)
            session_data = await self.redis_client.get(key)
            
            if session_data:
                data = json.loads(session_data)
                return ConversationSession(**data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving session for {phone_number}: {e}")
            return None
    
    async def save_session(self, session: ConversationSession) -> bool:
        """Save a session to Redis."""
        try:
            key = self._get_session_key(session.phone_number)
            session_data = session.model_dump_json()
            
            await self.redis_client.setex(
                key,
                self.session_ttl,
                session_data
            )
            
            logger.debug(f"Session saved for {session.phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session for {session.phone_number}: {e}")
            return False
    
    async def delete_session(self, phone_number: str) -> bool:
        """Delete a session from Redis."""
        try:
            key = self._get_session_key(phone_number)
            result = await self.redis_client.delete(key)
            
            logger.debug(f"Session deleted for {phone_number}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error deleting session for {phone_number}: {e}")
            return False
    
    async def update_session_state(
        self, 
        phone_number: str, 
        new_state: ConversationState
    ) -> bool:
        """Update the state of an existing session."""
        session = await self.get_session(phone_number)
        
        if not session:
            logger.warning(f"No session found for {phone_number}")
            return False
        
        session.state = new_state
        return await self.save_session(session)
    
    async def get_active_sessions_count(self) -> int:
        """Get count of active sessions."""
        try:
            pattern = "whatsapp_session:*"
            keys = await self.redis_client.keys(pattern)
            return len(keys)
            
        except Exception as e:
            logger.error(f"Error counting active sessions: {e}")
            return 0
    
    async def cleanup_expired_sessions(self):
        """Clean up completed sessions older than TTL."""
        try:
            pattern = "whatsapp_session:*"
            keys = await self.redis_client.keys(pattern)
            
            cleaned = 0
            for key in keys:
                ttl = await self.redis_client.ttl(key)
                if ttl <= 0:
                    await self.redis_client.delete(key)
                    cleaned += 1
            
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired sessions")
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")


# Singleton instance
session_manager = SessionManager()