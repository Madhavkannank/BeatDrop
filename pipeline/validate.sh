#!/usr/bin/env bash
# ==============================================================================
# Pipeline Pre-flight Validation
# Verifies environment, schema contract, and service accessibility
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== [1/3] Running Platform Healthcheck ==="
"${PROJECT_ROOT}/scripts/healthcheck.sh"

echo "=== [2/3] Validating Configuration and Schemas ==="
CONFIG_FILE="${PROJECT_ROOT}/config/application.yaml"
SCHEMA_FILE="${PROJECT_ROOT}/config/schemas/music_schema.json"
DATA_FILE="${PROJECT_ROOT}/data/sample/music_tracks.csv"

for f in "${CONFIG_FILE}" "${SCHEMA_FILE}" "${DATA_FILE}"; do
    if [ ! -f "$f" ]; then
        echo "ERROR: Required file missing: $f"
        exit 1
    fi
    echo "Verified: $f"
done

echo "=== [3/3] Testing Python Dependencies ==="
python3 -c "import yaml; import json; import csv; import time; print('Python core dependencies verified.')"

echo ""
echo "Pre-flight validation PASSED. Pipeline is ready to execute."
