#!/bin/bash

declare ACTION=""
declare MODE=""
declare COMPOSE_FILE_PATH=""
declare UTILS_PATH=""
declare STACK="agenta"

function init_vars() {
  ACTION=$1
  MODE=$2

  COMPOSE_FILE_PATH=$(
    cd "$(dirname "${BASH_SOURCE[0]}")" || exit
    pwd -P
  )

  UTILS_PATH="${COMPOSE_FILE_PATH}/../utils"

  # Load environment variables from package-metadata.json if present
  if [ -f "${COMPOSE_FILE_PATH}/package-metadata.json" ]; then
    export $(jq -r '.environmentVariables | to_entries|map("\(.key)=\(.value)")|.[]' "${COMPOSE_FILE_PATH}/package-metadata.json")
  fi

  readonly ACTION
  readonly MODE
  readonly COMPOSE_FILE_PATH
  readonly UTILS_PATH
  readonly STACK
}

# shellcheck disable=SC1091
function import_sources() {
  source "${UTILS_PATH}/docker-utils.sh"
  source "${UTILS_PATH}/config-utils.sh"
  source "${UTILS_PATH}/log.sh"
}

function initialize_package() {
  local dev_compose_filename=""
  local importer_compose_filename="importer/docker-compose.config.yml"

  if [ "${MODE}" == "dev" ]; then
    log info "Running package in DEV mode"
    dev_compose_filename="docker-compose.dev.yml"
  else
    log info "Running package in PROD mode"
  fi

  (
    # First, initialize the database
    log info "Initializing Agenta database..."
    docker::deploy_service "$STACK" "${COMPOSE_FILE_PATH}" "$importer_compose_filename"
    
    # Wait for DB init to complete
    sleep 5
    
    # Deploy main Agenta services
    log info "Deploying Agenta services..."
    docker::deploy_service "$STACK" "${COMPOSE_FILE_PATH}" "docker-compose.yml" "" "$dev_compose_filename"
  ) ||
    {
      log error "Failed to deploy Agenta package"
      exit 1
    }
}

function destroy_package() {
  docker::stack_destroy "$STACK"
  docker::prune_configs "agenta"
}

main() {
  init_vars "$@"
  import_sources

  if [[ "${ACTION}" == "init" ]] || [[ "${ACTION}" == "up" ]]; then
    initialize_package
  elif [[ "${ACTION}" == "down" ]]; then
    log info "Scaling down package"
    docker::scale_services "$STACK" 0
  elif [[ "${ACTION}" == "destroy" ]]; then
    log info "Destroying package"
    destroy_package
  else
    log error "Valid options are: init, up, down, or destroy"
  fi
}

main "$@"

