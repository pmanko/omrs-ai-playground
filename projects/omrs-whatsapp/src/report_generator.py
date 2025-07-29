"""Report generator for creating triage reports from conversation data."""
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger
from .models import ConversationSession, TriageReport


class ReportGenerator:
    """Generates medical reports from conversation sessions."""
    
    async def generate_triage_report(
        self, 
        session: ConversationSession
    ) -> TriageReport:
        """Generate a triage report from conversation session."""
        try:
            # Extract triage data
            triage_data = session.triage_data
            
            if not triage_data:
                raise ValueError("No triage data available in session")
            
            # Build history of present illness from conversation
            hpi = self._build_history_of_present_illness(session)
            
            # Determine triage category
            triage_category = self._determine_triage_category(
                triage_data.severity_level
            )
            
            # Generate recommended actions
            recommended_actions = self._generate_recommended_actions(
                triage_data,
                triage_category
            )
            
            # Create triage report
            report = TriageReport(
                patient_id=session.patient_profile.openmrs_patient_id,
                encounter_datetime=datetime.utcnow(),
                chief_complaint=triage_data.chief_complaint,
                history_of_present_illness=hpi,
                symptoms=triage_data.symptoms,
                severity_assessment=self._format_severity_assessment(
                    triage_data.severity_level
                ),
                recommended_actions=recommended_actions,
                triage_category=triage_category,
                vital_signs=triage_data.vital_signs,
                ai_assessment_summary=session.ai_summary or self._generate_default_summary(session)
            )
            
            logger.info(f"Generated triage report for session {session.session_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating triage report: {e}")
            raise
    
    def _build_history_of_present_illness(
        self, 
        session: ConversationSession
    ) -> str:
        """Build HPI from conversation history."""
        hpi_parts = []
        
        # Extract relevant information from conversation
        for msg in session.conversation_history:
            if msg["role"] == "user":
                content = msg["content"].lower()
                
                # Look for temporal information
                if any(word in content for word in ["started", "began", "since", "days", "weeks", "hours"]):
                    hpi_parts.append(msg["content"])
                
                # Look for symptom descriptions
                elif any(word in content for word in ["pain", "ache", "fever", "cough", "feeling", "symptoms"]):
                    hpi_parts.append(msg["content"])
                
                # Look for aggravating/alleviating factors
                elif any(word in content for word in ["worse", "better", "helps", "relieved"]):
                    hpi_parts.append(msg["content"])
        
        # Combine parts into coherent HPI
        if hpi_parts:
            hpi = "Patient reports: " + " ".join(hpi_parts[:5])  # Limit to 5 most relevant
        else:
            hpi = f"Patient presents with {session.triage_data.chief_complaint if session.triage_data else 'unspecified complaint'}."
        
        # Add duration if available
        if session.triage_data and session.triage_data.symptom_duration:
            hpi += f" Symptoms have been present for {session.triage_data.symptom_duration}."
        
        return hpi
    
    def _determine_triage_category(self, severity_level: int) -> str:
        """Determine triage category based on severity level."""
        categories = {
            1: "Non-urgent (Green)",
            2: "Less urgent (Yellow)",
            3: "Urgent (Orange)",
            4: "Very urgent (Red)",
            5: "Immediate/Resuscitation (Red)"
        }
        
        return categories.get(severity_level, "Urgent (Orange)")
    
    def _generate_recommended_actions(
        self,
        triage_data,
        triage_category: str
    ) -> List[str]:
        """Generate recommended actions based on triage assessment."""
        actions = []
        
        # Based on severity
        if triage_data.severity_level >= 4:
            actions.extend([
                "Immediate medical evaluation required",
                "Consider emergency department referral",
                "Monitor vital signs closely"
            ])
        elif triage_data.severity_level == 3:
            actions.extend([
                "Schedule appointment within 24-48 hours",
                "Provide symptom management advice",
                "Instruct patient on warning signs"
            ])
        else:
            actions.extend([
                "Schedule routine appointment",
                "Provide self-care instructions",
                "Follow up if symptoms worsen"
            ])
        
        # Based on specific symptoms
        if "fever" in [s.lower() for s in triage_data.symptoms]:
            actions.append("Check temperature and monitor for changes")
        
        if "chest pain" in [s.lower() for s in triage_data.symptoms]:
            actions.append("Perform ECG if indicated")
            actions.append("Rule out cardiac causes")
        
        if "breathing" in [s.lower() for s in triage_data.symptoms] or "shortness" in [s.lower() for s in triage_data.symptoms]:
            actions.append("Check oxygen saturation")
            actions.append("Assess respiratory rate and effort")
        
        return actions
    
    def _format_severity_assessment(self, severity_level: int) -> str:
        """Format severity assessment description."""
        assessments = {
            1: "Minimal severity - symptoms are mild and not significantly impacting daily activities",
            2: "Mild severity - symptoms are noticeable but manageable with self-care",
            3: "Moderate severity - symptoms are affecting daily activities and require medical attention",
            4: "High severity - symptoms are significant and require urgent medical evaluation",
            5: "Critical severity - symptoms indicate potential emergency requiring immediate intervention"
        }
        
        return assessments.get(
            severity_level,
            "Moderate severity - requires medical evaluation"
        )
    
    def _generate_default_summary(self, session: ConversationSession) -> str:
        """Generate a default summary if AI summary is not available."""
        if not session.triage_data:
            return "Patient engaged in triage conversation via WhatsApp."
        
        summary_parts = [
            f"Patient presented with {session.triage_data.chief_complaint}.",
            f"Reported symptoms include: {', '.join(session.triage_data.symptoms)}.",
            f"Severity assessed as level {session.triage_data.severity_level}/5.",
        ]
        
        if session.triage_data.medical_history:
            summary_parts.append(
                f"Relevant medical history: {', '.join(session.triage_data.medical_history)}."
            )
        
        if session.triage_data.current_medications:
            summary_parts.append(
                f"Current medications: {', '.join(session.triage_data.current_medications)}."
            )
        
        if session.appointment_preferences:
            summary_parts.append(
                "Patient expressed appointment preferences and scheduling was initiated."
            )
        
        return " ".join(summary_parts)
    
    def generate_appointment_notes(
        self,
        session: ConversationSession
    ) -> str:
        """Generate appointment notes for the scheduled visit."""
        notes_parts = [
            f"Appointment scheduled via WhatsApp triage system on {datetime.utcnow().strftime('%Y-%m-%d')}.",
            f"\nChief Complaint: {session.triage_data.chief_complaint if session.triage_data else 'See triage report'}",
            f"\nTriage Category: {self._determine_triage_category(session.triage_data.severity_level if session.triage_data else 3)}",
        ]
        
        if session.triage_data and session.triage_data.symptoms:
            notes_parts.append(f"\nPresenting Symptoms:\n- " + "\n- ".join(session.triage_data.symptoms))
        
        if session.ai_summary:
            notes_parts.append(f"\n\nAI Assessment Summary:\n{session.ai_summary}")
        
        notes_parts.append("\n\nPlease review full triage report in patient record.")
        
        return "".join(notes_parts)


# Singleton instance
report_generator = ReportGenerator()