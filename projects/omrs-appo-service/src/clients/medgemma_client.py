"""MedGemma AI client for medical conversations."""
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from src.core.config import get_settings
from src.models.domain import ConversationSession, TriageData


class MedGemmaClient:
    """Client for Google MedGemma medical AI model."""
    
    def __init__(self):
        self.settings = get_settings()
        genai.configure(api_key=self.settings.google_api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=self.settings.medgemma_model,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            },
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        )
        
        # System prompt for medical triage
        self.system_prompt = """You are MedGemma, a medical AI assistant helping with appointment scheduling and triage. 
Your role is to:
1. Gather information about the patient's symptoms and concerns
2. Ask relevant follow-up questions for triage
3. Assess urgency level (1-5, where 5 is most urgent)
4. Help schedule appointments based on the assessment
5. Be empathetic and professional

Important guidelines:
- Always clarify that you're an AI assistant, not a doctor
- Don't provide diagnoses or treatment recommendations
- Focus on information gathering for triage purposes
- If symptoms suggest emergency care is needed, advise seeking immediate medical attention
- Keep responses concise and clear for WhatsApp format
- Use simple language accessible to all patients

Current conversation state: {state}
Patient info: {patient_info}"""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_response(
        self,
        session: ConversationSession,
        user_message: str
    ) -> Dict[str, Any]:
        """Generate AI response based on conversation context."""
        try:
            # Build conversation history for context
            messages = self._build_message_history(session)
            
            # Add system prompt with current context
            system_context = self.system_prompt.format(
                state=session.state.value,
                patient_info=self._format_patient_info(session)
            )
            
            # Create chat session
            chat = self.model.start_chat(history=[])
            
            # Generate response
            response = await chat.send_message_async(
                f"{system_context}\n\nConversation history:\n{messages}\n\nUser: {user_message}\n\nAssistant:"
            )
            
            # Parse response
            response_text = response.text.strip()
            
            # Extract any structured data from response
            structured_data = self._extract_structured_data(response_text, session)
            
            logger.debug(f"Generated response for session {session.session_id}")
            
            return {
                "response": response_text,
                "structured_data": structured_data,
                "usage": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating MedGemma response: {e}")
            raise
    
    async def analyze_triage_data(
        self,
        session: ConversationSession
    ) -> Optional[TriageData]:
        """Analyze conversation to extract triage data."""
        try:
            # Build conversation summary
            messages = self._build_message_history(session)
            
            prompt = f"""Based on the following medical conversation, extract and structure the triage information:

{messages}

Please provide:
1. Chief complaint (main reason for visit)
2. List of symptoms
3. Duration of symptoms
4. Severity level (1-5, where 5 is most severe)
5. Relevant medical history mentioned
6. Current medications mentioned
7. Allergies mentioned

Format your response as JSON."""

            chat = self.model.start_chat(history=[])
            response = await chat.send_message_async(prompt)
            
            # Parse the response and create TriageData
            # This is a simplified version - you'd want more robust parsing
            triage_info = self._parse_triage_response(response.text)
            
            return triage_info
            
        except Exception as e:
            logger.error(f"Error analyzing triage data: {e}")
            return None
    
    async def generate_summary(
        self,
        session: ConversationSession
    ) -> str:
        """Generate a summary of the conversation for medical records."""
        try:
            messages = self._build_message_history(session)
            
            prompt = f"""Please provide a concise medical summary of this patient conversation for the healthcare provider:

{messages}

Include:
1. Chief complaint
2. History of present illness
3. Key symptoms and their duration
4. Patient's main concerns
5. Urgency assessment
6. Recommended follow-up actions

Keep it professional and suitable for medical records."""

            chat = self.model.start_chat(history=[])
            response = await chat.send_message_async(prompt)
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Error generating summary"
    
    def _build_message_history(self, session: ConversationSession) -> str:
        """Build formatted message history from session."""
        messages = []
        
        for msg in session.conversation_history[-10:]:  # Last 10 messages for context
            role = msg["role"].capitalize()
            content = msg["content"]
            messages.append(f"{role}: {content}")
        
        return "\n".join(messages)
    
    def _format_patient_info(self, session: ConversationSession) -> str:
        """Format patient information for context."""
        profile = session.patient_profile
        info_parts = []
        
        if profile.name:
            info_parts.append(f"Name: {profile.name}")
        if profile.date_of_birth:
            info_parts.append(f"DOB: {profile.date_of_birth}")
        if profile.gender:
            info_parts.append(f"Gender: {profile.gender}")
        
        return ", ".join(info_parts) if info_parts else "No patient info available"
    
    def _extract_structured_data(
        self, 
        response: str, 
        session: ConversationSession
    ) -> Dict[str, Any]:
        """Extract structured data from AI response."""
        structured_data = {}
        
        # Look for urgency indicators
        if any(word in response.lower() for word in ["urgent", "emergency", "immediate"]):
            structured_data["urgency_detected"] = True
        
        # Look for appointment scheduling intent
        if any(word in response.lower() for word in ["schedule", "appointment", "book"]):
            structured_data["scheduling_intent"] = True
        
        # Add more extraction logic as needed
        
        return structured_data
    
    def _parse_triage_response(self, response_text: str) -> Optional[TriageData]:
        """Parse triage information from AI response."""
        try:
            # This is a simplified parser - in production, you'd want more robust JSON parsing
            # For now, we'll create a basic TriageData object
            
            # Extract basic information using simple parsing
            lines = response_text.strip().split('\n')
            
            chief_complaint = ""
            symptoms = []
            severity_level = 3  # Default medium severity
            
            for line in lines:
                lower_line = line.lower()
                if "chief complaint" in lower_line or "main reason" in lower_line:
                    chief_complaint = line.split(":", 1)[-1].strip()
                elif "symptoms" in lower_line:
                    symptoms_text = line.split(":", 1)[-1].strip()
                    symptoms = [s.strip() for s in symptoms_text.split(",")]
                elif "severity" in lower_line:
                    try:
                        severity_level = int(''.join(filter(str.isdigit, line)))
                    except:
                        pass
            
            if chief_complaint and symptoms:
                return TriageData(
                    chief_complaint=chief_complaint,
                    symptoms=symptoms,
                    severity_level=severity_level
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing triage response: {e}")
            return None


# Singleton instance
medgemma_client = MedGemmaClient()