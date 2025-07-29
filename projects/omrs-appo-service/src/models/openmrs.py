from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class AppointmentRequest(BaseModel):
    """Appointment creation request model."""
    patient_id: str
    practitioner_id: Optional[str] = None
    location_id: Optional[str] = None
    appointment_type: str
    start_datetime: datetime
    end_datetime: datetime
    reason: str
    status: str = "proposed"
    priority: Optional[int] = None
    comment: Optional[str] = None


class TriageReport(BaseModel):
    """Triage report for OpenMRS."""
    patient_id: str
    encounter_datetime: datetime
    chief_complaint: str
    history_of_present_illness: str
    symptoms: List[str]
    severity_assessment: str
    recommended_actions: List[str]
    triage_category: str
    vital_signs: Optional[Dict[str, Any]] = None
    ai_assessment_summary: str
