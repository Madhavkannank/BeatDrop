#!/usr/bin/env python3
"""
CLI Tool: Ingest Single Song via Groq and Optionally Trigger Big Data Pipeline
"""

import os
import sys
import csv
import argparse
import subprocess
import yaml

# Add ingestion to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "ingestion"))

from groq_metadata import fetch_song_metadata
from catalog_search import find_existing_track
from validator import DataValidator

def append_track_to_dataset(track_record: dict, dataset_path: str, expected_cols: list) -> bool:
    os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
    file_exists = os.path.exists(dataset_path)

    # Check for duplicate track_id in dataset
    if file_exists:
        with open(dataset_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("track_id") == track_record["track_id"]:
                    print(f"Warning: Track ID {track_record['track_id']} already exists in {dataset_path}. Updating row...")
                    return False

    with open(dataset_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=expected_cols)
        if not file_exists or os.path.getsize(dataset_path) == 0:
            writer.writeheader()
        
        # Prepare row matching expected columns
        row = {col: track_record.get(col, "") for col in expected_cols}
        writer.writerow(row)
    
    print(f"Appended '{track_record['track_name']}' by {track_record['artist_name']} to {dataset_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Add a song via Groq AI metadata extraction.")
    parser.add_argument("--song", required=True, help="Song title (e.g. 'Hotel California')")
    parser.add_argument("--artist", default=None, help="Artist name hint (e.g. 'Eagles')")
    parser.add_argument("--api-key", default=None, help="Groq API Key (or set GROQ_API_KEY)")
    parser.add_argument("--run-pipeline", action="store_true", help="Execute full big data pipeline after adding track")
    args = parser.parse_args()

    # 1. Check if song already exists in database
    existing = find_existing_track(args.song, args.artist)
    already_in_db = False

    if existing:
        print(f"=== [1/4] Found existing track in database catalog for '{args.song}'! ===")
        raw_metadata = existing
        already_in_db = True
    else:
        print(f"=== [1/4] Song not in catalog. Fetching metadata from Groq for '{args.song}'... ===")
        try:
            raw_metadata = fetch_song_metadata(args.song, args.artist, args.api_key)
        except Exception as e:
            print(f"Error fetching metadata: {e}", file=sys.stderr)
            sys.exit(1)

    print("Metadata retrieved:")
    for k, v in raw_metadata.items():
        if not k.startswith("_"):
            print(f"  {k:15}: {v}")

    # 2. Validate against schema contract
    print("\n=== [2/4] Validating schema contract... ===")
    config_path = os.path.join(PROJECT_ROOT, "config", "application.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    validator = DataValidator(config)
    row_strings = {k: str(v) for k, v in raw_metadata.items() if not k.startswith("_")}
    is_valid, reason, cleaned = validator.validate_record(row_strings)

    if not is_valid:
        print(f"Validation FAILED: {reason}", file=sys.stderr)
        sys.exit(2)
    print("Schema contract validation: PASSED")

    # 3. Append to raw dataset if new
    print("\n=== [3/4] Dataset Staging... ===")
    dataset_path = os.path.join(PROJECT_ROOT, config["dataset"]["raw_input_path"])
    expected_cols = config["dataset"]["expected_columns"]
    if not already_in_db:
        append_track_to_dataset(cleaned, dataset_path, expected_cols)
    else:
        print(f"Track '{cleaned['track_name']}' is already in catalog dataset. Skipping duplicate append.")

    # 4. Optionally Run Pipeline
    if args.run_pipeline:
        print("\n=== [4/4] Executing Full Big Data Pipeline... ===")
        pipeline_script = os.path.join(PROJECT_ROOT, "pipeline", "run_pipeline.sh")
        res = subprocess.run([pipeline_script], cwd=PROJECT_ROOT)
        if res.returncode != 0:
            print("Pipeline execution failed!", file=sys.stderr)
            sys.exit(res.returncode)

        # Sync dashboard data
        sync_script = os.path.join(PROJECT_ROOT, "scripts", "prepare_dashboard_data.py")
        subprocess.run(["python3", sync_script], cwd=PROJECT_ROOT)
        print("Dashboard data synchronized.")

    print("\nSong ingestion completed successfully.")

if __name__ == "__main__":
    main()
