package com.example.omrsappo.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.omrsappo.R
import com.example.omrsappo.ui.screens.viewmodels.LoginViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LoginScreen(
    onLoginSuccess: (String) -> Unit,
    viewModel: LoginViewModel = hiltViewModel()
) {
    var openmrsId by remember { mutableStateOf("") }
    val loginState by viewModel.loginState.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = stringResource(R.string.login_title),
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.padding(bottom = 32.dp)
        )

        OutlinedTextField(
            value = openmrsId,
            onValueChange = { openmrsId = it },
            label = { Text(stringResource(R.string.openmrs_id_hint)) },
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 24.dp),
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Text),
            placeholder = { Text(stringResource(R.string.openmrs_id_example)) }
        )

        Button(
            onClick = {
                viewModel.authenticateWithOpenMRS(openmrsId)
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            enabled = openmrsId.isNotBlank() && !loginState.isLoading
        ) {
            if (loginState.isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    color = MaterialTheme.colorScheme.onPrimary
                )
            } else {
                Text(stringResource(R.string.login_button))
            }
        }

        loginState.error?.let { error ->
            Text(
                text = error,
                color = MaterialTheme.colorScheme.error,
                modifier = Modifier.padding(top = 16.dp)
            )
        }
    }

    // Handle successful login
    LaunchedEffect(loginState.isSuccess, loginState.welcomeMessage) {
        if (loginState.isSuccess) {
            val welcomeMessage = loginState.welcomeMessage ?: "Hello! Please describe your main concern."
            onLoginSuccess(welcomeMessage)
        }
    }
}