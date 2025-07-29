from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ConversationState(str, Enum):
    """States of a conversation."""
    INITIAL = "initial"
    COLLECTING_SYMPTOMS = "collecting_symptoms"
    TRIAGE_ASSESSMENT = "triage_assessment"
    SCHEDULING_APPOINTMENT = "scheduling_appointment"
    CONFIRMING_DETAILS = "confirming_details"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PatientProfile(BaseModel):
    """Patient profile information."""
    phone_number: str
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    openmrs_patient_id: Optional[str] = None


class TriageData(BaseModel):
    """Triage assessment data."""
    chief_complaint: str
    symptoms: List[str]
    symptom_duration: Optional[str] = None
    severity_level: Optional[int] = Field(None, ge=1, le=5)
    medical_history: Optional[List[str]] = []
    current_medications: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    vital_signs: Optional[Dict[str, Any]] = {}


class AppointmentPreferences(BaseModel):
    """Patient appointment preferences."""
    preferred_dates: List[str] = []
    preferred_times: List[str] = []
    provider_preference: Optional[str] = None
    location_preference: Optional[str] = None
    appointment_type: Optional[str] = None
    urgency: Optional[str] = None


class ConversationSession(BaseModel):
    """Complete conversation session data."""
    session_id: str
    phone_number: str
    patient_profile: PatientProfile
    state: ConversationState
    triage_data: Optional[TriageData] = None
    appointment_preferences: Optional[AppointmentPreferences] = None
    conversation_history: List[Dict[str, Any]] = []
    ai_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to conversation history."""
        message = {
            "timestamp": datetime.utcnow().isoformat(),
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        self.conversation_history.append(message)
        self.updated_at = datetime.utcnow()
