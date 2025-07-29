package com.example.omrsappo.data.api

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface OpenMRSApi {
    
    @POST("appointment")
    suspend fun createAppointment(@Body appointment: Map<String, Any>): Map<String, Any>
    
    @GET("patient/{patientId}")
    suspend fun getPatient(@Path("patientId") patientId: String): Map<String, Any>
    
    @GET("patient/{patientId}/appointments")
    suspend fun getPatientAppointments(@Path("patientId") patientId: String): List<Map<String, Any>>
}