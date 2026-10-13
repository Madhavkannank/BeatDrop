# Data Dictionary: Music Track & Popularity Analytics

This document defines the data contract and attribute semantics for the Music Track & Popularity Analytics platform.

| Field Name | Type | Nullable | Validation Rule | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `track_id` | `STRING` | **No** | Non-empty alphanumeric string (`minLength: 4`). Must be unique. | Unique identifier for the music track. | `4iV5W9uYEdYUVa79Axb7Rh` |
| `track_name` | `STRING` | **No** | Non-empty string (`minLength: 1`). | The displayed title of the musical recording. | `Blinding Lights` |
| `artist_name` | `STRING` | **No** | Non-empty string (`minLength: 1`). | Primary performing artist, group, or band. | `The Weeknd` |
| `album_name` | `STRING` | **Yes** | String (defaults to `Unknown Album` if blank). | Title of the studio album, EP, or single. | `After Hours` |
| `genre` | `STRING` | **No** | Non-empty string matching recognized genre tokens. | Primary musical genre classification. | `Pop` |
| `popularity` | `INTEGER` | **No** | `0 <= popularity <= 100` | Platform popularity score (0 to 100 scale). | `91` |
| `duration_ms` | `INTEGER` | **No** | `1000 <= duration_ms <= 3600000` | Duration of track playback in milliseconds. | `200040` |
| `explicit` | `INTEGER` | **No** | Values restricted to `0` or `1`. | Advisory content indicator (`0` = clean, `1` = explicit). | `0` |
| `year` | `INTEGER` | **No** | `1950 <= year <= 2026` | Original release year of the track or master recording. | `2020` |

---

### Data Ingestion Quality Thresholds

1. **Required Non-Null Constraints**:
   - Records with null or empty `track_id`, `track_name`, `artist_name`, `genre`, `popularity`, `duration_ms`, `explicit`, or `year` are rejected.
2. **Numeric Boundaries**:
   - `popularity`: Must fall within `[0, 100]`. Negative or values > 100 are rejected.
   - `duration_ms`: Must be strictly positive and realistic (1 second to 60 minutes).
3. **Quarantine Routing**:
   - Any record violating the above contracts is routed to `/music_project/quarantine/` with an explanatory error code rather than being silently ignored or crashing downstream processing.
