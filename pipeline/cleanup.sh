#!/usr/bin/env bash
# ==============================================================================
# Safe Pipeline Cleanup Script
# Cleans temporary files, build caches, staging files, and lock files.
# Preserves raw source datasets.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Performing Safe Local Cleanup ==="

# Clean staging files
rm -rf "${PROJECT_ROOT}/results/staging"
rm -f /tmp/canary_*.tmp
rm -f /tmp/hadoop-*.pid

# Clean Derby metastore lock files
HIVE_HOME="${HIVE_HOME:-/home/maddy/opt/hive-4.0.0}"
rm -f "${HIVE_HOME}/metastore_db/db.lck" "${HIVE_HOME}/metastore_db/dbex.lck" 2>/dev/null || true

# Clean Python caches
find "${PROJECT_ROOT}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${PROJECT_ROOT}" -type f -name "*.pyc" -delete 2>/dev/null || true

# Clean Java build artifacts
rm -rf "${PROJECT_ROOT}/hadoop/mapreduce/build"

echo "Cleanup completed safely. Source datasets and HDFS permanent layers preserved."
