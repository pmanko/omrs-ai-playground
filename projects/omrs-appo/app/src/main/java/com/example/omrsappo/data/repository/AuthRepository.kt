package com.example.omrsappo.data.repository

import kotlinx.coroutines.delay
import javax.inject.Inject
import javax.inject.Singleton

interface AuthRepository {
    suspend fun login(username: String, password: String): Boolean
}

@Singleton
class AuthRepositoryImpl @Inject constructor() : AuthRepository {
    
    override suspend fun login(username: String, password: String): Boolean {
        // Simulate network delay
        delay(1000)
        
        // For POC, accept any non-empty credentials
        // In production, this would validate against OpenMRS/Keycloak
        return username.isNotEmpty() && password.isNotEmpty()
    }
}