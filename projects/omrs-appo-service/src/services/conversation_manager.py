"""Conversation manager for orchestrating the appointment and triage workflow."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import re
from src.models.domain import (
    ConversationSession,
    ConversationState,
    TriageData,
    AppointmentPreferences
)
from src.services.session_manager import session_manager
from src.clients.whatsapp_client import whatsapp_client
from src.clients.medgemma_client import medgemma_client
from src.clients.openmrs_client import openmrs_client
from src.services.report_generator import report_generator


class ConversationManager:
    """Manages conversation flow and state transitions."""
    
    def __init__(self):
        self.state_handlers = {
            ConversationState.INITIAL: self._handle_initial_state,
            ConversationState.COLLECTING_SYMPTOMS: self._handle_collecting_symptoms,
            ConversationState.TRIAGE_ASSESSMENT: self._handle_triage_assessment,
            ConversationState.SCHEDULING_APPOINTMENT: self._handle_scheduling_appointment,
            ConversationState.CONFIRMING_DETAILS: self._handle_confirming_details,
            ConversationState.COMPLETED: self._handle_completed_state,
            ConversationState.CANCELLED: self._handle_cancelled_state
        }
    
    async def process_message(
        self, 
        session: ConversationSession, 
        user_message: str
    ) -> None:
        """Process incoming message and manage conversation flow."""
        try:
            # Check for cancel/restart commands
            if self._is_cancel_command(user_message):
                await self._handle_cancellation(session)
                return
            
            # Get handler for current state
            handler = self.state_handlers.get(session.state)
            
            if handler:
                await handler(session, user_message)
            else:
                logger.error(f"No handler for state: {session.state}")
                await self._send_error_message(session)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._send_error_message(session)
    
    async def _handle_initial_state(
        self, 
        session: ConversationSession, 
        user_message: str
    ) -> None:
        """Handle initial conversation state."""
        # Welcome message
        welcome_text = (
            "Hello! I'm MedGemma, an AI assistant here to help you schedule a medical appointment. "
            "I'll ask you some questions to understand your health concerns and find the best appointment for you.\n\n"
            "Please note: I'm an AI assistant, not a doctor. For emergencies, please call emergency services immediately.\n\n"
            "To get started, could you please tell me your name?"
        )
        
        await whatsapp_client.send_text_message(
            session.phone_number,
            welcome_text
        )
        
        # Update session state
        session.state = ConversationState.COLLECTING_SYMPTOMS
        session.add_message("assistant", welcome_text)
        await session_manager.save_session(session)
    
    async def _handle_collecting_symptoms(
        self, 
        session: ConversationSession, 
        user_message: str
    ) -> None:
        """Collect patient information and symptoms."""
        # If we don't have patient name yet
        if not session.patient_profile.name:
            session.patient_profile.name = user_message.strip()
            response = f"Thank you, {session.patient_profile.name}. What brings you in today? Please describe your main health concern."
            
            await whatsapp_client.send_text_message(
                session.phone_number,
                response
            )
            
            session.add_message("assistant", response)
            await session_manager.save_session(session)
            return
        
        # Use MedGemma to process symptom information
        ai_response = await medgemma_client.generate_response(session, user_message)
        response_text = ai_response["response"]
        
        # Send AI response
        await whatsapp_client.send_text_message(
            session.phone_number,
            response_text
        )
        
        session.add_message("assistant", response_text)
        
        # Check if we have enough information for triage
        if self._has_sufficient_symptoms_info(session):
            session.state = ConversationState.TRIAGE_ASSESSMENT
            
            # Add transition message
            transition_msg = "Thank you for providing that information. Let me assess your symptoms to determine the urgency and type of appointment you need."
            
            await whatsapp_client.send_text_message(
                session.phone_number,
                transition_msg
            )
            
            session.add_message("assistant", transition_msg)
            
            # Trigger triage assessment
            await self._perform_triage_assessment(session)
        
        await session_manager.save_session(session)
    
    async def _handle_triage_assessment(
        self, 
        session: ConversationSession, 
        user_message: str
    ) -> None:
        """Handle triage assessment state."""
        # This state is typically automated, but handle any user input
        await self._perform_triage_assessment(session)
    
    async def _perform_triage_assessment(
        self, 
        session: ConversationSession
    ) -> None:
        """Perform triage assessment using MedGemma."""
        # Analyze conversation for triage data
        triage_data = await medgemma_client.analyze_triage_data(session)
        
        if triage_data:
            session.triage_data = triage_data
            
            # Check urgency level
            if triage_data.severity_level >= 4:
                urgent_msg = (
                    "Based on your symptoms, this appears to be urgent. "
                    "I recommend seeking immediate medical attention. "
                    "Would you like me to help you schedule an urgent appointment?"
                )
                
                await whatsapp_client.send_interactive_buttons(
                    session.phone_number,
                    urgent_msg,
                    [
                        {"id": "urgent_yes", "title": "Yes, urgent appt"},
                        {"id": "urgent_no", "title": "No, regular appt"},
                        {"id": "cancel", "title": "Cancel"}
                    ]
                )
                
                session.add_message("assistant", urgent_msg)
            else:
                # Move to scheduling
                session.state = ConversationState.SCHEDULING_APPOINTMENT
                await self._initiate_appointment_scheduling(session)
        else:
            # Need more information
            followup_msg = "I need a bit more information to properly assess your needs. Could you tell me more about your symptoms?"
            
            await whatsapp_client.send_text_message(
                session.phone_number,
                followup_msg
            )
            
            session.add_message("assistant", followup_msg)
            session.state = ConversationState.COLLECTING_SYMPTOMS
        
        await session_manager.save_session(session)
    
    async def _handle_scheduling_appointment(
        self, 
        session: ConversationSession, 
        user_message: str
    ) -> None:
        """Handle appointment scheduling."""
        if not session.appointment_preferences:
            session.appointment_preferences = AppointmentPreferences()
        
        # Parse user response for scheduling preferences
        self._parse_scheduling_preferences(user_message, session)
        
        # Check if we have enough preferences
        if self._has_sufficient_preferences(session):
            # Show available slots
            await self._show_available_appointments(session)
        else:
            # Ask for missing preferences
            await self._ask_for_preferences(session)
    
    async def _initiate_appointment_scheduling(
        self, 
        session: ConversationSession
    ) -> None:
        """Start the appointment scheduling process."""
        scheduling_msg = (
            "Now let's schedule your appointment. "
            "When would you prefer to come in? "
            "Please let me know your preferred days and times."
        )
        
        # Provide date options
        date_options = self._generate_date_options()
        
        await whatsapp_client.send_list_message(
            session.phone_number,
            scheduling_msg,
            "Select dates",
            [
                {
                    "title": "Available Dates",
                    "rows": [
                        {
                            "id": f"date_{i}",
                            "title": date["display"],
                            "description": date["description"]
                        }
                        for i, date in enumerate(date_options[:10])
                    ]
                }
            ]
        )
        
        session.add_message("assistant", scheduling_msg)
        await session_manager.save_session(session)
    
    async def _handle_confirming_details(
        self, 
        session: ConversationSession, 
        user_message: str
    ) -> None:
        """Handle appointment confirmation."""
        user_response = user_message.lower().strip()
        
        if user_response in ["yes", "confirm", "correct", "ok"]:
            # Create appointment in OpenMRS
            await self._finalize_appointment(session)
        elif user_response in ["no", "change", "modify"]:
            # Go back to scheduling
            session.state = ConversationState.SCHEDULING_APPOINTMENT
            
            change_msg = "What would you like to change about the appointment?"
            await whatsapp_client.send_text_message(
                session.phone_number,
                change_msg
            )
            
            session.add_message("assistant", change_msg)
            await session_manager.save_session(session)
        else:
            # Ask for confirmation again
            confirm_msg = "Please respond with 'Yes' to confirm or 'No' to make changes."
            
            await whatsapp_client.send_interactive_buttons(
                session.phone_number,
                confirm_msg,
                [
                    {"id": "confirm_yes", "title": "Yes, confirm"},
                    {"id": "confirm_no", "title": "No, change"}
                ]
            )
            
            session.add_message("assistant", confirm_msg)
            await session_manager.save_session(session)
    
    async def _finalize_appointment(self, session: ConversationSession) -> None:
        """Finalize appointment creation in OpenMRS."""
        try:
            # Generate summary
            summary = await medgemma_client.generate_summary(session)
            session.ai_summary = summary
            
            # Create patient if needed
            if not session.patient_profile.openmrs_patient_id:
                patient_id = await openmrs_client.create_or_get_patient(
                    session.patient_profile
                )
                session.patient_profile.openmrs_patient_id = patient_id
            
            # Create appointment
            appointment = await openmrs_client.create_appointment(
                session.patient_profile.openmrs_patient_id,
                session.appointment_preferences,
                session.triage_data
            )
            
            # Create triage report
            report = await report_generator.generate_triage_report(session)
            await openmrs_client.create_encounter(report)
            
            # Send confirmation
            confirmation_msg = (
                f"✅ Your appointment has been confirmed!\n\n"
                f"📅 Date: {appointment['date']}\n"
                f"🕐 Time: {appointment['time']}\n"
                f"👨‍⚕️ Provider: {appointment['provider']}\n"
                f"📍 Location: {appointment['location']}\n\n"
                f"Please arrive 15 minutes early for check-in. "
                f"If you need to cancel or reschedule, please call us.\n\n"
                f"Thank you for using our scheduling service!"
            )
            
            await whatsapp_client.send_text_message(
                session.phone_number,
                confirmation_msg
            )
            
            session.add_message("assistant", confirmation_msg)
            session.state = ConversationState.COMPLETED
            session.completed_at = datetime.utcnow()
            
            await session_manager.save_session(session)
            
        except Exception as e:
            logger.error(f"Error finalizing appointment: {e}")
            
            error_msg = (
                "I encountered an error while creating your appointment. "
                "Please call our office directly to complete the scheduling. "
                "We apologize for the inconvenience."
            )
            
            await whatsapp_client.send_text_message(
                session.phone_number,
                error_msg
            )
            
            session.add_message("assistant", error_msg)
            session.state = ConversationState.COMPLETED
            await session_manager.save_session(session)
    
    async def _handle_completed_state(
        self, 
        session: ConversationSession, 
        user_message: str
    ) -> None:
        """Handle messages after conversation is completed."""
        followup_msg = (
            "Your appointment has already been scheduled. "
            "If you need to make changes or have questions, please call our office. "
            "For a new appointment, please start a new conversation."
        )
        
        await whatsapp_client.send_text_message(
            session.phone_number,
            followup_msg
        )
    
    async def _handle_cancelled_state(
        self, 
        session: ConversationSession, 
        user_message: str
    ) -> None:
        """Handle cancelled conversation."""
        restart_msg = "This conversation was cancelled. Please send 'Hi' to start a new appointment request."
        
        await whatsapp_client.send_text_message(
            session.phone_number,
            restart_msg
        )
    
    async def _handle_cancellation(self, session: ConversationSession) -> None:
        """Handle conversation cancellation."""
        cancel_msg = (
            "Your appointment request has been cancelled. "
            "If you'd like to start over, just send 'Hi' again. "
            "Take care!"
        )
        
        await whatsapp_client.send_text_message(
            session.phone_number,
            cancel_msg
        )
        
        session.add_message("assistant", cancel_msg)
        session.state = ConversationState.CANCELLED
        await session_manager.save_session(session)
    
    async def _send_error_message(self, session: ConversationSession) -> None:
        """Send error message to user."""
        error_msg = (
            "I'm sorry, I encountered an error processing your request. "
            "Please try again or call our office for assistance."
        )
        
        await whatsapp_client.send_text_message(
            session.phone_number,
            error_msg
        )
    
    def _is_cancel_command(self, message: str) -> bool:
        """Check if message is a cancel command."""
        cancel_words = ["cancel", "stop", "quit", "exit", "end"]
        return message.lower().strip() in cancel_words
    
    def _has_sufficient_symptoms_info(self, session: ConversationSession) -> bool:
        """Check if we have enough symptom information."""
        # Check conversation length and content
        message_count = len(session.conversation_history)
        
        # Need at least name + 2 symptom exchanges
        if message_count < 4:
            return False
        
        # Check for symptom keywords in recent messages
        recent_messages = session.conversation_history[-4:]
        symptom_keywords = [
            "pain", "ache", "fever", "cough", "symptom",
            "feel", "hurt", "sick", "issue", "problem"
        ]
        
        has_symptoms = any(
            any(keyword in msg["content"].lower() for keyword in symptom_keywords)
            for msg in recent_messages
            if msg["role"] == "user"
        )
        
        return has_symptoms
    
    def _has_sufficient_preferences(self, session: ConversationSession) -> bool:
        """Check if we have enough scheduling preferences."""
        prefs = session.appointment_preferences
        return bool(prefs and (prefs.preferred_dates or prefs.preferred_times))
    
    def _parse_scheduling_preferences(
        self, 
        message: str, 
        session: ConversationSession
    ) -> None:
        """Parse scheduling preferences from user message."""
        prefs = session.appointment_preferences
        
        # Parse dates (simple pattern matching)
        date_patterns = [
            r"tomorrow",
            r"next week",
            r"monday|tuesday|wednesday|thursday|friday|saturday|sunday",
            r"\d{1,2}/\d{1,2}",
            r"\d{1,2}-\d{1,2}"
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, message.lower())
            if matches:
                prefs.preferred_dates.extend(matches)
        
        # Parse times
        time_patterns = [
            r"\d{1,2}:\d{2}\s*(?:am|pm)",
            r"\d{1,2}\s*(?:am|pm)",
            r"morning|afternoon|evening"
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, message.lower())
            if matches:
                prefs.preferred_times.extend(matches)
        
        # Parse urgency
        if any(word in message.lower() for word in ["urgent", "asap", "emergency"]):
            prefs.urgency = "urgent"
    
    def _generate_date_options(self) -> List[Dict[str, str]]:
        """Generate available date options."""
        options = []
        today = datetime.now()
        
        for i in range(14):  # Next 2 weeks
            date = today + timedelta(days=i)
            
            # Skip weekends for this example
            if date.weekday() >= 5:
                continue
            
            options.append({
                "display": date.strftime("%a, %b %d"),
                "description": date.strftime("%Y-%m-%d"),
                "value": date.isoformat()
            })
        
        return options
    
    async def _show_available_appointments(self, session: ConversationSession) -> None:
        """Show available appointment slots."""
        # This would integrate with OpenMRS to get real availability
        # For now, show mock slots
        
        slots_msg = (
            "Here are some available appointment times based on your preferences:\n\n"
            "1️⃣ Tomorrow at 10:00 AM\n"
            "2️⃣ Tomorrow at 2:00 PM\n"
            "3️⃣ Thursday at 11:00 AM\n"
            "4️⃣ Friday at 3:00 PM\n\n"
            "Please select a time that works for you."
        )
        
        await whatsapp_client.send_interactive_buttons(
            session.phone_number,
            slots_msg,
            [
                {"id": "slot_1", "title": "Tomorrow 10AM"},
                {"id": "slot_2", "title": "Tomorrow 2PM"},
                {"id": "slot_3", "title": "Thursday 11AM"}
            ]
        )
        
        session.add_message("assistant", slots_msg)
        session.state = ConversationState.CONFIRMING_DETAILS
        await session_manager.save_session(session)
    
    async def _ask_for_preferences(self, session: ConversationSession) -> None:
        """Ask for missing scheduling preferences."""
        prefs = session.appointment_preferences
        
        if not prefs.preferred_dates:
            msg = "What days work best for you? (e.g., tomorrow, next Monday, etc.)"
        elif not prefs.preferred_times:
            msg = "What time of day works best? (e.g., morning, 2:00 PM, etc.)"
        else:
            msg = "Do you have any other preferences for your appointment?"
        
        await whatsapp_client.send_text_message(
            session.phone_number,
            msg
        )
        
        session.add_message("assistant", msg)
        await session_manager.save_session(session)


# Singleton instance
conversation_manager = ConversationManager()