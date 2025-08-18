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

# Optional readiness wait for FHIR CapabilityStatement
TIMEOUT=${TIMEOUT:-900}
WAIT_FOR_READY=${WAIT_FOR_READY:-true}
if [[ "$WAIT_FOR_READY" == "true" ]]; then
  METADATA_URL="${BASE_URL%/}/metadata"
  echo "Waiting for FHIR metadata at $METADATA_URL (timeout ${TIMEOUT}s)"
  end=$((SECONDS + TIMEOUT))
  ready=1
  while (( SECONDS < end )); do
    if python3 - <<'PY'
import os, sys, requests
base = os.environ.get('BASE_URL', '')
url = base.rstrip('/') + '/metadata'
user = os.environ.get('FHIR_USERNAME')
pwd = os.environ.get('FHIR_PASSWORD')
auth = (user, pwd) if user and pwd else None
try:
    r = requests.get(url, timeout=5, auth=auth, headers={'Accept': 'application/fhir+json'})
    r.raise_for_status()
    data = r.json()
    sys.exit(0 if data.get('resourceType') == 'CapabilityStatement' else 1)
except Exception:
    sys.exit(1)
PY
    then
      echo "FHIR endpoint is ready"
      ready=0
      break
    fi
    sleep 3
  done
  if (( ready != 0 )); then
    echo "Timed out waiting for FHIR metadata at $METADATA_URL" >&2
    exit 1
  fi
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
  

