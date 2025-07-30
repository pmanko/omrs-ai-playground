#!/bin/bash

declare ACTION=""
declare MODE=""
declare COMPOSE_FILE_PATH=""
declare UTILS_PATH=""
declare STACK="openmrs"

function init_vars() {
  ACTION=$1
  MODE=$2

  COMPOSE_FILE_PATH=$(
    cd "$(dirname "${BASH_SOURCE[0]}")" || exit
    pwd -P
  )

  UTILS_PATH="${COMPOSE_FILE_PATH}/../utils"

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

  if [[ "${MODE}" == "dev" ]]; then
    log info "Running package in DEV mode"
    openmrs_dev_compose_filename="docker-compose.dev.yml"
    openmrs_gateway_dev_compose_filename="docker-compose.gateway.dev.yml"
  else
    log info "Running package in PROD mode"
    openmrs_compose_filename="docker-compose.yml"
    openmrs_gateway_compose_filename="docker-compose.gateway.yml"
  fi

  (
    docker::await_service_status "mysql" "mysql" "Running"
    docker::deploy_service "$STACK" "${COMPOSE_FILE_PATH}" "docker-compose.yml" "${openmrs_dev_compose_filename}"
    docker::await_service_status "$STACK" "openmrs" "Running"
    docker::deploy_service "$STACK" "${COMPOSE_FILE_PATH}" "docker-compose.frontend.yml"
    docker::await_service_status "$STACK" "openmrs-frontend" "Running"
    docker::deploy_service "$STACK" "${COMPOSE_FILE_PATH}" "docker-compose.gateway.yml" "${openmrs_gateway_dev_compose_filename}"
    docker::await_service_status "$STACK" "openmrs-gateway" "Running"
  ) ||
    {
      log error "Failed to deploy package"
      exit 1
    }
}

function destroy_package() {
  docker::stack_destroy "$STACK"

  if [[ "${CLUSTERED_MODE}" == "true" ]]; then
    log warn "Volumes are only deleted on the host on which the command is run. Postgres volumes on other nodes are not deleted"
  fi

  docker::prune_configs "openmrs"
}

main() {
  init_vars "$@"
  import_sources

  if [[ "${ACTION}" == "init" ]] || [[ "${ACTION}" == "up" ]]; then
    if [[ "${CLUSTERED_MODE}" == "true" ]]; then
      log info "Running package in Cluster node mode"
    else
      log info "Running package in Single node mode"
    fi

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
