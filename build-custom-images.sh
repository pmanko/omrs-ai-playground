#!/bin/bash
set -e

# Build custom Docker images for packages
# This script builds custom images based on projects/ folder structure
# and uses base image versions from package metadata or environment variables

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to get environment variable value with fallback priority:
# 1. Environment variable
# 2. Root-level .env file
# 3. Package metadata file
get_env_value() {
    local var_name="$1"
    local package_name="$2"
    
    # Check environment variable first
    if [[ -n "${!var_name}" ]]; then
        echo "${!var_name}"
        return
    fi
    
    # Check root-level .env file
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        local env_value=$(grep "^${var_name}=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2- | sed 's/^["'\'']//' | sed 's/["'\'']$//')
        if [[ -n "$env_value" ]]; then
            echo "$env_value"
            return
        fi
    fi
    
    # Check package metadata file
    if [[ -n "$package_name" ]]; then
        local metadata_file="$PROJECT_ROOT/packages/$package_name/package-metadata.json"
        if [[ -f "$metadata_file" ]]; then
            local metadata_value=$(jq -r ".environmentVariables.${var_name} // empty" "$metadata_file" 2>/dev/null)
            if [[ -n "$metadata_value" && "$metadata_value" != "null" ]]; then
                echo "$metadata_value"
                return
            fi
        fi
    fi
    
    echo ""
}

# Function to build custom image for a project
build_custom_image() {
    local project_name="$1"
    local package_name="$2"
    
    echo "🔨 Checking build configuration for project: $project_name"
    
    local project_dir="$PROJECT_ROOT/projects/$project_name"
    if [[ ! -d "$project_dir" ]]; then
        echo "❌ Project directory not found: $project_dir"
        return 1
    fi
    
    local dockerfile_path="$project_dir/Dockerfile"
    if [[ ! -f "$dockerfile_path" ]]; then
        echo "❌ Dockerfile not found: $dockerfile_path"
        return 1
    fi
    
    # Get image tag from environment/package metadata
    local image_tag_var_name=$(echo "${project_name}" | tr '[:lower:]' '[:upper:]')_IMAGE
    image_tag_var_name="${image_tag_var_name//-/_}" # Replace hyphens with underscores
    local image_tag=$(get_env_value "$image_tag_var_name" "$package_name")
    
    if [[ -z "$image_tag" ]]; then
        echo "⏭️  Skipping build for $project_name - ${image_tag_var_name} not set or empty"
        echo "   To enable building, set ${image_tag_var_name} in package metadata"
        return 0
    fi
    
    echo "🏷️  Will tag as: $image_tag"
    
    # Build the custom image
    echo "🏗️  Building custom image: $image_tag"

    cd "$project_dir"
    sudo docker build -t "$image_tag" .

    if [[ $? -eq 0 ]]; then
        echo "✅ Successfully built custom image: $image_tag"
        echo ""
        echo "The custom image is ready to use. Your package metadata already specifies:"
        echo "   \"${image_tag_var_name}\": \"$image_tag\""
        echo ""
    else
        echo "❌ Failed to build custom image for $project_name"
        return 1
    fi
}

# Function to build multiagent_chat images (both server and client)
build_multiagent_chat_images() {
    local project_name="multiagent_chat"
    local package_name="multiagent-chat"
    
    echo "🔨 Building Multi-Agent Chat images..."
    
    local project_dir="$PROJECT_ROOT/projects/$project_name"
    if [[ ! -d "$project_dir" ]]; then
        echo "❌ Project directory not found: $project_dir"
        return 1
    fi
    
    # Get image tags from environment/package metadata
    local server_image=$(get_env_value "MULTIAGENT_CHAT_SERVER_IMAGE" "$package_name")
    local client_image=$(get_env_value "MULTIAGENT_CHAT_CLIENT_IMAGE" "$package_name")
    
    if [[ -z "$server_image" || -z "$client_image" ]]; then
        echo "⏭️  Skipping build for $project_name - image tags not set"
        echo "   To enable building, set MULTIAGENT_CHAT_SERVER_IMAGE and MULTIAGENT_CHAT_CLIENT_IMAGE"
        return 0
    fi
    
    # Build server image
    echo "🏗️  Building server image: $server_image"
    cd "$project_dir"
    
    if [[ ! -f "Dockerfile.server" ]]; then
        echo "❌ Server Dockerfile not found: $project_dir/Dockerfile.server"
        return 1
    fi
    
    sudo docker build -f Dockerfile.server -t "$server_image" .
    if [[ $? -eq 0 ]]; then
        echo "✅ Successfully built server image: $server_image"
    else
        echo "❌ Failed to build server image for $project_name"
        return 1
    fi
    
    # Build client image
    echo "🏗️  Building client image: $client_image"
    
    if [[ ! -f "Dockerfile.client" ]]; then
        echo "❌ Client Dockerfile not found: $project_dir/Dockerfile.client"
        return 1
    fi
    
    sudo docker build -f Dockerfile.client -t "$client_image" .
    if [[ $? -eq 0 ]]; then
        echo "✅ Successfully built client image: $client_image"
        echo ""
        echo "Both Multi-Agent Chat images are ready to use:"
        echo "   Server: $server_image"
        echo "   Client: $client_image"
        echo ""
    else
        echo "❌ Failed to build client image for $project_name"
        return 1
    fi
}

# Main execution
echo "🚀 Building custom Docker images..."
echo "Project root: $PROJECT_ROOT"
echo ""

# Check if jq is available for JSON parsing
if ! command -v jq &> /dev/null; then
    echo "❌ jq is required but not installed. Please install jq to continue."
    exit 1
fi

# Build custom images for each project
if [[ $# -eq 0 ]]; then
    # Build all supported projects by default
    echo "🎯 Building all supported projects..."
    build_custom_image "omrs-appo-service" "omrs-appo-service"
    build_multiagent_chat_images
else
    # Build specific projects
    for project_name in "$@"; do
        if [[ "$project_name" == "omrs-appo-service" ]]; then
            build_custom_image "$project_name" "omrs-appo-service"
        elif [[ "$project_name" == "multiagent_chat" || "$project_name" == "multiagent-chat" ]]; then
            build_multiagent_chat_images
        else
            echo "⚠️  Skipping unsupported project: $project_name. Supported: 'omrs-appo-service', 'multiagent_chat'"
        fi
    done
fi

echo "🎉 Custom image build process completed!"