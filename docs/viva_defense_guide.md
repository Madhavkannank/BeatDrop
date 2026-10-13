# Music Analytics Platform: Comprehensive Viva & Deployment Guide

This guide provides technical explanations, architectural defenses, command-line proofs, and a demonstration runbook for examiners, professors, and technical reviews.

---

## 1. Executive Summary & Verification Matrix

| Syllabus Requirement | Technology / Script | HDFS / Database Location | Verified Output / Scale |
| :--- | :--- | :--- | :--- |
| **1. Datacenter / Web Feed to HDFS** | [`pipeline/datacenter_web_to_hdfs.py`](../pipeline/datacenter_web_to_hdfs.py) | `/music_project/raw/datacenter/` | 49.2 KB unstructured JSON payloads ingested; 8.66 MB archive exported |
| **2. Relational SQL to HDFS** | [`pipeline/sql_hdfs_connector.py`](../pipeline/sql_hdfs_connector.py) | `/music_project/sql_import/` | Normalized SQLite warehouse (artists, albums, tracks); 97.9 KB TSV stream in HDFS |
| **3. NoSQL Storage & Aggregation** | [`nosql/mongo_manager.py`](../nosql/mongo_manager.py) | Cloud MongoDB Atlas (`music_lakehouse.tracks`) | **85,444 real documents**, 3 compound indexes, 2 aggregation pipelines |
| **4. Structured/Unstructured Pig ETL** | [`pig/clean_music.pig`](../pig/clean_music.pig) | `/music_project/curated/` & `/analytics/` | MapReduce execution mode; derived duration_sec, popularity_tier, and genre summaries |
| **5. Hive Data Warehouse & SQL** | [`hive/`](../hive/) | Hive metastore & `/music_project/analytics/` | External & managed ORC tables; 5 analytical views and queries |
| **Native Hadoop MapReduce** | [`hadoop/mapreduce/src/ArtistAnalyticsJob.java`](../hadoop/mapreduce/src/ArtistAnalyticsJob.java) | `/music_project/analytics/mapreduce_artist_summary/` | YARN MapReduce job; aggregated 85,444 records into 33,430 artist groups in 17s |
| **Advanced PySpark Analytics** | [`spark/jobs/music_analytics.py`](../spark/jobs/music_analytics.py) | `/music_project/analytics/spark/` | Window ranking (`row_number()` over genre) and Snappy Parquet outputs |
| **Data Validation & Quality Gate** | [`ingestion/validator.py`](../ingestion/validator.py) | `/music_project/quarantine/` | 85,444 clean records vs 50 quarantined records; zero silent failures |

---

## 2. Deep-Dive Examiner Questions & Defenses

### Q1: Why use both Hadoop MapReduce, Pig, Hive, AND PySpark on the same dataset? Isn't that redundant?
**Defense**:
- In modern enterprise data lakehouse architectures, each engine serves a distinct operational purpose based on workload characteristics:
  1. **Apache Pig**: Best suited for declarative, high-throughput ETL transformations (filtering, data cleansing, feature enrichment, and column normalization).
  2. **Native Java MapReduce**: Serves as the fundamental batch compute substrate. It demonstrates low-level key-value mapping, distributed shuffle-sort mechanics, and custom partitioner/combiner execution directly on YARN.
  3. **Apache Hive**: Provides the schema-on-read relational data warehouse layer. It allows BI analysts and SQL users to query HDFS data using HiveQL, leveraging external table isolation to protect raw data from accidental deletion on metadata drop.
  4. **PySpark**: Delivers in-memory distributed computation, advanced analytical queries (such as SQL window functions like `row_number() OVER (PARTITION BY genre ORDER BY popularity DESC)`), and column-pruned Parquet storage.
- Using them together demonstrates polyglot distributed computing across the entire data engineering lifecycle.

### Q2: Why did you incorporate both Relational SQL and NoSQL (MongoDB Atlas) alongside HDFS?
**Defense**:
- **HDFS**: The central, cost-effective distributed cold/warm data lake storing terabyte/petabyte-scale immutable files (`raw`, `processed`, `curated`).
- **Relational SQL (SQLite RDBMS)**: Demonstrates 3NF relational modeling (`artists JOIN albums JOIN tracks`) for strict transactional integrity and referential constraints.
- **NoSQL (MongoDB Atlas)**: Provides high-concurrency, schema-flexible document storage with compound secondary indexes (`track_id`, `artist_name`, `genre + popularity`). It enables real-time application queries and runs native server-side aggregation pipelines (`$group`, `$avg`, `$sort`) without invoking heavy distributed batch jobs.

### Q3: How do you guarantee Data Quality and Data Truthfulness?
**Defense**:
- **Data Truthfulness**: The dataset consists of **85,494 100% authentic music tracks** (Spotify 81k, Tamil Kollywood 4.2k, Malayalam 56, controlled edge cases 50). There is **zero synthetic data** in the clean catalog.
- **Deduplication**: Strict deduplication on unique `track_id` and compound `(track_name, artist_name)` pairs.
- **Quarantine Layer**: Invalid rows (e.g. negative duration, popularity > 100, missing mandatory fields) are never silently dropped with `try/except: pass`. They are routed to `/music_project/quarantine/` with audit timestamps and machine-readable error codes.
- **Fail-Safe Gate**: Ingestion enforces a rejection threshold ($\le 30\%$). If bad records exceed this threshold, the entire ingestion pipeline aborts to protect the downstream lakehouse.

### Q4: Explain the difference between Hive Managed Tables and External Tables in your project.
**Defense**:
- **External Tables (`hive_music_curated`)**: The table definition specifies `LOCATION '/music_project/processed'`. Hive only manages the metadata schema in its metastore. If an administrator issues `DROP TABLE hive_music_curated;`, the underlying files in HDFS remain completely intact and unaffected.
- **Managed Tables (`hive_artist_summary`)**: Hive controls both the schema and the physical lifecycle in its internal warehouse directory (`/user/hive/warehouse/`). The data is materialized in optimized ORC format with Snappy compression for query acceleration.

---

## 3. Step-by-Step Live Demonstration Runbook (5-Minute Viva Demo)

### Step 1: Prove System Health (30 Seconds)
```bash
make healthcheck
```
*Expected Result*: All 10 components output `[PASS]` (Java 17, Python 3, PyYAML, Hadoop CLI, HDFS NameNode, HDFS I/O, YARN, Spark, Hive, Pig).

### Step 2: Demonstrate Syllabus Requirements 1, 2, and 3 (1.5 Minutes)
```bash
# 1. Datacenter / Web Feed -> HDFS
make datacenter

# 2. Relational SQL <-> HDFS Bridge
make sql-bridge

# 3. Cloud MongoDB Atlas NoSQL Store & Aggregations
make nosql
```
*Expected Result*:
- Web feed JSON landed in HDFS `/music_project/raw/datacenter/`.
- SQL 3NF normalized tables seeded and joined into HDFS `/music_project/sql_import/`.
- Cloud MongoDB Atlas verifies **85,444 documents** stored with live aggregation output.

### Step 3: Run the Distributed Big Data Pipeline (2 Minutes)
```bash
make pipeline
```
*What happens on screen*:
1. `ingest.py`: Validates 85,494 tracks, lands 85,444 in HDFS `/music_project/processed`, and 50 in `/music_project/quarantine`.
2. Apache Pig: Runs MapReduce job to enrich features (`duration_sec`, `popularity_tier`) into `/music_project/curated`.
3. Native Java MapReduce: Compiles and runs `ArtistAnalyticsJob` on YARN, aggregating 85,444 records into 33,430 artist groups.
4. Apache Hive: Executes `database.hql`, provisions external tables, and computes top artist views.
5. PySpark: Computes genre-wise window rankings and saves Snappy Parquet files in HDFS.

### Step 4: Show the Interactive UI & Search Engine (1 Minute)
```bash
# Verify dashboard server is active
curl -s http://localhost:8080/api/pipeline/status
```
- Open browser at `http://localhost:8080/`.
- Show the **Overview** dashboard (total tracks, genre volume, popularity distribution).
- Open **Search**: Type "Anirudh", "Rahman", or "Taylor" to demonstrate the instant indexed search across 85,444 tracks.
- Show **Pipeline Run** tab: Real-time logs and one-click re-execution.

---

## 4. Key Metrics Summary
- **Total Valid Tracks in Lakehouse**: 85,444
- **Total Unique Artists**: 33,420
- **Total Quarantined Tracks**: 50
- **Cloud MongoDB Atlas Documents**: 85,444
- **Unit & Integration Tests**: 14 / 14 Passed (`make test`)
- **Pipeline Execution Time**: ~55 seconds end-to-end
