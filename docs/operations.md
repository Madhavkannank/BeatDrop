# Operations Guide: Music Analytics Platform

This guide outlines operational procedures for managing, executing, and monitoring the Music Analytics Platform.

---

## 1. Quick Start Commands

The project includes a unified `Makefile` for routine operations:

```bash
# 1. Start cluster services and verify engine health
make bootstrap

# 2. Run runtime healthcheck
make healthcheck

# 3. Execute the automated unit test suite
make test

# 4. Run the full end-to-end Big Data pipeline
make pipeline

# 5. Clean local temporary build files and staging folders
make clean

# 6. Launch the local interactive analytics dashboard
make dashboard
```

---

## 2. Managing Hadoop & YARN Daemons

Services run via systemd user units to prevent sandbox session termination:

```bash
# Check service status
systemctl --user status hadoop-namenode
systemctl --user status hadoop-datanode
systemctl --user status hadoop-resourcemanager
systemctl --user status hadoop-nodemanager

# Stop all services
./scripts/reset_environment.sh

# Restart all services
./scripts/bootstrap.sh
```

---

## 3. Data Lake Management via HDFS CLI

```bash
# List all data lake layers
hdfs dfs -ls /music_project/

# Inspect processed clean dataset
hdfs dfs -ls /music_project/processed/

# View sample of quarantined records
hdfs dfs -cat /music_project/quarantine/tracks_quarantine.csv | head -n 10

# View MapReduce output on HDFS
hdfs dfs -cat /music_project/analytics/mapreduce_artist_summary/part-r-00000 | head -n 10

# Inspect Spark Parquet outputs on HDFS
hdfs dfs -ls /music_project/analytics/*.parquet
```

---

## 4. Pipeline Observability & Logs

- **Main Pipeline Log**: `logs/pipeline.log`
- **Ingestion Audit Log**: `logs/ingestion.log`
- **Data Quality Audit**: `results/data_quality_report.md`
- **Execution Report**: `results/pipeline_execution_report.json`
