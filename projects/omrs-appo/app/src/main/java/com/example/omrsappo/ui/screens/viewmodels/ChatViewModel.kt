package com.example.omrsappo.ui.screens.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.omrsappo.data.repository.AppointmentRepository
import com.example.omrsappo.data.repository.ChatRepository
import com.example.omrsappo.domain.model.ChatMessage
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

data class ChatState(
    val messages: List<ChatMessage> = listOf(),
    val isLoading: Boolean = false,
    val appointmentCreated: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val chatRepository: ChatRepository,
    private val appointmentRepository: AppointmentRepository
) : ViewModel() {

    private val _chatState = MutableStateFlow(ChatState())
    val chatState: StateFlow<ChatState> = _chatState.asStateFlow()

    private var isInitialized = false

    fun initializeWithWelcomeMessage(welcomeMessage: String) {
        if (!isInitialized) {
            val greetingMessage = ChatMessage(
                id = UUID.randomUUID().toString(),
                content = welcomeMessage,
                isUser = false
            )
            _chatState.value = ChatState(messages = listOf(greetingMessage))
            isInitialized = true
        }
    }

    fun sendMessage(message: String) {
        viewModelScope.launch {
            // Add user message
            val userMessage = ChatMessage(
                id = UUID.randomUUID().toString(),
                content = message,
                isUser = true
            )
            
            _chatState.value = _chatState.value.copy(
                messages = _chatState.value.messages + userMessage,
                isLoading = true
            )

            try {
                // Process message with AI and get response
                val response = chatRepository.processMessage(message)
                
                // Add AI response
                val aiMessage = ChatMessage(
                    id = UUID.randomUUID().toString(),
                    content = response.message,
                    isUser = false
                )
                
                _chatState.value = _chatState.value.copy(
                    messages = _chatState.value.messages + aiMessage,
                    isLoading = false
                )

                // Check if we should create an appointment
                if (response.shouldCreateAppointment) {
                    createAppointment(response.appointmentData)
                }

            } catch (e: Exception) {
                _chatState.value = _chatState.value.copy(
                    isLoading = false,
                    error = e.message
                )
            }
        }
    }

    private suspend fun createAppointment(appointmentData: Map<String, Any>?) {
        appointmentData?.let {
            try {
                appointmentRepository.createAppointment(it)
                _chatState.value = _chatState.value.copy(appointmentCreated = true)
            } catch (e: Exception) {
                _chatState.value = _chatState.value.copy(error = e.message)
            }
        }
    }

    fun dismissAppointmentDialog() {
        _chatState.value = _chatState.value.copy(appointmentCreated = false)
    }
}