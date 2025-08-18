#!/bin/bash

# Get version parameter (default to latest)
cli_version=${1:-latest}

# Show help if requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
  echo "Usage: get-cli.sh [cli_version]"
  echo "  cli_version: Version to download (default: latest)"
  echo "  Automatically detects system type and downloads appropriate binary"
  exit 0
fi

# Detect system type
detect_system() {
  case "$(uname -s)" in
    Linux*)     echo "linux";;
    Darwin*)    echo "macos";;
    CYGWIN*|MINGW*|MSYS*) echo "windows";;
    *)          echo "unknown";;
  esac
}

system=$(detect_system)

if [[ "$system" == "unknown" ]]; then
  echo "Error: Unable to detect system type. Supported systems: Linux, macOS, Windows"
  exit 1
fi

# Set binary name and download URL based on system
case ${system} in
linux)
  binary_name="instant"
  download_url="https://github.com/openhie/instant-v2/releases/download/${cli_version}/instant-linux"
  ;;
macos)
  binary_name="instant"
  download_url="https://github.com/openhie/instant-v2/releases/download/${cli_version}/instant-macos"
  ;;
windows)
  binary_name="instant.exe"
  download_url="https://github.com/openhie/instant-v2/releases/download/${cli_version}/instant-win.exe"
  ;;
esac

echo "Detected system: ${system}"
echo "Downloading ${binary_name} version: ${cli_version}"

# Download and make executable
curl -L "${download_url}" -o "${binary_name}"
if [[ $? -eq 0 ]]; then
  chmod +x "./${binary_name}"
  echo "Successfully downloaded ${binary_name}"
else
  echo "Error: Failed to download ${binary_name}"
  exit 1
fi
