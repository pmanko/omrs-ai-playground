#!/usr/bin/env bash
set -euo pipefail

# Env contract
# TARGET: HAPI | OPENMRS
# BASE_URL: http://service:port/fhir (HAPI) or http://openmrs:8080/openmrs/ws/fhir2/R4 (OpenMRS)
# FHIR_USERNAME?, FHIR_PASSWORD? (optional)
# DATASET: small | full
# CORES: default 4
# TIMEOUT?: seconds (optional)
# BATCH_SIZE?: optional

TARGET=${TARGET:-HAPI}
BASE_URL=${BASE_URL:-}
DATASET=${DATASET:-small}
CORES=${CORES:-4}

if [[ -z "$BASE_URL" ]]; then
  echo "BASE_URL is required" >&2
  exit 1
fi

# Dataset directory mapping with sensible defaults
# - small -> /app/sample_data_small
# - full  -> /app/sample_data
SMALL_DIR=${SMALL_DIR:-sample_data_small}
FULL_DIR=${FULL_DIR:-sample_data}

case "$DATASET" in
  small)
    INPUT_DIR="/app/${SMALL_DIR}"
    ;;
  full)
    INPUT_DIR="/app/${FULL_DIR}"
    ;;
  *)
    INPUT_DIR="/app/${DATASET}"
    ;;
esac

AUTH_ARGS=()
if [[ -n "${FHIR_USERNAME:-}" && -n "${FHIR_PASSWORD:-}" ]]; then
  AUTH_ARGS+=("--username" "$FHIR_USERNAME" "--password" "$FHIR_PASSWORD")
fi

echo "Running uploader: TARGET=$TARGET BASE_URL=$BASE_URL DATASET=$DATASET CORES=$CORES INPUT_DIR=$INPUT_DIR"

CONVERT_ARG=()
if [[ "$TARGET" == "OpenMRS" ]]; then
  CONVERT_ARG+=("--convert_to_openmrs")
fi

exec python3 /app/uploader/main.py "$TARGET" "$BASE_URL" \
  --input_dir "$INPUT_DIR" \
  --cores "$CORES" \
  ${CONVERT_ARG[@]:-} \
  ${AUTH_ARGS[@]:-}

