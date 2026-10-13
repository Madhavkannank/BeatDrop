-- ==============================================================================
-- Apache Pig ETL Script: Clean, Enrich, and Aggregate Music Data
-- Input: /music_project/processed/tracks_processed.tsv
-- Outputs:
--   1. Curated Tracks: /music_project/curated/pig_curated_tracks
--   2. Genre Summary:  /music_project/analytics/pig_genre_summary
-- ==============================================================================

-- 1. Load Processed Records from HDFS
raw_tracks = LOAD '/music_project/processed/tracks_processed.tsv' USING PigStorage('\t') AS (
    track_id: chararray,
    track_name: chararray,
    artist_name: chararray,
    album_name: chararray,
    genre: chararray,
    popularity: int,
    duration_ms: int,
    explicit: int,
    year: int
);

-- 2. Filter Valid Records (Quality Gate)
clean_tracks = FILTER raw_tracks BY (
    track_id IS NOT NULL AND
    track_name IS NOT NULL AND
    artist_name IS NOT NULL AND
    genre IS NOT NULL AND
    popularity >= 0 AND popularity <= 100 AND
    duration_ms >= 1000
);

-- 3. Transformation & Feature Enrichment:
-- Convert duration to seconds and classify popularity tier
enriched_tracks = FOREACH clean_tracks GENERATE
    track_id,
    track_name,
    artist_name,
    album_name,
    genre,
    popularity,
    duration_ms,
    (duration_ms / 1000) AS duration_sec: int,
    (CASE
        WHEN popularity >= 75 THEN 'HIT'
        WHEN popularity >= 50 THEN 'MAINSTREAM'
        ELSE 'NICHE'
     END) AS popularity_tier: chararray,
    explicit,
    year;

-- Store Curated Analytical Tracks Dataset to HDFS
STORE enriched_tracks INTO '/music_project/curated/pig_curated_tracks' USING PigStorage('\t');

-- 4. Grouping & ETL Aggregation by Genre
grouped_by_genre = GROUP enriched_tracks BY genre;

genre_summary = FOREACH grouped_by_genre GENERATE
    group AS genre,
    COUNT(enriched_tracks) AS total_tracks: long,
    ROUND(AVG(enriched_tracks.popularity)) AS avg_popularity: double,
    ROUND(AVG(enriched_tracks.duration_sec)) AS avg_duration_sec: double;

-- Order by average popularity descending
ordered_genre_summary = ORDER genre_summary BY avg_popularity DESC;

-- Store Genre Summary Analytics to HDFS
STORE ordered_genre_summary INTO '/music_project/analytics/pig_genre_summary' USING PigStorage('\t');
