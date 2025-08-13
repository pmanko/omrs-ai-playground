# Documentation Index

## Architecture & Design
- [Augmented RAG Concept](./AUGMENTED-RAG.md) - High-level design for the RAG approach with OpenMRS concepts
- [RAG Implementation Plan](./AUGMENTED_RAG_IMPLEMENTATION_PLAN.md) - Detailed implementation guide for the augmented RAG system

## Packages Documentation

### Core Services
- [Multiagent Chat](./packages/multiagent-chat.md) - Multi-agent medical chat system
- [Vector Database](./packages/vector-db.md) - ChromaDB vector storage service
- [Embedding Pipeline](./packages/embedding-pipeline.md) - Batch processing for concept embeddings

### Infrastructure
- [OpenMRS EMR](./packages/emr-openmrs.md) - OpenMRS Electronic Medical Records
- [MySQL Database](./packages/database-mysql.md) - MySQL database for OpenMRS
- [Redis Cache](./packages/redis.md) - Redis for session management

## Deployment Guides
- [Configuration Guide](./deployment/configuration.md) - Central configuration management
- [Docker Swarm Setup](./deployment/swarm-setup.md) - Instructions for Docker Swarm deployment
- [Development Setup](./deployment/dev-setup.md) - Local development environment setup

## API Documentation
- [RAG API Endpoints](./api/rag-endpoints.md) - REST API for RAG operations
- [Agent Communication](./api/agent-protocol.md) - A2A protocol and message formats