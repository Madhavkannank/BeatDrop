#!/usr/bin/env bash
# ==============================================================================
# Apache Hive Warehouse & Analytics Runner
# Provisions database, tables, views, and executes analytical queries via Beeline
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

export JAVA_HOME="${JAVA_HOME:-/home/maddy/opt/jdk-17}"
export HADOOP_HOME="${HADOOP_HOME:-/home/maddy/opt/hadoop-3.5.0}"
export HIVE_HOME="${HIVE_HOME:-/home/maddy/opt/hive-4.0.0}"
export HIVE_CONF_DIR="${HIVE_HOME}/conf"
export PATH="${JAVA_HOME}/bin:${HADOOP_HOME}/bin:${HIVE_HOME}/bin:${PATH}"

export HADOOP_CLIENT_OPTS="${HADOOP_CLIENT_OPTS:-} --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.util.concurrent=ALL-UNNAMED --add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.nio=ALL-UNNAMED --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED"

# Ensure metastore lock is clean
rm -f "${HIVE_HOME}/metastore_db/db.lck" "${HIVE_HOME}/metastore_db/dbex.lck" 2>/dev/null || true

# Ensure HDFS warehouse path
hdfs dfs -mkdir -p /user/hive/warehouse 2>/dev/null || true
hdfs dfs -chmod 777 /user/hive/warehouse 2>/dev/null || true

RESULTS_DIR="${PROJECT_ROOT}/results/hive"
mkdir -p "${RESULTS_DIR}"

HIVE_CMD="beeline -u jdbc:hive2:// --silent=false"

echo "=== [1/4] Provisioning Hive Database ==="
$HIVE_CMD -f "${SCRIPT_DIR}/database.hql"

echo "=== [2/4] Defining External and Managed Tables ==="
$HIVE_CMD -f "${SCRIPT_DIR}/tables.hql"

echo "=== [3/4] Creating Business Analytical Views ==="
$HIVE_CMD -f "${SCRIPT_DIR}/views.hql"

echo "=== [4/4] Executing Analytical Queries ==="
$HIVE_CMD -f "${SCRIPT_DIR}/analytics.hql" | tee "${RESULTS_DIR}/analytics_output.txt"

echo "Hive analytics results saved to ${RESULTS_DIR}/analytics_output.txt"
echo "Apache Hive Warehouse phase completed successfully."
