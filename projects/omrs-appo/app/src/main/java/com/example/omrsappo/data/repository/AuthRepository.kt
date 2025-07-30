package com.example.omrsappo.data.repository

import kotlinx.coroutines.delay
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST
import javax.inject.Inject
import javax.inject.Singleton

data class AuthenticationRequest(
    val openmrsId: String
)

data class AuthenticationResult(
    val isSuccess: Boolean,
    val patientName: String? = null,
    val welcomeMessage: String? = null,
    val errorMessage: String? = null
)

interface OpenMRSAuthApi {
    @POST("api/auth/verify-patient")
    suspend fun verifyPatient(@Body request: AuthenticationRequest): Response<AuthenticationResult>
}

interface AuthRepository {
    suspend fun authenticateWithOpenMRS(openmrsId: String): AuthenticationResult
}

@Singleton
class AuthRepositoryImpl @Inject constructor(
    private val openMRSAuthApi: OpenMRSAuthApi
) : AuthRepository {
    
    override suspend fun authenticateWithOpenMRS(openmrsId: String): AuthenticationResult {
        return try {
            val request = AuthenticationRequest(openmrsId)
            val response = openMRSAuthApi.verifyPatient(request)
            
            if (response.isSuccessful) {
                response.body() ?: AuthenticationResult(
                    isSuccess = false,
                    errorMessage = "Invalid response from server"
                )
            } else {
                AuthenticationResult(
                    isSuccess = false,
                    errorMessage = "Authentication failed. Please check your Patient ID and try again."
                )
            }
        } catch (e: Exception) {
            AuthenticationResult(
                isSuccess = false,
                errorMessage = "Unable to connect to authentication service. Please check your internet connection and try again."
            )
        }
    }
}