# Music Track & Popularity Dataset

## Overview
This dataset contains Spotify track metadata curated for batch and analytical processing across the Big Data pipeline (Hadoop MapReduce, Apache Pig, Apache Hive, and PySpark).

In accordance with strict dataset truthfulness guidelines (Section 36 of project development rules), this dataset represents **track metadata and catalog popularity attributes**, rather than raw user streaming event logs.

## Source & Schema
The dataset file is located at `data/sample/music_tracks.csv` and adheres to the JSON schema contract defined in `config/schemas/music_schema.json` and documented in `docs/data_dictionary.md`.

### Attributes
1. `track_id` (String): Unique identifier.
2. `track_name` (String): Title of track.
3. `artist_name` (String): Primary artist or group name.
4. `album_name` (String): Associated album name.
5. `genre` (String): Categorical musical genre (Rock, Pop, Hip-Hop, Electronic, Jazz, Classical, R&B, Metal, Country, Indie).
6. `popularity` (Integer): Spotify popularity metric ranging from 0 to 100.
7. `duration_ms` (Integer): Track length in milliseconds (1,000 to 3,600,000 ms).
8. `explicit` (Integer): Flag indicating explicit lyrical content (0 = Clean, 1 = Explicit).
9. `year` (Integer): Release year (1950 to 2026).

## Injected Test Anomalies
To provide realistic and verifiable validation metrics during ingestion (Phase 4):
- **50 Synthetic Invalid Records** were injected with controlled flaws:
  - Negative duration (`duration_ms < 0`)
  - Sub-second duration (`duration_ms < 1000`)
  - Out-of-range popularity (`popularity < 0` or `popularity > 100`)
  - Missing mandatory fields (null `track_name`, null `artist_name`, null `genre`)
  - Invalid explicit flag values
  - Out-of-bounds release year
- **10 Exact Duplicate Pairs** were injected to verify deterministic deduplication.
