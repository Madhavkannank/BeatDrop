#!/usr/bin/env bash
# ==============================================================================
# PySpark Analytics Runner
# Executes spark/jobs/music_analytics.py on Apache Spark 3.5.3
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

export JAVA_HOME="${JAVA_HOME:-/home/maddy/opt/jdk-17}"
export HADOOP_HOME="${HADOOP_HOME:-/home/maddy/opt/hadoop-3.5.0}"
export SPARK_HOME="${SPARK_HOME:-/home/maddy/opt/spark-3.5.3}"
export PATH="${JAVA_HOME}/bin:${HADOOP_HOME}/bin:${SPARK_HOME}/bin:${PATH}"

export PYSPARK_PYTHON="$(which python3)"
export PYSPARK_DRIVER_PYTHON="$(which python3)"

export SPARK_SUBMIT_OPTS="--add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.invoke=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.nio=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.util.concurrent=ALL-UNNAMED --add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED --add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/sun.nio.cs=ALL-UNNAMED --add-opens=java.base/sun.security.action=ALL-UNNAMED --add-opens=java.base/sun.util.calendar=ALL-UNNAMED"

echo "=== [1/3] Executing PySpark Analytics Job via spark-submit ==="
spark-submit \
  --master local[*] \
  --name "MusicAnalyticsPySpark" \
  --driver-java-options "${SPARK_SUBMIT_OPTS}" \
  "${SCRIPT_DIR}/jobs/music_analytics.py"

echo "=== [2/3] Verifying HDFS Parquet Outputs ==="
hdfs dfs -ls /music_project/analytics/spark_genre_metrics.parquet
hdfs dfs -ls /music_project/analytics/spark_ranked_tracks.parquet

echo "=== [3/3] Verifying Local Results Files ==="
ls -lh "${PROJECT_ROOT}/results/spark/"

echo "PySpark Analytics phase completed successfully."
