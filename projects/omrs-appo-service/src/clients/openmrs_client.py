"""OpenMRS FHIR client for interacting with OpenMRS."""
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger
import base64
from fhir.resources.patient import Patient
from fhir.resources.appointment import Appointment
from fhir.resources.encounter import Encounter
from fhir.resources.observation import Observation
from fhir.resources.practitioner import Practitioner
from fhir.resources.location import Location
from fhir.resources.humanname import HumanName
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.identifier import Identifier
from fhir.resources.reference import Reference
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.period import Period
from fhir.resources.narrative import Narrative
from src.core.config import get_settings
from src.models.domain import PatientProfile, AppointmentPreferences, TriageData
from src.models.openmrs import TriageReport


class OpenMRSClient:
    """Client for OpenMRS FHIR API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.openmrs_base_url
        
        # Create basic auth header
        credentials = f"{self.settings.openmrs_username}:{self.settings.openmrs_password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json"
        }
    
    async def create_or_get_patient(
        self, 
        patient_profile: PatientProfile
    ) -> str:
        """Create a new patient or get existing one by phone number."""
        try:
            # First, search for existing patient by phone
            existing_patient = await self._search_patient_by_phone(
                patient_profile.phone_number
            )
            
            if existing_patient:
                logger.info(f"Found existing patient: {existing_patient}")
                return existing_patient
            
            # Create new patient
            patient = self._build_patient_resource(patient_profile)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/Patient",
                    headers=self.headers,
                    json=patient.dict(exclude_unset=True)
                )
                response.raise_for_status()
                
                result = response.json()
                patient_id = result.get("id")
                
                logger.info(f"Created new patient: {patient_id}")
                return patient_id
                
        except Exception as e:
            logger.error(f"Error creating/getting patient: {e}")
            raise
    
    async def create_appointment(
        self,
        patient_id: str,
        preferences: AppointmentPreferences,
        triage_data: Optional[TriageData] = None
    ) -> Dict[str, Any]:
        """Create an appointment in OpenMRS."""
        try:
            # For this example, we'll use mock data
            # In production, you'd integrate with real scheduling system
            
            start_time = datetime.now() + timedelta(days=2)
            end_time = start_time + timedelta(minutes=30)
            
            appointment = Appointment(
                status="proposed",
                serviceCategory=[CodeableConcept(
                    coding=[Coding(
                        system="http://terminology.hl7.org/CodeSystem/service-category",
                        code="17",
                        display="General Practice"
                    )]
                )],
                serviceType=[CodeableConcept(
                    text="General Consultation"
                )],
                appointmentType=CodeableConcept(
                    coding=[Coding(
                        system="http://terminology.hl7.org/CodeSystem/v2-0276",
                        code="ROUTINE",
                        display="Routine appointment"
                    )]
                ),
                reasonCode=[CodeableConcept(
                    text=triage_data.chief_complaint if triage_data else "General consultation"
                )],
                priority=triage_data.severity_level if triage_data else 3,
                description=f"Appointment scheduled via WhatsApp. Urgency: {preferences.urgency or 'routine'}",
                start=start_time.isoformat(),
                end=end_time.isoformat(),
                participant=[
                    {
                        "actor": Reference(reference=f"Patient/{patient_id}"),
                        "required": "required",
                        "status": "accepted"
                    }
                ]
            )
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/Appointment",
                    headers=self.headers,
                    json=appointment.dict(exclude_unset=True)
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Return formatted appointment details
                return {
                    "id": result.get("id"),
                    "date": start_time.strftime("%B %d, %Y"),
                    "time": start_time.strftime("%I:%M %p"),
                    "provider": "Dr. Smith",  # Mock provider
                    "location": "Main Clinic"  # Mock location
                }
                
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            raise
    
    async def create_encounter(
        self, 
        triage_report: TriageReport
    ) -> str:
        """Create a triage encounter in OpenMRS."""
        try:
            # Create encounter resource
            encounter = Encounter(
                status="finished",
                class_fhir=Coding(
                    system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    code="AMB",
                    display="ambulatory"
                ),
                type=[CodeableConcept(
                    coding=[Coding(
                        system="http://snomed.info/sct",
                        code="225390008",
                        display="Triage"
                    )]
                )],
                subject=Reference(reference=f"Patient/{triage_report.patient_id}"),
                period=Period(
                    start=triage_report.encounter_datetime.isoformat(),
                    end=triage_report.encounter_datetime.isoformat()
                ),
                reasonCode=[CodeableConcept(
                    text=triage_report.chief_complaint
                )]
            )
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/Encounter",
                    headers=self.headers,
                    json=encounter.dict(exclude_unset=True)
                )
                response.raise_for_status()
                
                result = response.json()
                encounter_id = result.get("id")
                
                # Create observations for the encounter
                await self._create_triage_observations(
                    encounter_id,
                    triage_report
                )
                
                logger.info(f"Created triage encounter: {encounter_id}")
                return encounter_id
                
        except Exception as e:
            logger.error(f"Error creating encounter: {e}")
            raise
    
    async def get_practitioners(self) -> List[Dict[str, Any]]:
        """Get list of available practitioners."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/Practitioner",
                    headers=self.headers,
                    params={"_count": 20}
                )
                response.raise_for_status()
                
                result = response.json()
                practitioners = []
                
                for entry in result.get("entry", []):
                    resource = entry.get("resource", {})
                    name = resource.get("name", [{}])[0]
                    
                    practitioners.append({
                        "id": resource.get("id"),
                        "name": f"{name.get('given', [''])[0]} {name.get('family', '')}",
                        "specialty": resource.get("qualification", [{}])[0].get("code", {}).get("text", "General Practice")
                    })
                
                return practitioners
                
        except Exception as e:
            logger.error(f"Error getting practitioners: {e}")
            return []
    
    async def get_locations(self) -> List[Dict[str, Any]]:
        """Get list of available locations."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/Location",
                    headers=self.headers,
                    params={"_count": 20}
                )
                response.raise_for_status()
                
                result = response.json()
                locations = []
                
                for entry in result.get("entry", []):
                    resource = entry.get("resource", {})
                    
                    locations.append({
                        "id": resource.get("id"),
                        "name": resource.get("name", "Unknown Location"),
                        "address": resource.get("address", {}).get("text", "")
                    })
                
                return locations
                
        except Exception as e:
            logger.error(f"Error getting locations: {e}")
            return []
    
    async def _search_patient_by_phone(self, phone_number: str) -> Optional[str]:
        """Search for patient by phone number."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/Patient",
                    headers=self.headers,
                    params={
                        "telecom": phone_number,
                        "_count": 1
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("total", 0) > 0:
                    entry = result.get("entry", [])[0]
                    return entry.get("resource", {}).get("id")
                
                return None
                
        except Exception as e:
            logger.error(f"Error searching patient: {e}")
            return None
    
    def _build_patient_resource(self, profile: PatientProfile) -> Patient:
        """Build FHIR Patient resource from profile."""
        # Create patient resource
        patient = Patient(
            active=True,
            name=[HumanName(
                use="official",
                text=profile.name or "Unknown Patient",
                given=[profile.name.split()[0]] if profile.name else ["Unknown"],
                family=profile.name.split()[-1] if profile.name and len(profile.name.split()) > 1 else "Patient"
            )],
            telecom=[ContactPoint(
                system="phone",
                value=profile.phone_number,
                use="mobile",
                rank=1
            )]
        )
        
        # Add gender if available
        if profile.gender:
            patient.gender = profile.gender.lower()
        
        # Add birth date if available
        if profile.date_of_birth:
            patient.birthDate = profile.date_of_birth
        
        # Add email if available
        if profile.email:
            patient.telecom.append(ContactPoint(
                system="email",
                value=profile.email,
                use="home"
            ))
        
        # Add address if available
        if profile.address:
            patient.address = [{
                "use": "home",
                "text": profile.address
            }]
        
        return patient
    
    async def _create_triage_observations(
        self,
        encounter_id: str,
        triage_report: TriageReport
    ) -> None:
        """Create observations for triage data."""
        try:
            # Create chief complaint observation
            chief_complaint_obs = Observation(
                status="final",
                code=CodeableConcept(
                    coding=[Coding(
                        system="http://loinc.org",
                        code="10154-3",
                        display="Chief complaint"
                    )]
                ),
                subject=Reference(reference=f"Patient/{triage_report.patient_id}"),
                encounter=Reference(reference=f"Encounter/{encounter_id}"),
                effectiveDateTime=triage_report.encounter_datetime.isoformat(),
                valueString=triage_report.chief_complaint
            )
            
            # Create triage category observation
            triage_category_obs = Observation(
                status="final",
                code=CodeableConcept(
                    coding=[Coding(
                        system="http://loinc.org",
                        code="85352-1",
                        display="Triage category"
                    )]
                ),
                subject=Reference(reference=f"Patient/{triage_report.patient_id}"),
                encounter=Reference(reference=f"Encounter/{encounter_id}"),
                effectiveDateTime=triage_report.encounter_datetime.isoformat(),
                valueCodeableConcept=CodeableConcept(
                    text=triage_report.triage_category
                )
            )
            
            # Create observations
            async with httpx.AsyncClient() as client:
                for obs in [chief_complaint_obs, triage_category_obs]:
                    response = await client.post(
                        f"{self.base_url}/Observation",
                        headers=self.headers,
                        json=obs.dict(exclude_unset=True)
                    )
                    response.raise_for_status()
            
            logger.info(f"Created triage observations for encounter {encounter_id}")
            
        except Exception as e:
            logger.error(f"Error creating observations: {e}")


# Singleton instance
openmrs_client = OpenMRSClient()