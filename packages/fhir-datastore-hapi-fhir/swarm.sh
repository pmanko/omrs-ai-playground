#!/bin/bash

declare ACTION=""
declare MODE=""
declare COMPOSE_FILE_PATH=""
declare UTILS_PATH=""
declare STACK="hapi-fhir"

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
  local hapi_fhir_dev_compose_filename=""

  if [ "${MODE}" == "dev" ]; then
    log info "Running package in DEV mode"
    hapi_fhir_dev_compose_filename="docker-compose.dev.yml"
  else
    log info "Running package in PROD mode"
  fi

  if [ "${CLUSTERED_MODE}" == "true" ]; then
    postgres_cluster_compose_filename="docker-compose-postgres.cluster.yml"
  fi

  (

    docker::await_service_status "postgres" "postgres-1" "Running"

    # Ensure DB is prepared before bringing up HAPI
    if [[ "${ACTION}" == "init" ]]; then
      log info "Deploying config importer"
      docker::deploy_config_importer "postgres" "$COMPOSE_FILE_PATH/importer/docker-compose.config.yml" "hapi_db_config" "hapi-fhir"
    fi

    # Bring up HAPI first
    docker::deploy_service "$STACK" "${COMPOSE_FILE_PATH}" "docker-compose.yml" "$hapi_fhir_dev_compose_filename"

    # Wait for HAPI to be ready before running the loader
    log info "Waiting for HAPI to become ready before running Synthea loader"
    attempts=60
    until [ $attempts -le 0 ]; do
      if docker service logs --tail 200 ${STACK}_hapi-fhir 2>/dev/null | grep -qE "Tomcat started|Started HAPI"; then
        overwrite "Waiting for HAPI to become ready before running Synthea loader ... Done"
        break
      fi
      sleep 2
      attempts=$((attempts-1))
    done

    # Only on init, run the one-shot Synthea loader now
    if [[ "${ACTION}" == "init" ]]; then
      log info "Deploying Synthea one-shot loader"
      docker::deploy_service "$STACK" "$COMPOSE_FILE_PATH/importer" "docker-compose.synthea-loader.yml"
      if [[ "${MODE}" != "dev" ]]; then
        log info "Cleaning up Synthea loader"
        config::remove_config_importer "$STACK" "hapi-synthea-loader"
        config::await_service_removed "$STACK" "hapi-synthea-loader"
      fi
    fi
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

  docker::prune_configs "hapi-fhir"
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
