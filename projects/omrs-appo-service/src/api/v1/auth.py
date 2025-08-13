"""Authentication endpoints for patient verification."""
from fastapi import APIRouter, HTTPException
from loguru import logger
from src.models.domain import AuthenticationRequest, AuthenticationResult
from src.clients.openmrs_client import openmrs_client


router = APIRouter(tags=["authentication"])


@router.post("/verify-patient", response_model=AuthenticationResult)
async def verify_patient(request: AuthenticationRequest) -> AuthenticationResult:
    """Verify patient exists in OpenMRS and return welcome message."""
    try:
        logger.info(f"Verifying patient with OpenMRS ID: {request.openmrsId}")
        
        # Use the OpenMRS client to search for the patient
        patient_resource = await openmrs_client.get_patient_by_id(request.openmrsId)
        
        if patient_resource:
            # Extract patient name from the FHIR resource
            patient_name = extract_patient_name(patient_resource)
            
            welcome_message = (
                f"Welcome {patient_name}! We found your account. "
                "Please describe your main concern or what you'd like to schedule an appointment for."
            )
            
            logger.info(f"Patient verification successful for ID: {request.openmrsId}")
            
            return AuthenticationResult(
                isSuccess=True,
                patientName=patient_name,
                welcomeMessage=welcome_message
            )
        else:
            logger.warning(f"Patient not found for ID: {request.openmrsId}")
            return AuthenticationResult(
                isSuccess=False,
                errorMessage="Patient ID not found. Please check your OpenMRS Patient ID and try again."
            )
            
    except Exception as e:
        logger.error(f"Error verifying patient {request.openmrsId}: {e}")
        return AuthenticationResult(
            isSuccess=False,
            errorMessage="Unable to verify patient at this time. Please try again later."
        )


def extract_patient_name(patient_resource: dict) -> str:
    """Extract patient name from OpenMRS REST API Patient resource."""
    try:
        # OpenMRS REST API structure for patient name
        person = patient_resource.get("person", {})
        names = person.get("names", [])
        
        if names:
            # Get the preferred name (first in the list)
            name = names[0]
            given_name = name.get("givenName", "")
            family_name = name.get("familyName", "")
            
            # Construct full name
            if given_name and family_name:
                return f"{given_name} {family_name}"
            elif given_name:
                return given_name
            elif family_name:
                return family_name
        
        # Fallback to display name if available
        display_name = patient_resource.get("display", "")
        if display_name and " - " in display_name:
            # OpenMRS display format is typically "Name - ID"
            return display_name.split(" - ")[0]
        
        return "Patient"
        
    except Exception as e:
        logger.error(f"Error extracting patient name: {e}")
        return "Patient" 