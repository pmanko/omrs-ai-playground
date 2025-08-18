#!/bin/bash

declare ACTION=""
declare MODE=""
declare COMPOSE_FILE_PATH=""
declare UTILS_PATH=""
declare STACK="analytics-ohs-data-pipes"

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
    # Read as compact JSON entries to preserve spaces and special characters
    while IFS= read -r entry; do
      key=$(echo "$entry" | jq -r '.key')
      value=$(echo "$entry" | jq -r '.value')
      # Assign without word-splitting and export
      printf -v "$key" '%s' "$value"
      export "$key"
    done < <(jq -c '.environmentVariables | to_entries[]' "${COMPOSE_FILE_PATH}/package-metadata.json")
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
  local spark_dev_compose_filename=""
  local controller_dev_compose_filename=""

  if [ "${MODE}" == "dev" ]; then
    log info "Running package in DEV mode"
    spark_dev_compose_filename="docker-compose.spark.dev.yml"
    controller_dev_compose_filename="docker-compose.controller.dev.yml"
  else
    log info "Running package in PROD mode"
  fi

  (
    # Deploy Spark first
    docker::deploy_service "$STACK" "${COMPOSE_FILE_PATH}" "docker-compose.spark.yml" "" "$spark_dev_compose_filename"

    # Then deploy the pipeline controller (no config substitution needed)
    # Deploy controller; compose file references configs directly from ./config
    docker::deploy_service "$STACK" "${COMPOSE_FILE_PATH}" "docker-compose.controller.yml" "" "$controller_dev_compose_filename"

    # Post-deploy sanity: fail fast if the controller crashes during boot
    local attempts=40
    local svc="${STACK}_pipeline-controller"
    log info "Checking ${svc} boot status ..."
    until [ $attempts -le 0 ]; do
      if docker service logs --tail 200 "$svc" 2>/dev/null | grep -q "Started ControlPanelApplication"; then
        overwrite "Checking ${svc} boot status ... Done"
        break
      fi
      if docker service logs --tail 200 "$svc" 2>/dev/null | grep -qE "Application run failed|NoSuchFileException|UnsatisfiedDependencyException"; then
        log error "${svc} failed to start. Recent logs:" 
        docker service logs --tail 200 "$svc" 2>/dev/null 1>&2
        exit 1
      fi
      sleep 3
      attempts=$((attempts-1))
    done
    if [ $attempts -le 0 ]; then
      log error "Timed out waiting for ${svc} to report a successful start"
      exit 1
    fi
  ) ||
    {
      log error "Failed to deploy package"
      exit 1
    }
}

function destroy_package() {
  docker::stack_destroy "$STACK"
  docker::prune_configs "analytics-ohs-data-pipes"
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


