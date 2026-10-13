#!/usr/bin/env bash
# ==============================================================================
# Healthcheck Script for Music Analytics Platform
# Verifies actual runtime health (not just executable existence)
# ==============================================================================

set -u

# Source environment variables if available
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment overrides
export JAVA_HOME="${JAVA_HOME:-/home/maddy/opt/jdk-17}"
export HADOOP_HOME="${HADOOP_HOME:-/home/maddy/opt/hadoop-3.5.0}"
export SPARK_HOME="${SPARK_HOME:-/home/maddy/opt/spark-3.5.3}"
export HIVE_HOME="${HIVE_HOME:-/home/maddy/opt/hive-4.0.0}"
export PIG_HOME="${PIG_HOME:-/home/maddy/opt/pig-0.17.0}"

export PATH="${JAVA_HOME}/bin:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin:${SPARK_HOME}/bin:${HIVE_HOME}/bin:${PIG_HOME}/bin:${PATH}"

FAILURES=0

check_service() {
    local name="$1"
    local cmd="$2"
    printf "%-30s ... " "$name"
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "\033[0;32m[PASS]\033[0m"
    else
        echo -e "\033[0;31m[FAIL]\033[0m"
        FAILURES=$((FAILURES + 1))
    fi
}

echo "=========================================================="
echo "          MUSIC ANALYTICS PLATFORM HEALTHCHECK            "
echo "=========================================================="
echo "Date: $(date)"
echo "Host: $(hostname)"
echo "----------------------------------------------------------"

check_service "Java 17 Runtime" "java -version"
check_service "Python 3 Runtime" "python3 -c 'import sys; assert sys.version_info >= (3, 8)'"
check_service "Python PyYAML Library" "python3 -c 'import yaml'"
check_service "Hadoop CLI" "hadoop version"
check_service "HDFS NameNode & Cluster" "hdfs dfsadmin -report | grep -E 'Live datanodes \([1-9]'"
check_service "HDFS Filesystem I/O" "hdfs dfs -ls /"
check_service "YARN Cluster Nodes" "yarn node -list | grep -E 'Total Nodes:[1-9]'"
check_service "Apache Spark Engine" "spark-submit --version"
check_service "Apache Hive Warehouse" "hive --version"
check_service "Apache Pig Engine" "pig -version"

echo "----------------------------------------------------------"
if [ "$FAILURES" -eq 0 ]; then
    echo -e "Overall Status: \033[0;32mALL HEALTH CHECKS PASSED\033[0m"
    exit 0
else
    echo -e "Overall Status: \033[0;33m${FAILURES} COMPONENT(S) FAILED / PENDING INSTALLATION\033[0m"
    exit "$FAILURES"
fi
