package com.example.omrsappo

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class OmrsAppoApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        // Initialize FHIR Engine and other app-wide components here
    }
}