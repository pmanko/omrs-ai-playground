package com.example.omrsappo.di

import com.example.omrsappo.data.api.MedGemmaApi
import com.example.omrsappo.data.api.OpenMRSApi
import com.example.omrsappo.data.repository.*
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import javax.inject.Named
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    
    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        
        return OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .build()
    }
    
    @Provides
    @Singleton
    @Named("OpenMRS")
    fun provideOpenMRSRetrofit(okHttpClient: OkHttpClient): Retrofit {
        return Retrofit.Builder()
            .baseUrl("https://demo.openmrs.org/openmrs/ws/rest/v1/") // Demo URL for POC
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }
    
    @Provides
    @Singleton
    @Named("MedGemma")
    fun provideMedGemmaRetrofit(okHttpClient: OkHttpClient): Retrofit {
        return Retrofit.Builder()
            .baseUrl("https://api.example.com/medgemma/") // Placeholder URL
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }
    
    @Provides
    @Singleton
    @Named("OmrsAppoService")
    fun provideOmrsAppoServiceRetrofit(okHttpClient: OkHttpClient): Retrofit {
        return Retrofit.Builder()
            .baseUrl("https://service.omrs-appo.live/") // Production endpoint for omrs-appo-service
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }
    
    @Provides
    @Singleton
    fun provideOpenMRSApi(@Named("OpenMRS") retrofit: Retrofit): OpenMRSApi {
        return retrofit.create(OpenMRSApi::class.java)
    }
    
    @Provides
    @Singleton
    fun provideMedGemmaApi(@Named("MedGemma") retrofit: Retrofit): MedGemmaApi {
        return retrofit.create(MedGemmaApi::class.java)
    }
    
    @Provides
    @Singleton
    fun provideOpenMRSAuthApi(@Named("OmrsAppoService") retrofit: Retrofit): OpenMRSAuthApi {
        return retrofit.create(OpenMRSAuthApi::class.java)
    }
    
    @Provides
    @Singleton
    fun provideAuthRepository(openMRSAuthApi: OpenMRSAuthApi): AuthRepository {
        return AuthRepositoryImpl(openMRSAuthApi)
    }
    
    @Provides
    @Singleton
    fun provideChatRepository(medGemmaApi: MedGemmaApi): ChatRepository {
        return ChatRepositoryImpl(medGemmaApi)
    }
    
    @Provides
    @Singleton
    fun provideAppointmentRepository(openMRSApi: OpenMRSApi): AppointmentRepository {
        return AppointmentRepositoryImpl(openMRSApi)
    }
}