package com.example.omrsappo.data.repository

import com.example.omrsappo.data.api.OpenMRSApi
import kotlinx.coroutines.delay
import javax.inject.Inject
import javax.inject.Singleton

interface AppointmentRepository {
    suspend fun createAppointment(appointmentData: Map<String, Any>): Boolean
}

@Singleton
class AppointmentRepositoryImpl @Inject constructor(
    private val openMRSApi: OpenMRSApi
) : AppointmentRepository {
    
    override suspend fun createAppointment(appointmentData: Map<String, Any>): Boolean {
        // Simulate API call
        delay(1000)
        
        // For POC, always return success
        // In production, this would call the actual OpenMRS API
        return true
    }
}