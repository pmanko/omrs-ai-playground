package com.example.omrsappo

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.example.omrsappo.ui.screens.ChatScreen
import com.example.omrsappo.ui.screens.LoginScreen
import com.example.omrsappo.ui.theme.OmrsAppoTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            OmrsAppoTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    AppNavigation()
                }
            }
        }
    }
}

@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    
    NavHost(
        navController = navController,
        startDestination = "login"
    ) {
        composable("login") {
            LoginScreen(
                onLoginSuccess = { welcomeMessage ->
                    navController.navigate("chat/$welcomeMessage") {
                        popUpTo("login") { inclusive = true }
                    }
                }
            )
        }
        composable("chat/{welcomeMessage}") { backStackEntry ->
            val welcomeMessage = backStackEntry.arguments?.getString("welcomeMessage") ?: 
                "Hello! Please describe your main concern."
            ChatScreen(welcomeMessage = welcomeMessage)
        }
    }
}