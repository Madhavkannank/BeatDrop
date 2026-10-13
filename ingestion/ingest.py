#!/usr/bin/env python3
"""
Main Ingestion Driver for Music Analytics Platform
Coordinates validation, quarantine dispatch, HDFS landing, and audit metrics.
"""

import os
import sys
import yaml
import json
import logging
import subprocess
from datetime import datetime, timezone

from validator import DataValidator
from quarantine import QuarantineManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/ingestion.log", mode="a")
    ]
)
logger = logging.getLogger("IngestionPipeline")

def run_hdfs_cmd(cmd_list):
    res = subprocess.run(cmd_list, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"HDFS command failed ({' '.join(cmd_list)}): {res.stderr.strip()}")
    return res.stdout.strip()

def main():
    logger.info("Starting ingestion workflow...")
    os.makedirs("logs", exist_ok=True)
    os.makedirs("results", exist_ok=True)

    # 1. Load Configuration
    config_path = "config/application.yaml"
    if not os.path.exists(config_path):
        logger.error(f"Configuration file {config_path} not found.")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    raw_input_path = config["dataset"]["raw_input_path"]
    if not os.path.exists(raw_input_path):
        logger.error(f"Raw input dataset not found at {raw_input_path}")
        sys.exit(1)

    logger.info(f"Validating dataset from: {raw_input_path}")
    validator = DataValidator(config)
    
    # 2. Execute Validation
    try:
        valid_records, quarantine_raw, metrics = validator.process_file(raw_input_path)
    except Exception as e:
        logger.error(f"Validation failure: {e}", exc_info=True)
        sys.exit(2)

    logger.info(f"Validation finished. Total: {metrics['total_records']}, "
                f"Valid: {metrics['valid_records']}, "
                f"Quarantined: {metrics['invalid_records']}, "
                f"Duplicates: {metrics['duplicate_records']}, "
                f"Quality Score: {metrics['data_quality_score']}%")

    # 3. Check Quarantine Threshold
    max_quarantine_ratio = config.get("validation", {}).get("quarantine_threshold_ratio", 0.3)
    observed_ratio = metrics["invalid_records"] / max(metrics["total_records"], 1)
    if observed_ratio > max_quarantine_ratio:
        logger.error(f"Quarantine ratio {observed_ratio:.2f} exceeds threshold {max_quarantine_ratio:.2f}! Aborting.")
        sys.exit(3)

    # 4. Stage Local Files for HDFS Landing
    temp_dir = "results/staging"
    os.makedirs(temp_dir, exist_ok=True)
    processed_local = os.path.join(temp_dir, "tracks_processed.csv")
    quarantine_local = os.path.join(temp_dir, "tracks_quarantine.csv")

    # Write processed CSV (tab-delimited for optimal Pig / MapReduce / Hive ingestion)
    fieldnames = config["dataset"]["expected_columns"]
    import csv
    with open(processed_local, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        # No header in processed data lake layer to align with standard MapReduce/Pig/Hive text loaders
        writer.writerows(valid_records)

    # Write quarantine CSV
    formatted_quarantine = QuarantineManager.format_quarantine_records(quarantine_raw)
    QuarantineManager.write_quarantine_csv(formatted_quarantine, quarantine_local)

    # 5. Land onto HDFS
    hadoop_home = config["environment"].get("hadoop_home", "/home/maddy/opt/hadoop-3.5.0")
    hdfs_bin = os.path.join(hadoop_home, "bin", "hdfs")
    hdfs_raw_dir = config["hdfs"]["raw_dir"]
    hdfs_proc_dir = config["hdfs"]["processed_dir"]
    hdfs_quar_dir = config["hdfs"]["quarantine_dir"]

    logger.info("Landing raw source dataset into HDFS raw layer (immutable)...")
    run_hdfs_cmd([hdfs_bin, "dfs", "-put", "-f", raw_input_path, f"{hdfs_raw_dir}/music_tracks_raw.csv"])

    logger.info("Landing processed validated dataset into HDFS processed layer...")
    run_hdfs_cmd([hdfs_bin, "dfs", "-put", "-f", processed_local, f"{hdfs_proc_dir}/tracks_processed.tsv"])

    logger.info("Landing quarantined records into HDFS quarantine layer...")
    run_hdfs_cmd([hdfs_bin, "dfs", "-put", "-f", quarantine_local, f"{hdfs_quar_dir}/tracks_quarantine.csv"])

    # 6. Verify HDFS Destination Artifacts
    logger.info("Verifying HDFS landing artifacts...")
    for target in [
        f"{hdfs_raw_dir}/music_tracks_raw.csv",
        f"{hdfs_proc_dir}/tracks_processed.tsv",
        f"{hdfs_quar_dir}/tracks_quarantine.csv"
    ]:
        run_hdfs_cmd([hdfs_bin, "dfs", "-test", "-e", target])
        stat_out = run_hdfs_cmd([hdfs_bin, "dfs", "-stat", "%n - %b bytes", target])
        logger.info(f"Verified HDFS target: {stat_out}")

    # 7. Persist Ingestion Metrics
    metrics_path = "results/ingestion_metrics.json"
    metrics["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()
    metrics["hdfs_raw_path"] = f"{hdfs_raw_dir}/music_tracks_raw.csv"
    metrics["hdfs_processed_path"] = f"{hdfs_proc_dir}/tracks_processed.tsv"
    metrics["hdfs_quarantine_path"] = f"{hdfs_quar_dir}/tracks_quarantine.csv"

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Ingestion metrics written to {metrics_path}")
    logger.info("Ingestion phase completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
