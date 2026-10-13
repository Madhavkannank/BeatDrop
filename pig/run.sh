#!/usr/bin/env bash
# ==============================================================================
# Apache Pig ETL Runner
# Executes pig/clean_music.pig on HDFS cluster
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

export JAVA_HOME="${JAVA_HOME:-/home/maddy/opt/jdk-17}"
export HADOOP_HOME="${HADOOP_HOME:-/home/maddy/opt/hadoop-3.5.0}"
export PIG_HOME="${PIG_HOME:-/home/maddy/opt/pig-0.17.0}"
export HADOOP_CONF_DIR="${HADOOP_HOME}/etc/hadoop"
export PATH="${JAVA_HOME}/bin:${HADOOP_HOME}/bin:${PIG_HOME}/bin:${PATH}"

export PIG_CLASSPATH="${HADOOP_CONF_DIR}:$(hadoop classpath)"
export PIG_OPTS="-Djava.security.manager=allow --add-opens java.base/java.lang=ALL-UNNAMED --add-opens java.base/java.util=ALL-UNNAMED --add-opens java.base/java.net=ALL-UNNAMED --add-opens java.base/java.io=ALL-UNNAMED --add-opens java.base/java.lang.reflect=ALL-UNNAMED"

echo "=== [1/4] Preparing HDFS Destination Paths (Idempotent) ==="
hdfs dfs -rm -r -skipTrash /music_project/curated/pig_curated_tracks 2>/dev/null || true
hdfs dfs -rm -r -skipTrash /music_project/analytics/pig_genre_summary 2>/dev/null || true

echo "=== [2/4] Executing Apache Pig ETL Job ==="
PIG_SCRIPT="${SCRIPT_DIR}/clean_music.pig"
# Run Pig with Hadoop MapReduce execution mode
pig -x mapreduce -f "${PIG_SCRIPT}"

echo "=== [3/4] Verifying Pig Outputs on HDFS ==="
hdfs dfs -test -e /music_project/curated/pig_curated_tracks
hdfs dfs -test -e /music_project/analytics/pig_genre_summary

echo "Curated tracks sample:"
hdfs dfs -cat /music_project/curated/pig_curated_tracks/part* 2>/dev/null | head -n 5 || true

echo ""
echo "Genre summary output:"
hdfs dfs -cat /music_project/analytics/pig_genre_summary/part* 2>/dev/null | head -n 10 || true

echo "=== [4/4] Persisting Pig Results to Local Results Directory ==="
mkdir -p "${PROJECT_ROOT}/results/pig"
hdfs dfs -getmerge /music_project/analytics/pig_genre_summary "${PROJECT_ROOT}/results/pig/genre_summary.tsv"
echo "Pig results saved locally to results/pig/genre_summary.tsv"

echo "Apache Pig ETL phase completed successfully."
