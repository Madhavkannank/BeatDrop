#!/usr/bin/env bash
# ==============================================================================
# HDFS Storage Architecture Setup & Verification
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

export JAVA_HOME="${JAVA_HOME:-/home/maddy/opt/jdk-17}"
export HADOOP_HOME="${HADOOP_HOME:-/home/maddy/opt/hadoop-3.5.0}"
export PATH="${JAVA_HOME}/bin:${HADOOP_HOME}/bin:${PATH}"

echo "=========================================================="
echo "          HDFS STORAGE ARCHITECTURE SETUP                 "
echo "=========================================================="

echo "=== [1/3] Verifying Cluster Connectivity ==="
if ! hdfs dfsadmin -report >/dev/null 2>&1; then
    echo "ERROR: HDFS NameNode is not reachable at hdfs://localhost:9000."
    echo "Please run './scripts/bootstrap.sh' first."
    exit 1
fi
echo "HDFS cluster is reachable."

echo "=== [2/3] Provisioning HDFS Lake Layers ==="
"${SCRIPT_DIR}/directories.sh"

echo "=== [3/3] Testing Canary Write / Read across layers ==="
CANARY_FILE="/tmp/canary_$(date +%s).tmp"
echo "canary_token_$(date +%s)" > "${CANARY_FILE}"

for layer in raw processed curated analytics quarantine; do
    TEST_DST="/music_project/${layer}/.canary_test"
    hdfs dfs -put -f "${CANARY_FILE}" "${TEST_DST}"
    CANARY_CONTENT=$(hdfs dfs -cat "${TEST_DST}")
    ORIGINAL_CONTENT=$(cat "${CANARY_FILE}")
    if [ "${CANARY_CONTENT}" != "${ORIGINAL_CONTENT}" ]; then
        echo "ERROR: Canary check failed for layer ${layer}"
        rm -f "${CANARY_FILE}"
        exit 1
    fi
    hdfs dfs -rm -skipTrash "${TEST_DST}" >/dev/null 2>&1
    echo "Layer verified: /music_project/${layer} [READ/WRITE OK]"
done

rm -f "${CANARY_FILE}"
echo ""
echo "HDFS Storage Architecture verification PASSED."
