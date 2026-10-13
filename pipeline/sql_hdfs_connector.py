#!/usr/bin/env python3
"""
RDBMS SQL <-> HDFS Bidirectional Data Connector for BeatDrop Platform.
Requirement 2: Import / Export the data from SQL to HDFS.

Capabilities:
1. SQL Database Provisioning:
   - Sets up normalized relational schema (artists, albums, tracks).
   - Seeds with relational music records.
2. SQL to HDFS Import:
   - Performs relational JOIN query in SQL.
   - Streams formatted records directly into HDFS (/music_project/sql_import/tracks_from_sql.tsv).
3. HDFS to SQL Export:
   - Reads processed / analytical data from HDFS lake layer.
   - Materializes relational analytics tables in SQL database (sql_genre_analytics, sql_artist_analytics).
"""

import os
import sys
import sqlite3
import csv
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "music_relational_warehouse.db")
HADOOP_HOME = os.environ.get("HADOOP_HOME", "/home/maddy/opt/hadoop-3.5.0")
HDFS_BIN = os.path.join(HADOOP_HOME, "bin", "hdfs")

def run_hdfs(cmd_args):
    full_cmd = [HDFS_BIN] + cmd_args
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"HDFS error ({' '.join(cmd_args)}): {res.stderr.strip()}")
    return res.stdout.strip()

def init_sql_database(sample_size=1000):
    print(f"=== [1/4] Provisioning Relational SQL Database at {DB_PATH} ===")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS artists (
        artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
        artist_name TEXT UNIQUE NOT NULL,
        primary_genre TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS albums (
        album_id INTEGER PRIMARY KEY AUTOINCREMENT,
        album_name TEXT UNIQUE NOT NULL,
        release_year INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tracks (
        track_id TEXT PRIMARY KEY,
        track_name TEXT NOT NULL,
        artist_id INTEGER NOT NULL,
        album_id INTEGER NOT NULL,
        duration_ms INTEGER NOT NULL,
        popularity INTEGER NOT NULL,
        explicit INTEGER NOT NULL,
        FOREIGN KEY (artist_id) REFERENCES artists(artist_id),
        FOREIGN KEY (album_id) REFERENCES albums(album_id)
    );

    CREATE TABLE IF NOT EXISTS sql_genre_analytics (
        genre TEXT PRIMARY KEY,
        total_tracks INTEGER,
        avg_popularity REAL,
        avg_duration_sec REAL
    );
    """)

    # Populate from catalog if empty
    cur.execute("SELECT COUNT(*) FROM tracks")
    if cur.fetchone()[0] == 0:
        print("Seeding SQL database from BeatDrop catalog...")
        csv_path = os.path.join(PROJECT_ROOT, "data", "sample", "music_tracks.csv")
        artist_cache = {}
        album_cache = {}

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for r in reader:
                if r["track_id"].startswith("QUAR_"):
                    continue
                art = r["artist_name"]
                alb = r["album_name"]
                g = r["genre"]
                yr = int(r["year"])

                if art not in artist_cache:
                    cur.execute("INSERT OR IGNORE INTO artists (artist_name, primary_genre) VALUES (?, ?)", (art, g))
                    cur.execute("SELECT artist_id FROM artists WHERE artist_name = ?", (art,))
                    row = cur.fetchone()
                    if row:
                        artist_cache[art] = row[0]

                if alb not in album_cache:
                    cur.execute("INSERT OR IGNORE INTO albums (album_name, release_year) VALUES (?, ?)", (alb, yr))
                    cur.execute("SELECT album_id FROM albums WHERE album_name = ?", (alb,))
                    row = cur.fetchone()
                    if row:
                        album_cache[alb] = row[0]

                a_id = artist_cache.get(art)
                alb_id = album_cache.get(alb)
                if a_id and alb_id:
                    cur.execute("""
                    INSERT OR IGNORE INTO tracks 
                    (track_id, track_name, artist_id, album_id, duration_ms, popularity, explicit)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (r["track_id"], r["track_name"], a_id, alb_id, int(r["duration_ms"]), int(r["popularity"]), int(r["explicit"])))
                    count += 1
                if count >= sample_size:
                    break

        conn.commit()
        print(f"Seeded {count} relational tracks into SQL database.")

    conn.close()

def import_sql_to_hdfs():
    print("=== [2/4] Executing SQL Query & Importing Relational Data to HDFS ===")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = """
    SELECT 
        t.track_id, 
        t.track_name, 
        a.artist_name, 
        al.album_name, 
        a.primary_genre, 
        t.popularity, 
        t.duration_ms, 
        t.explicit, 
        al.release_year
    FROM tracks t
    JOIN artists a ON t.artist_id = a.artist_id
    JOIN albums al ON t.album_id = al.album_id
    ORDER BY t.popularity DESC;
    """
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    staging_file = os.path.join(PROJECT_ROOT, "results", "staging", "tracks_from_sql.tsv")
    os.makedirs(os.path.dirname(staging_file), exist_ok=True)

    with open(staging_file, "w", encoding="utf-8") as f:
        for r in rows:
            line = "\t".join(str(val) for val in r) + "\n"
            f.write(line)

    hdfs_dest_dir = "/music_project/sql_import"
    hdfs_target = f"{hdfs_dest_dir}/tracks_from_sql.tsv"

    run_hdfs(["dfs", "-mkdir", "-p", hdfs_dest_dir])
    run_hdfs(["dfs", "-put", "-f", staging_file, hdfs_target])

    stat = run_hdfs(["dfs", "-stat", "%n - %b bytes", hdfs_target])
    print(f"Successfully imported SQL data into HDFS: {stat}")
    return hdfs_target

def export_hdfs_to_sql():
    print("=== [3/4] Exporting Analytics from HDFS to Relational SQL Warehouse ===")
    hdfs_analytics = "/music_project/processed/tracks_processed.tsv"
    local_staging = os.path.join(PROJECT_ROOT, "results", "staging", "export_from_hdfs.tsv")

    run_hdfs(["dfs", "-get", "-f", hdfs_analytics, local_staging])

    # Compute genre analytics from HDFS export and load into SQL table
    from collections import defaultdict
    genre_data = defaultdict(list)

    with open(local_staging, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 9:
                genre = parts[4]
                try:
                    pop = int(parts[5])
                    dur_sec = int(parts[6]) / 1000.0
                    genre_data[genre].append((pop, dur_sec))
                except ValueError:
                    continue

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM sql_genre_analytics")

    for g, metrics in genre_data.items():
        total = len(metrics)
        avg_pop = round(sum(m[0] for m in metrics) / total, 2)
        avg_dur = round(sum(m[1] for m in metrics) / total, 1)
        cur.execute("""
        INSERT INTO sql_genre_analytics (genre, total_tracks, avg_popularity, avg_duration_sec)
        VALUES (?, ?, ?, ?)
        """, (g, total, avg_pop, avg_dur))

    conn.commit()
    print("=== [4/4] Verifying SQL Warehouse Analytics Tables ===")
    cur.execute("SELECT genre, total_tracks, avg_popularity, avg_duration_sec FROM sql_genre_analytics ORDER BY avg_popularity DESC")
    results = cur.fetchall()
    for row in results:
        print(f"  [SQL Exported View] {row[0]:12} | Tracks: {row[1]:5} | Avg Pop: {row[2]:5.1f} | Avg Dur: {row[3]:5.1f}s")

    conn.close()
    print("SQL <-> HDFS import and export completed successfully.")

if __name__ == "__main__":
    init_sql_database()
    import_sql_to_hdfs()
    export_hdfs_to_sql()
