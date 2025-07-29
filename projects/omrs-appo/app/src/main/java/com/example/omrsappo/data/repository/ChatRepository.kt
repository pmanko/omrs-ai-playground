package com.example.omrsappo.data.repository

import com.example.omrsappo.data.api.MedGemmaApi
import kotlinx.coroutines.delay
import javax.inject.Inject
import javax.inject.Singleton

data class ChatResponse(
    val message: String,
    val shouldCreateAppointment: Boolean = false,
    val appointmentData: Map<String, Any>? = null
)

interface ChatRepository {
    suspend fun processMessage(message: String): ChatResponse
}

@Singleton
class ChatRepositoryImpl @Inject constructor(
    private val medGemmaApi: MedGemmaApi
) : ChatRepository {
    
    private var conversationContext = mutableListOf<String>()
    
    override suspend fun processMessage(message: String): ChatResponse {
        // Add message to context
        conversationContext.add("User: $message")
        
        // For POC, simulate AI response
        delay(1500)
        
        // Simple logic to detect appointment creation intent
        val lowerMessage = message.lowercase()
        val appointmentKeywords = listOf("schedule", "book", "appointment", "visit", "see doctor")
        val shouldCreate = appointmentKeywords.any { lowerMessage.contains(it) }
        
        val response = if (shouldCreate) {
            ChatResponse(
                message = "I understand you'd like to schedule an appointment. Based on your description, I've prepared an appointment summary. Would you like me to proceed with booking?",
                shouldCreateAppointment = true,
                appointmentData = mapOf(
                    "reason" to message,
                    "patientId" to "demo-patient-123",
                    "providerId" to "demo-provider-456",
                    "appointmentType" to "General Consultation"
                )
            )
        } else {
            // Simulate contextual response
            val responses = listOf(
                "Could you tell me more about your symptoms?",
                "How long have you been experiencing this?",
                "Have you had similar issues before?",
                "Would you like to schedule an appointment to discuss this with a doctor?"
            )
            ChatResponse(
                message = responses.random(),
                shouldCreateAppointment = false
            )
        }
        
        conversationContext.add("Assistant: ${response.message}")
        return response
    }
}