-- ==============================================================================
-- Analytical Queries for Music Analytics Platform
-- Executes meaningful queries across the music warehouse
-- ==============================================================================

USE music_warehouse;

-- Populate Managed Summary Table from External Processed Data
INSERT OVERWRITE TABLE hive_artist_summary
SELECT 
    artist_name,
    genre,
    COUNT(track_id) AS total_tracks,
    ROUND(AVG(popularity), 2) AS avg_popularity,
    MIN(popularity) AS min_popularity,
    MAX(popularity) AS max_popularity,
    ROUND(AVG(duration_ms) / 1000.0, 2) AS avg_duration_sec
FROM processed_music_tracks
GROUP BY artist_name, genre;

-- Query 1: Top 10 Artists by Average Popularity
SELECT 
    artist_name,
    track_count,
    avg_popularity,
    min_popularity,
    max_popularity
FROM view_top_artists
ORDER BY avg_popularity DESC
LIMIT 10;

-- Query 2: Genre Distribution and Metrics
SELECT 
    genre,
    total_tracks,
    avg_genre_popularity,
    avg_genre_duration_sec,
    explicit_track_count
FROM view_genre_distribution
ORDER BY total_tracks DESC;

-- Query 3: Top 10 Artists by Track Catalog Volume
SELECT 
    artist_name,
    track_count,
    avg_popularity
FROM view_top_artists
ORDER BY track_count DESC
LIMIT 10;

-- Query 4: Average Popularity and Duration Ranked by Genre
SELECT 
    genre,
    avg_genre_popularity,
    avg_genre_duration_sec
FROM view_genre_distribution
ORDER BY avg_genre_popularity DESC;

-- Query 5: Top 15 Most Popular Tracks in the Catalog
SELECT 
    track_id,
    track_name,
    artist_name,
    genre,
    popularity,
    year
FROM view_popular_hits
ORDER BY popularity DESC, year DESC
LIMIT 15;
