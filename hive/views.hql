-- ==============================================================================
-- Analytical Views for Music Warehouse
-- Provides business semantics and pre-computed analytical views
-- ==============================================================================

USE music_warehouse;

-- View 1: Top Artists Ranked by Average Popularity
CREATE OR REPLACE VIEW view_top_artists AS
SELECT 
    artist_name,
    COUNT(track_id) AS track_count,
    ROUND(AVG(popularity), 2) AS avg_popularity,
    MIN(popularity) AS min_popularity,
    MAX(popularity) AS max_popularity,
    ROUND(AVG(duration_ms) / 1000.0, 1) AS avg_duration_sec
FROM processed_music_tracks
GROUP BY artist_name
HAVING COUNT(track_id) >= 10;

-- View 2: Genre Distribution and Popularity Benchmarks
CREATE OR REPLACE VIEW view_genre_distribution AS
SELECT 
    genre,
    COUNT(track_id) AS total_tracks,
    ROUND(AVG(popularity), 2) AS avg_genre_popularity,
    ROUND(AVG(duration_ms) / 1000.0, 1) AS avg_genre_duration_sec,
    SUM(CASE WHEN explicit = 1 THEN 1 ELSE 0 END) AS explicit_track_count
FROM processed_music_tracks
GROUP BY genre;

-- View 3: Top Hit Records (Popularity >= 85)
CREATE OR REPLACE VIEW view_popular_hits AS
SELECT 
    track_id,
    track_name,
    artist_name,
    album_name,
    genre,
    popularity,
    year
FROM processed_music_tracks
WHERE popularity >= 85;
