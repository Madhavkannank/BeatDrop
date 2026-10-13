#!/usr/bin/env python3
"""
Prepares and synchronizes real pipeline result files for the frontend dashboard.
Ensures zero hardcoded numbers: everything comes directly from real engine outputs.
"""

import os
import shutil
import json

def main():
    dashboard_data_dir = "dashboard/data"
    os.makedirs(dashboard_data_dir, exist_ok=True)

    sources = [
        ("results/ingestion_metrics.json", f"{dashboard_data_dir}/ingestion_metrics.json"),
        ("results/data_quality_report.json", f"{dashboard_data_dir}/data_quality_report.json"),
        ("results/spark/genre_metrics.json", f"{dashboard_data_dir}/genre_metrics.json"),
        ("results/spark/top_artists.json", f"{dashboard_data_dir}/top_artists.json"),
        ("results/spark/top_tracks_per_genre.json", f"{dashboard_data_dir}/top_tracks_per_genre.json"),
        ("results/pipeline_execution_report.json", f"{dashboard_data_dir}/pipeline_execution_report.json"),
    ]

    for src, dst in sources:
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Synced: {src} -> {dst}")
        else:
            print(f"Warning: source file {src} not found.")

    print("Dashboard data synchronization complete.")

if __name__ == "__main__":
    main()
