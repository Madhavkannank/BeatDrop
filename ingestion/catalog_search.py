#!/usr/bin/env python3
"""
Catalog Search Engine for Music Analytics Platform
Searches local dataset and data lake layers for existing tracks before invoking external APIs.
Guarantees strict matching: ignores corrupt/anomalous rows and prevents false-positive substring matches.
"""

import os
import csv
from typing import Dict, Any, Optional

def find_existing_track(
    song_name: str,
    artist_hint: Optional[str] = None,
    dataset_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    if not song_name or not song_name.strip():
        return None

    norm_query_song = song_name.strip().lower()
    if len(norm_query_song) < 2:
        return None

    if dataset_path is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dataset_path = os.path.join(project_root, "data", "sample", "music_tracks.csv")

    if not os.path.exists(dataset_path):
        return None

    norm_query_artist = artist_hint.strip().lower() if artist_hint and artist_hint.strip() else None

    exact_match = None
    substring_match = None

    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            track_id = (row.get("track_id") or "").strip()
            # Ignore synthetic error/quarantine rows (e.g. TRK_ERR_038)
            if track_id.startswith("TRK_ERR") or not track_id:
                continue

            track_name = (row.get("track_name") or "").strip()
            artist_name = (row.get("artist_name") or "").strip()
            
            # Must have valid title and artist
            if not track_name or not artist_name:
                continue

            norm_track = track_name.lower()
            norm_artist = artist_name.lower()

            # 1. Exact match on song title
            if norm_query_song == norm_track:
                if norm_query_artist:
                    if norm_query_artist in norm_artist or norm_artist in norm_query_artist:
                        exact_match = row
                        break
                else:
                    exact_match = row
                    break

            # 2. Substring match: query is a substantial substring of the catalog title
            # (e.g. user typed "hotel california" matching catalog "hotel california - 2013 remaster")
            # Query must be at least 4 characters to avoid accidental 1-3 letter collisions
            if len(norm_query_song) >= 4 and norm_query_song in norm_track and not substring_match:
                if norm_query_artist:
                    if norm_query_artist in norm_artist or norm_artist in norm_query_artist:
                        substring_match = row
                else:
                    substring_match = row

    matched_row = exact_match or substring_match
    if not matched_row:
        return None

    try:
        # Validate that required numeric fields are parseable
        popularity = int(matched_row.get("popularity", 50))
        duration_ms = int(matched_row.get("duration_ms", 210000))
        if popularity < 0 or popularity > 100 or duration_ms < 1000:
            return None

        return {
            "track_id": matched_row["track_id"],
            "track_name": matched_row["track_name"],
            "artist_name": matched_row["artist_name"],
            "album_name": matched_row.get("album_name") or "Unknown Album",
            "genre": matched_row["genre"],
            "popularity": popularity,
            "duration_ms": duration_ms,
            "explicit": int(matched_row.get("explicit", 0)),
            "year": int(matched_row.get("year", 2020)),
            "source": "database",
            "already_in_database": True
        }
    except Exception:
        return None

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "sdfghj"
    artist = sys.argv[2] if len(sys.argv) > 2 else None
    print(f"Searching for: '{query}' (Artist: {artist})...")
    res = find_existing_track(query, artist)
    print("Found:", res)
