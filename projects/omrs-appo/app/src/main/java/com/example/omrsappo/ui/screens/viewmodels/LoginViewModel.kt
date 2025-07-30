package com.example.omrsappo.ui.screens.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.omrsappo.data.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class LoginState(
    val isLoading: Boolean = false,
    val isSuccess: Boolean = false,
    val error: String? = null,
    val welcomeMessage: String? = null
)

@HiltViewModel
class LoginViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _loginState = MutableStateFlow(LoginState())
    val loginState: StateFlow<LoginState> = _loginState.asStateFlow()

    fun authenticateWithOpenMRS(openmrsId: String) {
        viewModelScope.launch {
            _loginState.value = LoginState(isLoading = true)
            try {
                val authResult = authRepository.authenticateWithOpenMRS(openmrsId)
                if (authResult.isSuccess) {
                    _loginState.value = LoginState(
                        isSuccess = true,
                        welcomeMessage = authResult.welcomeMessage
                    )
                } else {
                    _loginState.value = LoginState(error = authResult.errorMessage ?: "Authentication failed")
                }
            } catch (e: Exception) {
                _loginState.value = LoginState(error = e.message ?: "Login failed")
            }
        }
    }
}