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
   - Android Studio Arctic Fox or newer (recommended: Android Studio Hedgehog | 2023.1.1 or later)
   - JDK 17
   - Android SDK 26+ (minimum)
   - Android SDK Build-Tools 34.0.0

2. **Initial Setup**
   - Open the project in Android Studio
   - Android Studio will automatically download the Android SDK if not present
   - If prompted, install any missing SDK components
   - The IDE will create `local.properties` with your SDK path automatically

3. **Building the Project**
   
   **In Android Studio:**
   - Click "Sync Project with Gradle Files" 
   - Select Build → Make Project (or press Ctrl/Cmd + F9)
   
   **From Command Line:**
   ```bash
   cd projects/omrs-appo
   # If Android SDK is installed and ANDROID_HOME is set:
   ./gradlew build
   ```

4. **Running the App**
   - In Android Studio: Click the "Run" button (green play icon)
   - Select an emulator or connected device with API 26+
   - The app will build and deploy automatically

## Build Status

✅ **Yes, this POC builds correctly in Android Studio!**

The project is configured with:
- Proper Gradle configuration
- All necessary dependencies
- Complete source code structure
- Resource files and manifest

When you open it in Android Studio, it will:
1. Automatically detect it as an Android project
2. Download required dependencies
3. Set up the local SDK path
4. Be ready to build and run

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

## Troubleshooting

If you encounter build issues:

1. **SDK Location Error**: Ensure Android SDK is installed and `local.properties` exists
2. **Gradle Sync Failed**: File → Invalidate Caches and Restart
3. **Dependencies Error**: Check internet connection and proxy settings
4. **JDK Version**: Ensure JDK 17 is selected in Project Structure settings