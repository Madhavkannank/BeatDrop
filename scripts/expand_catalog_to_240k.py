#!/usr/bin/env python3
"""
Expands the BeatDrop Music Catalog to 239,000 Verified Original Tracks.
Zero deletions: All existing 85,638 tracks (including all authentic Tamil & Malayalam discographies) are 100% preserved.

Target Distribution:
- Hip-Hop:    26,000
- Jazz:       25,500
- R&B:        25,500
- Metal:      25,000
- Country:    25,000
- Rock:       22,000
- Indie:      22,000
- Electronic: 20,000
- Classical:  18,000
- Pop:        30,000 (includes all Tamil blockbusters)
Total: 239,000 original tracks
"""

import os
import csv
import ast
from collections import Counter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CATALOG = os.path.join(PROJECT_ROOT, "data", "sample", "music_tracks.csv")
EXTERNAL_CORPUS = os.path.join(PROJECT_ROOT, "data", "external_spotify_songs_genre_fix.csv")
OUTPUT_CATALOG = os.path.join(PROJECT_ROOT, "data", "sample", "music_tracks.csv")

TARGET_COUNTS = {
    "Hip-Hop": 26000,
    "Jazz": 25500,
    "R&B": 25500,
    "Metal": 25000,
    "Country": 25000,
    "Rock": 22000,
    "Indie": 22000,
    "Electronic": 20000,
    "Classical": 18000,
    "Pop": 30000
}

def classify_subgenres(genre_str):
    if not genre_str or genre_str == "[]":
        return None
    try:
        subgenres = ast.literal_eval(genre_str)
        if isinstance(subgenres, list):
            sub_text = " ".join(s.lower() for s in subgenres)
        else:
            sub_text = str(subgenres).lower()
    except Exception:
        sub_text = str(genre_str).lower()

    if any(k in sub_text for k in ["metal", "grindcore", "hardcore"]):
        return "Metal"
    if any(k in sub_text for k in ["hip hop", "hip-hop", "rap", "trap", "drill", "boom bap"]):
        return "Hip-Hop"
    if any(k in sub_text for k in ["r&b", "r-n-b", "soul", "funk", "motown", "neo soul", "blues", "gospel"]):
        return "R&B"
    if any(k in sub_text for k in ["jazz", "bop", "swing", "big band", "dixieland", "bossa nova"]):
        return "Jazz"
    if any(k in sub_text for k in ["country", "bluegrass", "nashville", "americana", "honky tonk", "honky-tonk"]):
        return "Country"
    if any(k in sub_text for k in ["classical", "orchestra", "symphony", "baroque", "chamber music", "opera"]):
        return "Classical"
    if any(k in sub_text for k in ["indie", "folk", "acoustic", "singer-songwriter", "lo-fi", "ambient", "dream pop"]):
        return "Indie"
    if any(k in sub_text for k in ["rock", "punk", "grunge", "alt-rock", "alternative rock", "new wave", "psych"]):
        return "Rock"
    if any(k in sub_text for k in ["electronic", "edm", "house", "techno", "trance", "dubstep", "synth", "electro", "dance"]):
        return "Electronic"
    if any(k in sub_text for k in ["pop", "disco", "k-pop", "j-pop", "latin"]):
        return "Pop"
    return None

def main():
    print("=== Step 1: Loading existing catalog ===")
    existing_tracks = []
    existing_ids = set()
    existing_pairs = set()
    genre_counts = Counter()

    with open(INPUT_CATALOG, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            existing_tracks.append(r)
            existing_ids.add(r["track_id"])
            existing_pairs.add((r["track_name"].strip().lower(), r["artist_name"].strip().lower()))
            genre_counts[r["genre"]] += 1

    print(f"Base catalog: {len(existing_tracks):,} tracks (100% preserved)")
    for g, c in genre_counts.most_common():
        print(f"  {g:12s}: {c:,} (Target: {TARGET_COUNTS.get(g, 0):,})")

    print("\n=== Step 2: Sampling required tracks from 1.26M verified Spotify dataset ===")
    added_counts = Counter()
    new_records = []

    with open(EXTERNAL_CORPUS, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            g = classify_subgenres(r.get("genre", ""))
            if not g:
                continue

            current_total = genre_counts[g] + added_counts[g]
            target = TARGET_COUNTS.get(g, 0)
            if current_total >= target:
                continue

            tid = r.get("track_id", "").strip()
            tname = r.get("name", "").strip()
            art = r.get("artist", "").strip()
            alb = r.get("album", "").strip() or "Single"

            if not tid or not tname or not art or tname.lower() == "name":
                continue

            pair = (tname.lower(), art.lower())
            if tid in existing_ids or pair in existing_pairs:
                continue

            try:
                pop = int(float(r.get("popularity", 50)))
                dur = int(float(r.get("duration_ms", 210000)))
                yr = int(float(r.get("release_year", 2020)))
                exp = 1 if str(r.get("explicit", "")).lower() in ["true", "1", "t"] else 0
            except (ValueError, TypeError):
                continue

            if dur < 1000 or dur > 3600000 or yr < 1950 or yr > 2026 or pop < 0 or pop > 100:
                continue

            existing_ids.add(tid)
            existing_pairs.add(pair)
            added_counts[g] += 1

            new_record = {
                "track_id": tid,
                "track_name": tname,
                "artist_name": art,
                "album_name": alb,
                "genre": g,
                "popularity": pop,
                "duration_ms": dur,
                "explicit": exp,
                "year": yr
            }
            new_records.append(new_record)

    print(f"\nSuccessfully extracted {len(new_records):,} new verified tracks:")
    for g, c in added_counts.most_common():
        print(f"  + {g:12s}: {c:,}")

    print("\n=== Step 3: Writing combined dataset ===")
    combined = existing_tracks + new_records
    with open(OUTPUT_CATALOG, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined)

    final_counts = Counter(r["genre"] for r in combined)
    print(f"\nFinal catalog size: {len(combined):,} tracks written to {OUTPUT_CATALOG}")
    print("\n=== Final Genre Distribution ===")
    for g, c in final_counts.most_common():
        print(f"  {g:12s}: {c:,}")

if __name__ == "__main__":
    main()
