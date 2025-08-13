#!/bin/bash

# RAG System Setup Script
# This script helps set up the Augmented RAG system for OpenMRS

set -e

echo "============================================"
echo "OpenMRS Augmented RAG System Setup"
echo "============================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "Please edit .env to configure your environment:"
    echo "  - Update MYSQL_* variables for your OpenMRS database"
    echo "  - Set CHROMA_AUTH_TOKEN to a secure value"
    echo "  - Configure LLM settings if using local models"
    echo ""
else
    echo "✓ .env file already exists"
fi

# Create instant network if it doesn't exist
echo ""
echo "Checking Docker network..."
if ! docker network ls | grep -q instant; then
    echo "Creating 'instant' network..."
    docker network create instant
    echo "✓ Created instant network"
else
    echo "✓ instant network exists"
fi

# Function to deploy a service
deploy_service() {
    local service_name=$1
    local service_path=$2
    
    echo ""
    echo "Deploying $service_name..."
    cd "$service_path"
    
    if [ -f docker-compose.yml ]; then
        docker-compose up -d
        echo "✓ $service_name deployed"
    else
        echo "✗ docker-compose.yml not found in $service_path"
        return 1
    fi
    cd - > /dev/null
}

# Main menu
echo ""
echo "What would you like to do?"
echo "1) Deploy complete RAG system"
echo "2) Deploy vector database only"
echo "3) Run embedding pipeline"
echo "4) Deploy multiagent chat with RAG"
echo "5) Check system status"
echo "6) Stop all services"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo ""
        echo "Deploying complete RAG system..."
        
        # Deploy vector database
        deploy_service "Vector Database" "packages/vector-db"
        
        # Wait for vector-db to be ready
        echo ""
        echo "Waiting for vector database to be ready..."
        sleep 10
        
        # Build and run embedding pipeline
        echo ""
        echo "Building embedding pipeline..."
        cd packages/embedding-pipeline
        docker build -t embedding-pipeline:latest .
        echo "✓ Embedding pipeline built"
        
        echo ""
        echo "Running embedding pipeline to populate vector database..."
        docker run --rm \
            --network instant \
            --env-file ../../.env \
            embedding-pipeline:latest
        echo "✓ Embeddings generated"
        cd - > /dev/null
        
        # Deploy multiagent chat
        deploy_service "Multiagent Chat" "packages/multiagent_chat"
        
        echo ""
        echo "============================================"
        echo "RAG System Deployment Complete!"
        echo "============================================"
        echo "Services running:"
        echo "  - Vector DB: http://localhost:8001"
        echo "  - Multiagent Chat: http://localhost:3000"
        echo ""
        ;;
        
    2)
        deploy_service "Vector Database" "packages/vector-db"
        ;;
        
    3)
        echo ""
        echo "Running embedding pipeline..."
        cd packages/embedding-pipeline
        
        # Build if needed
        if ! docker images | grep -q embedding-pipeline; then
            echo "Building embedding pipeline image..."
            docker build -t embedding-pipeline:latest .
        fi
        
        # Run pipeline
        docker run --rm \
            --network instant \
            --env-file ../../.env \
            embedding-pipeline:latest
        
        cd - > /dev/null
        echo "✓ Embedding pipeline completed"
        ;;
        
    4)
        deploy_service "Multiagent Chat" "packages/multiagent_chat"
        ;;
        
    5)
        echo ""
        echo "System Status:"
        echo "--------------"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(vector-db|embedding-pipeline|multiagent)" || echo "No RAG services running"
        ;;
        
    6)
        echo ""
        echo "Stopping all RAG services..."
        
        # Stop services
        cd packages/vector-db && docker-compose down && cd - > /dev/null
        cd packages/multiagent_chat && docker-compose down && cd - > /dev/null
        
        echo "✓ All services stopped"
        ;;
        
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Done!"