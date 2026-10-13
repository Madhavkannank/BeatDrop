# Music Track & Popularity Analytics Platform

An enterprise-grade, distributed Big Data engineering platform built on **Hadoop HDFS, Native Java MapReduce, Apache Pig, Apache Hive, and PySpark**.

---

## 1. Project Overview
The Music Track & Popularity Analytics Platform provides an end-to-end distributed Big Data architecture to ingest, validate, store, enrich, and analyze music metadata across the Hadoop ecosystem, relational databases, and Cloud NoSQL lakehouses. It implements a 5-layer HDFS data lakehouse architecture and executes authentic analytics across multiple distributed computing frameworks.

## 2. Problem Statement
Modern music streaming catalogs comprise tens of thousands of tracks across diverse international and regional languages. Processing catalog metadata at scale requires:
- Strict schema validation and quarantine routing to eliminate dirty data.
- Layered data lake storage ensuring raw data immutability.
- Distributed batch aggregation (MapReduce) and transformation (Pig ETL).
- Relational data warehousing with external/managed separation (Hive) and SQL bidirectional synchronization.
- Advanced distributed analytical queries using window partitioning (PySpark).
- Unstructured/semi-structured web datacenter ingestion and Cloud NoSQL document storage (MongoDB Atlas).
- Real-time observability, indexed search, and verified result visualizations.

## 3. Core Syllabus Requirements & Implementation
The platform satisfies all 5 Big Data curriculum requirements:
1. **Import/Export Data from Datacenter (Website or Unstructured) to HDFS**: [`pipeline/datacenter_web_to_hdfs.py`](pipeline/datacenter_web_to_hdfs.py) (`make datacenter`)
2. **Import/Export Data from SQL to HDFS**: [`pipeline/sql_hdfs_connector.py`](pipeline/sql_hdfs_connector.py) (`make sql-bridge`)
3. **Storage / Process Data in NoSQL Using MongoDB**: [`nosql/mongo_manager.py`](nosql/mongo_manager.py) (`make nosql`) connected to Cloud MongoDB Atlas (`music_lakehouse.tracks`)
4. **Structured / Unstructured Data Analysis Using Apache Pig**: [`pig/clean_music.pig`](pig/clean_music.pig) (`make pipeline`)
5. **Structured Data Processing & Analysis Using Apache Hive**: [`hive/`](hive/) (`make pipeline`)

## 4. Architecture
The platform is organized into 5 distinct tiers: Web/Datacenter Ingestion, HDFS Data Lake Storage, Distributed Processing Engines (MapReduce, Pig, Hive, Spark), Cloud NoSQL Lakehouse (MongoDB Atlas), and Observability/Visualization.
For full architectural blueprints and Mermaid diagrams, see [docs/architecture.md](docs/architecture.md).

## 5. Technologies
- **Operating System**: Fedora Linux 44 (Workstation Edition), Kernel 7.1.9, x86_64
- **Core Runtime**: Java OpenJDK 17.0.14 Temurin, Python 3.14.7
- **Distributed Storage**: Apache Hadoop 3.5.0 HDFS (`hdfs://localhost:9000`)
- **Cluster Resource Manager**: Apache Hadoop YARN
- **Batch Processing**: Native Java MapReduce
- **Distributed ETL**: Apache Pig 0.17.0
- **Data Warehouse**: Apache Hive 4.0.0
- **Advanced Analytics**: Apache Spark 3.5.3 (PySpark)
- **Relational Bridge**: SQLite 3NF Normalized Relational Warehouse
- **NoSQL Engine**: Cloud MongoDB Atlas + Embedded Document Store Fallback
- **Frontend Dashboard**: Vanilla HTML5, CSS3, JavaScript, Chart.js, In-Memory Indexed Search Engine

## 6. Dataset
- **Nature**: 100% Authentic Music Metadata (85,494 tracks across 10 musical genres).
- **Scale**:
  - 81,191 real English & international tracks from Spotify
  - 4,197 real Tamil Kollywood tracks (A.R. Rahman, Anirudh, Yuvan, Ilaiyaraaja, Harris Jayaraj, etc.)
  - 56 iconic Malayalam cinema classics (Sushin Shyam, Jassie Gift, Mohanlal films, etc.)
  - 50 controlled quarantine edge cases (schema boundary testing)
- **Zero Synthetic & Zero Duplicates**: Every track is globally unique (`track_id` and `track_name + artist_name`).
- **Dataset Truthfulness**: In compliance with Section 36 of project development rules, the dataset represents track metadata and catalog popularity attributes rather than raw streaming clickstream events.
- Full details in [data/README.md](data/README.md).

## 7. Data Schema
The dataset schema is strictly specified in [config/schemas/music_schema.json](config/schemas/music_schema.json) and documented in [docs/data_dictionary.md](docs/data_dictionary.md):
- `track_id` (String, Required): Unique track identifier.
- `track_name` (String, Required): Track title.
- `artist_name` (String, Required): Performing artist or band.
- `album_name` (String, Optional): Album title.
- `genre` (String, Required): Musical genre classification.
- `popularity` (Integer, 0-100): Popularity score.
- `duration_ms` (Integer, 1000-3600000): Track duration in milliseconds.
- `explicit` (Integer, 0 or 1): Explicit content advisory flag.
- `year` (Integer, 1950-2026): Track release year.

## 8. HDFS Layout
HDFS lakehouse enforces 5 distinct layers under `/music_project`:
- `/music_project/raw`: Immutable raw CSV ingestion.
- `/music_project/processed`: Clean tab-delimited normalized dataset.
- `/music_project/curated`: Enriched features output by Pig ETL (`popularity_tier`, `duration_sec`).
- `/music_project/analytics`: Multi-engine analytical aggregates (Parquet, ORC, TSV).
- `/music_project/quarantine`: Schema-violating records with audit rejection codes.

## 9. Pig Pipeline
- **Script**: [pig/clean_music.pig](pig/clean_music.pig)
- **Runner**: [pig/run.sh](pig/run.sh)
- **Transformations**: Filters clean rows, derives `duration_sec = duration_ms / 1000`, assigns `popularity_tier` (`HIT`, `MAINSTREAM`, `NICHE`), groups by genre, and calculates volume, average popularity, and average duration.
- **Output**: Saved to `/music_project/curated/pig_curated_tracks` and `/music_project/analytics/pig_genre_summary`.

## 10. MapReduce Job
- **Java Class**: [hadoop/mapreduce/src/ArtistAnalyticsJob.java](hadoop/mapreduce/src/ArtistAnalyticsJob.java)
- **Runner**: [hadoop/mapreduce/run.sh](hadoop/mapreduce/run.sh)
- **Logic**: Custom Mapper emitting `(artist_name, "popularity:durationMs")`; Reducer computing catalog volume, average popularity, minimum popularity, maximum popularity, and average duration.
- **Output**: Saved to `/music_project/analytics/mapreduce_artist_summary`.

## 11. Hive Warehouse
- **Scripts**: [hive/database.hql](hive/database.hql), [hive/tables.hql](hive/tables.hql), [hive/views.hql](hive/views.hql), [hive/analytics.hql](hive/analytics.hql)
- **Runner**: [hive/run.sh](hive/run.sh)
- **Safety**: Uses external tables for HDFS data lake layers to prevent data loss on drop. Implements managed ORC table `hive_artist_summary`.
- **Queries**: Runs top artists by popularity, genre distribution, catalog volume, genre rankings, and top hit songs.

## 12. PySpark Analytics
- **Job**: [spark/jobs/music_analytics.py](spark/jobs/music_analytics.py)
- **Runner**: [spark/run.sh](spark/run.sh)
- **Logic**: Reads with explicit `StructType`, performs DataFrame column pruning, cache reuse, explicit vs clean content disparity analysis, and window partitioning (`row_number()` over genre) to determine the top 3 tracks per genre.
- **Output**: Written in Snappy Parquet to HDFS and JSON to `results/spark/`.

## 13. Data-Quality Strategy
Validation occurs at ingestion before any data lands in the clean lake:
- Mandatory non-null constraints.
- Range bounds on popularity ($[0, 100]$), duration ($[1000, 3600000]$ ms), and year ($[1950, 2026]$).
- Deduplication by `track_id`.
- Rejection threshold safety check ($\le 30\%$).
- All rejected records routed to HDFS quarantine with audit timestamps and error codes.

## 14. Error Handling
- Strict `set -euo pipefail` across all Bash orchestrators.
- No silent exception swallowing (`try / except: pass` forbidden).
- Detailed error logging to `logs/ingestion.log` and `logs/pipeline.log`.
- Idempotent cleanup ensuring repeat runs do not fail due to pre-existing directories.

## 15. Testing
Automated test suite located in `tests/`:
- `tests/test_schema.py`: Schema contract validation.
- `tests/test_validation.py`: Null handling, boundaries, duplicates, explicit flags.
- `tests/test_transformations.py`: Calculations, popularity tiers, token parsing.
- Run via `make test`.

## 16. Installation
Prerequisites: Fedora Linux, Java 17 Temurin, Hadoop 3.5.0.
```bash
git clone <repo_url>
cd bdpro
make bootstrap
```

## 17. Execution
```bash
# Ensure HDFS and YARN daemons are active
make bootstrap

# Run full healthcheck across all 10 ecosystem components
make healthcheck

# Execute end-to-end Big Data pipeline (Ingest -> Pig -> MapReduce -> Hive -> Spark)
make pipeline

# Execute syllabus integration bridges
make datacenter   # Web Datacenter <-> HDFS
make sql-bridge   # Relational SQL <-> HDFS
make nosql        # Cloud MongoDB Atlas NoSQL Store & Aggregations

# Run automated test suite
make test

# Launch local visualization dashboard & search engine
make dashboard
```

## 18. Troubleshooting
Detailed troubleshooting steps for Java 17 reflection, Derby metastore locks, SSH bypass, and YARN container dependencies are documented in [docs/troubleshooting.md](docs/troubleshooting.md).

## 19. Results
Key analytical findings from authentic cluster runs on 85,494 tracks:
- **Total Ingested Tracks**: 85,494 (85,444 Valid, 50 Quarantined).
- **Unique Artists Represented**: 33,420 unique artists.
- **Top Genres by Catalog Volume**: Pop (36,929 tracks), Electronic (13,162 tracks), Indie (8,860 tracks), Rock (7,469 tracks).
- **Highest Average Popularity Genres**: R&B (46.6 / 100), Indie (44.7 / 100), Rock (40.5 / 100).
- **Cloud MongoDB Atlas Documents**: 85,444 verified documents across 10 musical genres.
- Full audit report in [results/data_quality_report.md](results/data_quality_report.md).

## 20. Limitations
- Single-node pseudo-distributed deployment running on one Fedora workstation.
- Embedded Apache Derby metastore limits concurrent Hive sessions to one connection.
- Batch processing model rather than real-time streaming ingestion.

## 21. Future Scalability
- Transition to fully distributed multi-node cluster with dedicated NameNode HA and ZooKeeper.
- Deploy external PostgreSQL metastore for concurrent Hive / Trino / Presto query engines.
- Add Apache Kafka and Spark Structured Streaming for real-time clickstream ingestion.
