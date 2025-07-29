package com.example.omrsappo.data.api

import retrofit2.http.Body
import retrofit2.http.POST

data class ChatRequest(
    val message: String,
    val context: List<String> = emptyList(),
    val patientData: Map<String, Any>? = null
)

data class ChatResponseDto(
    val response: String,
    val confidence: Float,
    val suggestedActions: List<String> = emptyList()
)

interface MedGemmaApi {
    
    @POST("chat")
    suspend fun sendMessage(@Body request: ChatRequest): ChatResponseDto
    
    @POST("analyze")
    suspend fun analyzeSymptoms(@Body symptoms: Map<String, Any>): Map<String, Any>
}