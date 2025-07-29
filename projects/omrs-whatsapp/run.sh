#!/bin/bash

# WhatsApp-OpenMRS-MedGemma Service Runner Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_status "Creating .env from .env.example..."
    cp .env.example .env
    print_warning "Please edit .env file with your credentials before running."
    exit 1
fi

# Function to check if required environment variables are set
check_env_vars() {
    local required_vars=(
        "WHATSAPP_ACCESS_TOKEN"
        "WHATSAPP_PHONE_NUMBER_ID"
        "GOOGLE_API_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=your_" .env || grep -q "^${var}=$" .env; then
            print_error "${var} is not configured in .env file!"
            exit 1
        fi
    done
}

# Main command handler
case "$1" in
    start)
        print_status "Starting WhatsApp-OpenMRS-MedGemma service..."
        check_env_vars
        docker-compose up -d
        print_status "Service started! Check logs with: ./run.sh logs"
        ;;
    
    start-dev)
        print_status "Starting in development mode with ngrok..."
        check_env_vars
        docker-compose --profile development up -d
        print_status "Waiting for ngrok to start..."
        sleep 5
        print_status "Ngrok URL:"
        docker logs omrs-ngrok 2>&1 | grep -o 'https://.*\.ngrok\.io' | head -1
        ;;
    
    stop)
        print_status "Stopping services..."
        docker-compose down
        print_status "Services stopped."
        ;;
    
    restart)
        print_status "Restarting services..."
        docker-compose restart
        ;;
    
    logs)
        docker-compose logs -f omrs-whatsapp
        ;;
    
    logs-all)
        docker-compose logs -f
        ;;
    
    status)
        print_status "Service status:"
        docker-compose ps
        ;;
    
    health)
        print_status "Checking service health..."
        curl -s http://localhost:8000/health | python -m json.tool
        ;;
    
    stats)
        print_status "Service statistics:"
        curl -s http://localhost:8000/api/stats | python -m json.tool
        ;;
    
    shell)
        print_status "Opening shell in service container..."
        docker exec -it omrs-whatsapp /bin/bash
        ;;
    
    redis-cli)
        print_status "Opening Redis CLI..."
        docker exec -it omrs-redis redis-cli
        ;;
    
    build)
        print_status "Building Docker image..."
        docker-compose build
        ;;
    
    clean)
        print_status "Cleaning up volumes and containers..."
        docker-compose down -v
        print_warning "This will delete all data including Redis sessions!"
        ;;
    
    test-webhook)
        if [ -z "$2" ]; then
            print_error "Usage: ./run.sh test-webhook <phone_number>"
            exit 1
        fi
        print_status "Sending test message to webhook..."
        curl -X POST http://localhost:8000/api/webhook/whatsapp \
            -H "Content-Type: application/json" \
            -d '{
                "object": "whatsapp_business_account",
                "entry": [{
                    "changes": [{
                        "value": {
                            "messages": [{
                                "id": "test_message_id",
                                "from": "'"$2"'",
                                "timestamp": "'"$(date +%s)"'",
                                "type": "text",
                                "text": {"body": "Hello, this is a test message"}
                            }],
                            "contacts": [{
                                "wa_id": "'"$2"'",
                                "profile": {"name": "Test User"}
                            }]
                        }
                    }]
                }]
            }'
        ;;
    
    *)
        echo "WhatsApp-OpenMRS-MedGemma Service Manager"
        echo ""
        echo "Usage: ./run.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start         Start all services"
        echo "  start-dev     Start with ngrok for development"
        echo "  stop          Stop all services"
        echo "  restart       Restart services"
        echo "  logs          View service logs"
        echo "  logs-all      View all container logs"
        echo "  status        Show service status"
        echo "  health        Check service health"
        echo "  stats         Show service statistics"
        echo "  shell         Open shell in service container"
        echo "  redis-cli     Open Redis CLI"
        echo "  build         Build Docker image"
        echo "  clean         Clean up all data and volumes"
        echo "  test-webhook  Send test message to webhook"
        echo ""
        exit 1
        ;;
esac