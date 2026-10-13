#!/usr/bin/env bash
# ==============================================================================
# Bootstrap Script for Music Analytics Platform
# Sets up environment variables, ensures daemons are active, runs health check
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== [1/4] Configuring Environment Variables ==="
export JAVA_HOME="${JAVA_HOME:-/home/maddy/opt/jdk-17}"
export HADOOP_HOME="${HADOOP_HOME:-/home/maddy/opt/hadoop-3.5.0}"
export SPARK_HOME="${SPARK_HOME:-/home/maddy/opt/spark-3.5.3}"
export HIVE_HOME="${HIVE_HOME:-/home/maddy/opt/hive-4.0.0}"
export PIG_HOME="${PIG_HOME:-/home/maddy/opt/pig-0.17.0}"
export HADOOP_CONF_DIR="${HADOOP_HOME}/etc/hadoop"

export PATH="${JAVA_HOME}/bin:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin:${SPARK_HOME}/bin:${HIVE_HOME}/bin:${PIG_HOME}/bin:${PATH}"

echo "=== [2/4] Checking and Starting Hadoop / YARN Services ==="
# Check NameNode
if ! systemctl --user is-active --quiet hadoop-namenode 2>/dev/null; then
    echo "Starting HDFS NameNode and DataNode via systemd-run --user..."
    systemd-run --user --unit=hadoop-namenode /bin/bash -c "export JAVA_HOME=${JAVA_HOME}; export HADOOP_HOME=${HADOOP_HOME}; exec \${HADOOP_HOME}/bin/hdfs namenode"
    systemd-run --user --unit=hadoop-datanode /bin/bash -c "export JAVA_HOME=${JAVA_HOME}; export HADOOP_HOME=${HADOOP_HOME}; exec \${HADOOP_HOME}/bin/hdfs datanode"
    sleep 3
else
    echo "HDFS cluster is already active."
fi

# Check YARN
if ! systemctl --user is-active --quiet hadoop-resourcemanager 2>/dev/null; then
    echo "Starting YARN ResourceManager and NodeManager via systemd-run --user..."
    systemd-run --user --unit=hadoop-resourcemanager /bin/bash -c "export JAVA_HOME=${JAVA_HOME}; export HADOOP_HOME=${HADOOP_HOME}; exec \${HADOOP_HOME}/bin/yarn resourcemanager"
    systemd-run --user --unit=hadoop-nodemanager /bin/bash -c "export JAVA_HOME=${JAVA_HOME}; export HADOOP_HOME=${HADOOP_HOME}; exec \${HADOOP_HOME}/bin/yarn nodemanager"
    sleep 3
else
    echo "YARN cluster is already active."
fi

echo "=== [3/4] Ensuring Project HDFS Directories ==="
hdfs dfs -mkdir -p /music_project/raw
hdfs dfs -mkdir -p /music_project/processed
hdfs dfs -mkdir -p /music_project/curated
hdfs dfs -mkdir -p /music_project/analytics
hdfs dfs -mkdir -p /music_project/quarantine

echo "=== [4/4] Executing Healthcheck ==="
"${PROJECT_ROOT}/scripts/healthcheck.sh"

echo "Bootstrap completed successfully."
