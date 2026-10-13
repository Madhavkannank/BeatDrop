#!/usr/bin/env bash
# ==============================================================================
# Interactive Demonstration Script for Examiners & Evaluators
# Demonstrates every live component of the Music Analytics Platform
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "======================================================================"
echo "      MUSIC ANALYTICS PLATFORM - LIVE EXAMINER DEMONSTRATION          "
echo "======================================================================"
echo ""

echo ">>> [DEMO STEP 1] Verifying System Health & Engines..."
"${PROJECT_ROOT}/scripts/healthcheck.sh"
echo ""

echo ">>> [DEMO STEP 2] Executing Automated Test Suite..."
python3 -m unittest discover -s "${PROJECT_ROOT}/tests" -p "test_*.py" -v
echo ""

echo ">>> [DEMO STEP 3] Inspecting 5-Layer HDFS Data Lake..."
hdfs dfs -ls /music_project/
echo ""

echo ">>> [DEMO STEP 4] Demonstrating Quarantine Audit Trail (Anomalous Records)..."
hdfs dfs -cat /music_project/quarantine/tracks_quarantine.csv 2>/dev/null | head -n 6 || true
echo ""

echo ">>> [DEMO STEP 5] Demonstrating Apache Pig ETL Outputs (Genre Aggregates)..."
cat "${PROJECT_ROOT}/results/pig/genre_summary.tsv" | head -n 5
echo ""

echo ">>> [DEMO STEP 6] Demonstrating Native Hadoop MapReduce (Top Artists by Popularity)..."
sort -k3,3nr "${PROJECT_ROOT}/results/mapreduce/artist_summary.tsv" | head -n 5
echo ""

echo ">>> [DEMO STEP 7] Demonstrating PySpark Window Analytics (Top 3 Hits per Genre)..."
cat "${PROJECT_ROOT}/results/spark/top_tracks_per_genre.json" | head -n 25
echo ""

echo ">>> [DEMO STEP 8] Demonstrating Live Analytics Dashboard..."
echo "To explore the interactive web dashboard, run:"
echo "    make dashboard"
echo "and open http://localhost:8080 in your web browser."
echo ""
echo "Demonstration script completed successfully."
