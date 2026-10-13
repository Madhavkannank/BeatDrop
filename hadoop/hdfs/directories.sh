#!/usr/bin/env bash
# ==============================================================================
# HDFS Storage Architecture & Layer Provisioning
# Provisions: /music_project/{raw, processed, curated, analytics, quarantine}
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

export JAVA_HOME="${JAVA_HOME:-/home/maddy/opt/jdk-17}"
export HADOOP_HOME="${HADOOP_HOME:-/home/maddy/opt/hadoop-3.5.0}"
export PATH="${JAVA_HOME}/bin:${HADOOP_HOME}/bin:${PATH}"

BASE_DIR="/music_project"
LAYERS=(
    "raw"
    "processed"
    "curated"
    "analytics"
    "quarantine"
)

echo "=== Provisioning HDFS Data Lake Architecture ==="
echo "Base Directory: ${BASE_DIR}"

for layer in "${LAYERS[@]}"; do
    TARGET_PATH="${BASE_DIR}/${layer}"
    echo "Creating layer: ${TARGET_PATH}"
    hdfs dfs -mkdir -p "${TARGET_PATH}"
    hdfs dfs -chmod 755 "${TARGET_PATH}"
done

echo ""
echo "=== Verifying HDFS Lake Structure ==="
hdfs dfs -ls -d "${BASE_DIR}"/*

echo ""
echo "HDFS data lake directory structure successfully provisioned."
