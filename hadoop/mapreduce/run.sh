#!/usr/bin/env bash
# ==============================================================================
# Native Hadoop MapReduce Runner
# Compiles, packages, and executes ArtistAnalyticsJob on HDFS cluster
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

export JAVA_HOME="${JAVA_HOME:-/home/maddy/opt/jdk-17}"
export HADOOP_HOME="${HADOOP_HOME:-/home/maddy/opt/hadoop-3.5.0}"
export PATH="${JAVA_HOME}/bin:${HADOOP_HOME}/bin:${PATH}"

BUILD_DIR="${SCRIPT_DIR}/build"
SRC_DIR="${SCRIPT_DIR}/src"
JAR_FILE="${BUILD_DIR}/ArtistAnalytics.jar"

HDFS_INPUT="/music_project/processed/tracks_processed.tsv"
HDFS_OUTPUT="/music_project/analytics/mapreduce_artist_summary"

echo "=== [1/5] Compiling Java MapReduce Source ==="
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

HADOOP_CP=$(hadoop classpath --glob)
javac -cp "${HADOOP_CP}" -d "${BUILD_DIR}" "${SRC_DIR}/ArtistAnalyticsJob.java"

echo "=== [2/5] Packaging into JAR ==="
jar -cvf "${JAR_FILE}" -C "${BUILD_DIR}" com/

echo "=== [3/5] Preparing HDFS Output Directory (Idempotent) ==="
hdfs dfs -rm -r -skipTrash "${HDFS_OUTPUT}" 2>/dev/null || true

echo "=== [4/5] Executing MapReduce Job on Hadoop ==="
hadoop jar "${JAR_FILE}" com.music.analytics.ArtistAnalyticsJob "${HDFS_INPUT}" "${HDFS_OUTPUT}"

echo "=== [5/5] Verifying MapReduce Outputs on HDFS ==="
hdfs dfs -test -e "${HDFS_OUTPUT}/_SUCCESS"
echo "Sample MapReduce Results (Artist | Count | AvgPop | MinPop | MaxPop | AvgDurSec):"
hdfs dfs -cat "${HDFS_OUTPUT}/part-r-00000" 2>/dev/null | head -n 10 || true

mkdir -p "${PROJECT_ROOT}/results/mapreduce"
hdfs dfs -getmerge "${HDFS_OUTPUT}" "${PROJECT_ROOT}/results/mapreduce/artist_summary.tsv"
echo "MapReduce outputs saved locally to results/mapreduce/artist_summary.tsv"

echo "Hadoop MapReduce phase completed successfully."
