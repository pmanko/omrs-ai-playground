#!/bin/bash

# Vector Database (ChromaDB) Swarm Deployment Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION="${1:-deploy}"

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(cat "$SCRIPT_DIR/.env" | grep -v '^#' | xargs)
fi

# Set default values
export VECTOR_DB_IMAGE=${VECTOR_DB_IMAGE:-chromadb/chroma:latest}
export VECTOR_DB_PORT=${VECTOR_DB_PORT:-8000}
export CHROMA_AUTH_TOKEN=${CHROMA_AUTH_TOKEN:-test-token}
export STACK_NAME=${STACK_NAME:-vector-db}

# Functions
deploy() {
    echo "Deploying Vector Database stack..."
    docker stack deploy -c "$SCRIPT_DIR/docker-compose.yml" "$STACK_NAME"
    echo "Vector Database stack deployed as '$STACK_NAME'"
}

remove() {
    echo "Removing Vector Database stack..."
    docker stack rm "$STACK_NAME"
    echo "Vector Database stack removed"
}

status() {
    echo "Vector Database Stack Status:"
    docker stack services "$STACK_NAME"
}

logs() {
    SERVICE="${2:-vector-db}"
    docker service logs -f "${STACK_NAME}_${SERVICE}"
}

# Main execution
case "$ACTION" in
    deploy|up)
        deploy
        ;;
    remove|down)
        remove
        ;;
    status|ps)
        status
        ;;
    logs)
        logs "$@"
        ;;
    *)
        echo "Usage: $0 {deploy|remove|status|logs} [service]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Deploy the vector database stack"
        echo "  remove  - Remove the vector database stack"
        echo "  status  - Show stack status"
        echo "  logs    - Show service logs"
        exit 1
        ;;
esac