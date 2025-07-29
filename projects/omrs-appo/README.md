# OMRS Appo - FHIR-based Appointment Assistant POC

This is a Proof of Concept Android application that demonstrates an AI-powered appointment scheduling assistant using FHIR standards and OpenMRS integration.

## Features

1. **Simple Login Interface** - Basic authentication (ready for SSO integration)
2. **Chat-based Interface** - Conversational UI for appointment requests
3. **FHIR Integration** - Connects to FHIR endpoints for patient data
4. **AI-Powered Chat** - Integration with MedGemma model for intelligent responses
5. **Report Generation** - Summarizes patient concerns and health history
6. **OpenMRS Integration** - Creates appointments via OpenMRS API

## Architecture

The app is built using:
- **Kotlin** and **Jetpack Compose** for modern Android development
- **FHIR Android SDK** for healthcare data standards
- **Hilt** for dependency injection
- **Retrofit** for API calls
- **Coroutines** for async operations
- **Material 3** for UI components

## Project Structure

```
omrs-appo/
├── app/
│   ├── src/main/java/com/example/omrsappo/
│   │   ├── data/
│   │   │   ├── api/          # API interfaces
│   │   │   └── repository/   # Repository implementations
│   │   ├── di/              # Dependency injection
│   │   ├── domain/
│   │   │   └── model/       # Data models
│   │   └── ui/
│   │       ├── screens/     # Composable screens
│   │       └── theme/       # Material 3 theme
│   └── src/main/res/        # Resources
└── build.gradle.kts         # Build configuration
```

## Setup Instructions

1. **Prerequisites**
   - Android Studio Arctic Fox or newer
   - JDK 17
   - Android SDK 26+ (minimum)

2. **Building the Project**
   ```bash
   cd projects/omrs-appo
   ./gradlew build
   ```

3. **Running the App**
   - Open the project in Android Studio
   - Run on emulator or physical device with API 26+

## POC Limitations

This is a proof of concept with the following simplifications:
- Mock authentication (accepts any non-empty credentials)
- Simulated AI responses (no actual MedGemma integration yet)
- Mock appointment creation (always returns success)
- No persistent storage
- No real FHIR server connection yet

## Next Steps

1. Integrate with actual Keycloak/OpenMRS authentication
2. Connect to real FHIR server for patient data
3. Implement actual MedGemma API integration
4. Add FHIR resource creation for appointments
5. Implement proper error handling and offline support
6. Add comprehensive testing
7. Enhance UI/UX with appointment details and confirmation

## Configuration

Update the following in `di/AppModule.kt` for real endpoints:
- OpenMRS base URL
- MedGemma API endpoint
- Authentication endpoints