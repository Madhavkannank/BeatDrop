#!/usr/bin/env python3
"""
Consolidated Observability & Data-Quality Report Generator
Aggregates logs, HDFS lake statistics, quarantine breakdowns, and analytics KPIs.
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timezone

def run_cmd(cmd_list):
    res = subprocess.run(cmd_list, capture_output=True, text=True)
    return res.stdout.strip()

def get_hdfs_dir_size(path):
    out = run_cmd(["hdfs", "dfs", "-count", "-q", "-h", "-v", path])
    # Extract du output
    du_out = run_cmd(["hdfs", "dfs", "-du", "-h", "-s", path])
    return du_out.split()[0] if du_out else "0 B"

def main():
    print("Generating comprehensive observability and data-quality report...")
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)

    # 1. Load Ingestion Metrics
    ingestion_file = os.path.join(results_dir, "ingestion_metrics.json")
    ingestion_data = {}
    if os.path.exists(ingestion_file):
        with open(ingestion_file, "r", encoding="utf-8") as f:
            ingestion_data = json.load(f)

    # 2. Analyze Quarantine Audit Breakdown
    quarantine_file = os.path.join(results_dir, "staging", "tracks_quarantine.csv")
    quarantine_reasons = {}
    if os.path.exists(quarantine_file):
        import csv
        with open(quarantine_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                reason = row.get("rejection_reason", "UNKNOWN")
                prefix = reason.split("_")[0] + "_" + reason.split("_")[1] if len(reason.split("_")) > 1 else reason
                quarantine_reasons[prefix] = quarantine_reasons.get(prefix, 0) + 1

    # 3. Inspect HDFS Layers
    layers = ["raw", "processed", "curated", "analytics", "quarantine"]
    hdfs_stats = {}
    for layer in layers:
        hdfs_path = f"/music_project/{layer}"
        size_info = run_cmd(["hdfs", "dfs", "-du", "-s", "-h", hdfs_path])
        hdfs_stats[hdfs_path] = size_info if size_info else "Empty"

    # 4. Load Pipeline Execution Report
    pipeline_file = os.path.join(results_dir, "pipeline_execution_report.json")
    pipeline_data = {}
    if os.path.exists(pipeline_file):
        with open(pipeline_file, "r", encoding="utf-8") as f:
            pipeline_data = json.load(f)

    # 5. Load Analytics Output Summaries
    genre_metrics_file = os.path.join(results_dir, "spark", "genre_metrics.json")
    genre_data = []
    if os.path.exists(genre_metrics_file):
        with open(genre_metrics_file, "r", encoding="utf-8") as f:
            genre_data = json.load(f)

    report = {
        "report_title": "Music Analytics Platform - Observability & Data Quality Audit",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_status": pipeline_data.get("status", "SUCCESS"),
        "total_runtime_seconds": pipeline_data.get("total_duration_seconds", 0),
        "data_quality": {
            "total_records_ingested": ingestion_data.get("total_records", 0),
            "valid_records_admitted": ingestion_data.get("valid_records", 0),
            "quarantined_records": ingestion_data.get("invalid_records", 0),
            "duplicate_records_dropped": ingestion_data.get("duplicate_records", 0),
            "null_records_detected": ingestion_data.get("null_records", 0),
            "data_quality_score_percent": ingestion_data.get("data_quality_score", 0.0),
            "quarantine_reasons_breakdown": quarantine_reasons
        },
        "hdfs_storage_lake": hdfs_stats,
        "analytics_kpis": {
            "total_genres_analyzed": len(genre_data),
            "top_popular_genre": genre_data[0]["genre"] if genre_data else "N/A",
            "top_popular_genre_avg_score": genre_data[0]["avg_popularity"] if genre_data else 0.0,
            "lowest_popular_genre": genre_data[-1]["genre"] if genre_data else "N/A",
            "lowest_popular_genre_avg_score": genre_data[-1]["avg_popularity"] if genre_data else 0.0
        }
    }

    # Save JSON report
    report_json_path = os.path.join(results_dir, "data_quality_report.json")
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Save Markdown report
    report_md_path = os.path.join(results_dir, "data_quality_report.md")
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(f"# Data Quality & Observability Audit Report\n\n")
        f.write(f"**Generated:** {report['generated_at']}\n")
        f.write(f"**Pipeline Status:** {report['pipeline_status']} ({report['total_runtime_seconds']}s)\n\n")
        f.write("## 1. Data Quality & Integrity Metrics\n\n")
        f.write(f"- **Total Ingested Records:** {report['data_quality']['total_records_ingested']}\n")
        f.write(f"- **Valid Admitted Records:** {report['data_quality']['valid_records_admitted']}\n")
        f.write(f"- **Quarantined Records:** {report['data_quality']['quarantined_records']}\n")
        f.write(f"- **Duplicate Records:** {report['data_quality']['duplicate_records_dropped']}\n")
        f.write(f"- **Null Records:** {report['data_quality']['null_records_detected']}\n")
        f.write(f"- **Data Quality Score:** **{report['data_quality']['data_quality_score_percent']}%**\n\n")
        f.write("### Quarantine Rejection Breakdown\n\n")
        f.write("| Anomaly Category | Rejected Count |\n| :--- | :--- |\n")
        for k, v in quarantine_reasons.items():
            f.write(f"| `{k}` | {v} |\n")
        f.write("\n## 2. HDFS Lake Storage Inventory\n\n")
        f.write("| HDFS Layer Path | Size on Disk |\n| :--- | :--- |\n")
        for k, v in hdfs_stats.items():
            f.write(f"| `{k}` | `{v}` |\n")
        f.write("\n## 3. High-Level Analytics KPIs\n\n")
        f.write(f"- **Total Genres Evaluated:** {report['analytics_kpis']['total_genres_analyzed']}\n")
        f.write(f"- **Highest Rated Genre:** `{report['analytics_kpis']['top_popular_genre']}` ({report['analytics_kpis']['top_popular_genre_avg_score']}/100)\n")
        f.write(f"- **Lowest Rated Genre:** `{report['analytics_kpis']['lowest_popular_genre']}` ({report['analytics_kpis']['lowest_popular_genre_avg_score']}/100)\n")

    print(f"Observability reports successfully written to:")
    print(f"  - {report_json_path}")
    print(f"  - {report_md_path}")

if __name__ == "__main__":
    main()
