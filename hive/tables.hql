-- ==============================================================================
-- Table Definitions for Music Analytics Warehouse
--
-- HIVE DATA SAFETY CONTRACT:
-- 1. EXTERNAL TABLES: Used for data lake layers (/music_project/{raw, processed, curated}).
--    Dropping an EXTERNAL table drops ONLY the metastore schema definition,
--    GUARANTEEING that raw/curated HDFS storage files remain intact and preserved.
-- 2. MANAGED TABLES: Used for Hive-owned internal summary aggregations.
--    Dropping a MANAGED table purges both metadata and underlying warehouse files.
-- ==============================================================================

USE music_warehouse;

-- 1. External Table: Processed Tracks (Tab-delimited clean data lake layer)
CREATE EXTERNAL TABLE IF NOT EXISTS processed_music_tracks (
    track_id STRING COMMENT 'Unique Spotify Track ID',
    track_name STRING COMMENT 'Track Title',
    artist_name STRING COMMENT 'Performing Artist Name',
    album_name STRING COMMENT 'Album or Single Title',
    genre STRING COMMENT 'Musical Genre',
    popularity INT COMMENT 'Spotify Popularity 0-100',
    duration_ms INT COMMENT 'Duration in Milliseconds',
    explicit INT COMMENT 'Explicit Flag 0 or 1',
    year INT COMMENT 'Release Year'
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION '/music_project/processed';

-- 2. External Table: Pig Curated Tracks (Enriched features from Pig ETL)
CREATE EXTERNAL TABLE IF NOT EXISTS curated_music_tracks (
    track_id STRING,
    track_name STRING,
    artist_name STRING,
    album_name STRING,
    genre STRING,
    popularity INT,
    duration_ms INT,
    duration_sec INT,
    popularity_tier STRING,
    explicit INT,
    year INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
STORED AS TEXTFILE
LOCATION '/music_project/curated/pig_curated_tracks';

-- 3. Managed Analytical Table: Pre-aggregated Artist Catalog & Popularity Summary
CREATE TABLE IF NOT EXISTS hive_artist_summary (
    artist_name STRING,
    genre STRING,
    total_tracks INT,
    avg_popularity DOUBLE,
    min_popularity INT,
    max_popularity INT,
    avg_duration_sec DOUBLE
)
STORED AS ORC;
