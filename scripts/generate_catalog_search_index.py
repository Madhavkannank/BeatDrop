#!/usr/bin/env python3
"""
Generates the CDN-ready catalog search index for the BeatDrop edge search engine.
Extracts top tracks per genre, classic discographies, high-volume and high-popularity artists.
"""

import csv
import json
import os
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "sample", "music_tracks.csv")
DEST_JSON = os.path.join(PROJECT_ROOT, "dashboard", "data", "catalog_search_index.json")

def generate():
    artist_tracks = defaultdict(list)
    genre_tracks = defaultdict(list)
    
    total_tracks = 0
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            total_tracks += 1
            if r["track_id"].startswith("QUAR_"):
                continue
            try:
                pop = int(r["popularity"])
                dur = round(int(r["duration_ms"]) / 1000.0, 1)
                yr = int(r["year"])
            except (ValueError, KeyError):
                continue
            
            t = {
                "track_id": r["track_id"],
                "track_name": r["track_name"],
                "artist_name": r["artist_name"],
                "album_name": r.get("album_name", ""),
                "genre": r["genre"],
                "popularity": pop,
                "duration_sec": dur,
                "year": yr
            }
            artist_tracks[r["artist_name"]].append(t)
            genre_tracks[r["genre"]].append(t)
            
    # Compile top artists
    top_artists = []
    for art, t_list in artist_tracks.items():
        count = len(t_list)
        avg_pop = round(sum(x["popularity"] for x in t_list) / count, 1)
        avg_dur = round(sum(x["duration_sec"] for x in t_list) / count, 1)
        latest_yr = max(x["year"] for x in t_list)
        top_artists.append({
            "artist_name": art,
            "total_tracks": count,
            "avg_popularity": avg_pop,
            "avg_duration_sec": avg_dur,
            "latest_year": latest_yr
        })
    
    # Sort artists prioritizing multi-track catalog leaders and high popularity
    top_artists.sort(
        key=lambda a: (a["avg_popularity"] * (1.2 if a["total_tracks"] >= 5 else 0.8), a["total_tracks"]),
        reverse=True
    )
    selected_artists = top_artists[:600]
    
    # Compile popular tracks
    selected_tracks_map = {}
    tamil_keywords = [
        "A.R. Rahman", "Ilaiyaraaja", "Anirudh", "Harris Jayaraj", "Yuvan", "Sid Sriram",
        "K.J. Yesudas", "S. P. Balasubrahmanyam", "Hariharan", "Shankar Mahadevan",
        "Chithra", "Shreya Ghoshal", "Dhanush", "Santhosh Narayanan", "G.V. Prakash",
        "D. Imman", "Vijay", "Kamal Haasan", "Roja", "Bombay", "Alaipayuthey", "Muthu",
        "Padayappa", "Kannathil", "Pudhupettai", "Anniyan", "Ghajini", "Vaaranam"
    ]
    
    for genre, t_list in genre_tracks.items():
        # Top 300 tracks per genre
        t_list.sort(key=lambda x: (x["popularity"], x["year"]), reverse=True)
        for t in t_list[:300]:
            selected_tracks_map[t["track_id"]] = t
            
        # Add all high pop (>= 75)
        for t in t_list:
            if t["popularity"] >= 75:
                selected_tracks_map[t["track_id"]] = t
            elif any(kw.lower() in (t["artist_name"] + " " + t["track_name"] + " " + t["album_name"]).lower() for kw in tamil_keywords):
                selected_tracks_map[t["track_id"]] = t
                
    selected_tracks = list(selected_tracks_map.values())
    selected_tracks.sort(key=lambda x: (x["popularity"], x["year"]), reverse=True)
    
    output = {
        "total_catalog_tracks": total_tracks,
        "total_catalog_artists": len(artist_tracks),
        "popular_tracks": selected_tracks,
        "top_artists": selected_artists
    }
    
    os.makedirs(os.path.dirname(DEST_JSON), exist_ok=True)
    with open(DEST_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
        
    print(f"Generated {DEST_JSON}:")
    print(f"  Tracks indexed: {len(selected_tracks):,}")
    print(f"  Artists indexed: {len(selected_artists):,}")
    print(f"  Total catalog scale: {total_tracks:,}")

if __name__ == "__main__":
    generate()
