#!/usr/bin/env python3
"""
Groq Metadata Fetcher for Music Analytics Platform
Extracts rich, schema-compliant track metadata from a song title using Groq LLM API.
Supports global, Indian, Malayalam, Tamil, Telugu, Hindi, Western, and international music.
Filters keyboard mash deterministically.
"""

import os
import sys
import json
import re
import hashlib
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

RECOGNIZED_GENRES = [
    "Pop", "Hip-Hop", "Indie", "Rock", "R&B",
    "Classical", "Jazz", "Electronic", "Country", "Metal"
]

CANDIDATE_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b"
]

def load_env_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "")
    if key:
        return key.strip()
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GROQ_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

def is_likely_gibberish(text: str) -> bool:
    t = text.strip().lower()
    if len(t) < 2:
        return True
    
    # Check for pure vowel-less consonant strings >= 4 chars (e.g. sdfghj, dfghjkl)
    vowels = set("aeiouy")
    words = t.split()
    if all(len(w) >= 4 and not any(c in vowels for c in w) for w in words):
        return True

    # Common keyboard mash rows
    mash_patterns = [
        "qwerty", "asdfgh", "zxcvbn", "sdfghj", "dfghjk", "fghjkl",
        "qwert", "asdfg", "zxcvb", "lkjhgf", "mnbvcx", "poiuyt"
    ]
    if any(pat in t for pat in mash_patterns):
        return True

    # Repeated characters 4+ times (e.g. aaaaa, zzzzz)
    if re.search(r"(.)\1{3,}", t):
        return True

    return False

import urllib.parse

def map_genre(raw_genre: str) -> str:
    g = (raw_genre or "").lower()
    if any(k in g for k in ["rap", "hip-hop", "hip hop", "trap"]):
        return "Hip-Hop"
    elif any(k in g for k in ["indie", "folk", "acoustic", "singer"]):
        return "Indie"
    elif any(k in g for k in ["metal"]):
        return "Metal"
    elif any(k in g for k in ["rock", "punk", "grunge"]):
        return "Rock"
    elif any(k in g for k in ["r&b", "soul", "funk"]):
        return "R&B"
    elif any(k in g for k in ["jazz", "blues"]):
        return "Jazz"
    elif any(k in g for k in ["classic", "carnatic", "hindustani", "orchestral", "instrumental"]):
        return "Classical"
    elif any(k in g for k in ["dance", "electronic", "edm", "house", "techno"]):
        return "Electronic"
    elif any(k in g for k in ["country", "bluegrass"]):
        return "Country"
    else:
        return "Pop"

def search_global_catalog(song_name: str, artist_hint: Optional[str] = None) -> list:
    """
    Queries global music catalog (Apple Music / iTunes public search API).
    Returns real, verified track candidates with exact artist, album, duration, year.
    """
    clean = song_name.strip()
    term = clean
    if artist_hint:
        term = f"{clean} {artist_hint.strip()}"
    
    url = f"https://itunes.apple.com/search?term={urllib.parse.quote(term)}&entity=song&limit=8"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    results = []
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
    except Exception:
        results = []

    # If nothing was found with the combined artist_hint, try with clean song_name alone
    if not results and artist_hint:
        url2 = f"https://itunes.apple.com/search?term={urllib.parse.quote(clean)}&entity=song&limit=8"
        req2 = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req2, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("results", [])
        except Exception:
            results = []

    candidates = []
    seen = set()
    for r in results:
        track_name = r.get("trackName")
        if not track_name:
            continue
        
        artist_name = r.get("artistName", "Various Artists")
        album_name = r.get("collectionName", "Soundtrack / Single")
        rel_date = r.get("releaseDate", "2020")
        year = int(rel_date[:4]) if rel_date and len(rel_date) >= 4 else 2020
        dur_ms = int(r.get("trackTimeMillis", 215000))
        is_exp = 1 if r.get("trackExplicitness") == "explicit" else 0
        raw_genre = r.get("primaryGenreName", "Pop")
        genre = map_genre(raw_genre)

        key_sig = (track_name.lower(), artist_name.lower()[:15], album_name.lower()[:15])
        if key_sig in seen:
            continue
        seen.add(key_sig)

        seed = f"{track_name}_{artist_name}_{album_name}"
        tid = "TRK" + hashlib.md5(seed.encode("utf-8")).hexdigest()[:19]

        cand = {
            "track_id": tid,
            "track_name": track_name,
            "artist_name": artist_name,
            "album_name": album_name,
            "genre": genre,
            "popularity": 76,
            "duration_ms": max(1000, min(3600000, dur_ms)),
            "explicit": is_exp,
            "year": max(1950, min(2026, year)),
            "source": "verified_catalog"
        }
        candidates.append(cand)

    # If artist_hint provided, prioritize candidates containing the hint in artist or album
    if artist_hint and candidates:
        hint_lower = artist_hint.strip().lower()
        candidates.sort(
            key=lambda c: (
                0 if (hint_lower in c["artist_name"].lower() or hint_lower in c["album_name"].lower()) else 1
            )
        )

    return candidates

def fetch_song_metadata(song_name: str, artist_hint: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
    clean_name = song_name.strip()
    if not clean_name or len(clean_name) < 2:
        raise ValueError("Please provide a valid song title.")

    # 1. Deterministic Gibberish Guard
    if is_likely_gibberish(clean_name):
        raise ValueError(f"'{song_name}' appears to be keyboard mash or random keystrokes rather than a real song.")

    # 2. Check Global Music Catalog for verified ground truth
    catalog_candidates = search_global_catalog(clean_name, artist_hint)
    
    key = (api_key or load_env_key()).strip()

    # If we have verified catalog candidates, use them as ground truth
    if catalog_candidates:
        top_cand = dict(catalog_candidates[0])
        # Format candidate display labels for the UI
        formatted_candidates = []
        for c in catalog_candidates[:4]:
            formatted_candidates.append({
                "label": f"{c['album_name']} ({c['year']}) — {c['artist_name']}",
                "metadata": c
            })
        top_cand["candidates"] = formatted_candidates

        # If Groq key is present, use Groq to intelligently refine genre and popularity score
        if key:
            try:
                refine_prompt = f"""You are a music catalog expert.
Given this verified song:
- Title: "{top_cand['track_name']}"
- Artist: "{top_cand['artist_name']}"
- Album/Soundtrack: "{top_cand['album_name']}"
- Year: {top_cand['year']}
- Duration (ms): {top_cand['duration_ms']}

Refine the genre to exactly one of: {json.dumps(RECOGNIZED_GENRES)}
And estimate its popularity score (integer 0 to 100).
Return valid JSON only:
{{
  "genre": "...",
  "popularity": 75,
  "artist_name": "Primary performing artist / composer"
}}"""
                payload = {
                    "model": "openai/gpt-oss-120b",
                    "messages": [
                        {"role": "system", "content": "You are a music catalog expert. Return valid JSON only."},
                        {"role": "user", "content": refine_prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                    "max_tokens": 256
                }
                req = urllib.request.Request(
                    "https://api.groq.com/openai/v1/chat/completions",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    ref_data = json.loads(resp.read().decode("utf-8"))
                    content = ref_data["choices"][0]["message"]["content"]
                    match = re.search(r"\{.*\}", content, re.DOTALL)
                    if match:
                        refined = json.loads(match.group(0))
                        if refined.get("genre") in RECOGNIZED_GENRES:
                            top_cand["genre"] = refined["genre"]
                        if isinstance(refined.get("popularity"), int):
                            top_cand["popularity"] = max(0, min(100, refined["popularity"]))
                        if refined.get("artist_name") and len(refined["artist_name"]) > 2:
                            top_cand["artist_name"] = refined["artist_name"]
            except Exception:
                pass  # Fall back directly to top_cand ground-truth if Groq refinement times out

        return top_cand

    # 3. Fallback to Groq generative estimation if not found in catalog search
    if not key:
        raise ValueError(f"No catalog entries found for '{song_name}', and GROQ_API_KEY is not set.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    
    prompt = f"""You are a global music metadata engine for Spotify and Apple Music.
Your catalog spans ALL international and regional music, including Indian cinema soundtracks (Malayalam, Tamil, Telugu, Hindi, Bollywood, Kollywood, etc.), as well as Western Pop, Rock, Hip-Hop, Latin, and global releases.

Song query: "{clean_name}"{f' (Artist/Movie hint: "{artist_hint}")' if artist_hint else ''}

Extract or estimate the canonical catalog metadata for this song.
Return valid JSON with:
- "track_name": Canonical track title (string)
- "artist_name": Primary performing artist, singer, or composer (string)
- "album_name": Album or movie soundtrack title (string)
- "genre": MUST be exactly one of: {json.dumps(RECOGNIZED_GENRES)}
- "popularity": integer popularity score between 0 and 100
- "duration_ms": integer length in milliseconds (typically 120000 to 360000)
- "explicit": integer 0 or 1
- "year": integer release year between 1950 and 2026
- "track_id": 22-character alphanumeric Spotify ID

Genre Mapping:
- Movie soundtracks, Indian cinema, romantic ballads, dance -> "Pop" or "R&B"
- Acoustic, alternative, independent releases -> "Indie"
- Carnatic, Hindustani, orchestral, instrumental -> "Classical"
- Rock, Metal -> "Rock" or "Metal"
- Hip-Hop, Rap, Trap -> "Hip-Hop"

Output ONLY the raw JSON object.
"""

    last_error = None
    record = None

    for model in CANDIDATE_MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a music metadata engine. Output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": 1024
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    record = json.loads(match.group(0))
                else:
                    record = json.loads(content)
                if record and record.get("track_name"):
                    break
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            last_error = f"HTTP {e.code} on {model}: {error_body}"
            continue
        except Exception as e:
            last_error = f"Error on {model}: {e}"
            continue

    if not record:
        raise RuntimeError(f"Failed to query Groq: {last_error}")

    track_title = str(record.get("track_name", clean_name)).strip()
    artist_title = str(record.get("artist_name", artist_hint or "Various Artists")).strip()
    if not track_title or track_title.lower() == "unknown":
        track_title = clean_name

    # Fallback / Normalize values
    if "track_id" not in record or len(str(record["track_id"])) < 4:
        seed = f"{artist_title}_{track_title}"
        record["track_id"] = "TRK" + hashlib.md5(seed.encode("utf-8")).hexdigest()[:19]

    # Ensure genre is one of recognized
    genre_raw = str(record.get("genre", "")).strip()
    matched_genre = next((g for g in RECOGNIZED_GENRES if g.lower() == genre_raw.lower()), None)
    if not matched_genre:
        matched_genre = map_genre(genre_raw)
    record["genre"] = matched_genre

    # Coerce numeric types
    record["popularity"] = max(0, min(100, int(record.get("popularity", 68))))
    record["duration_ms"] = max(1000, min(3600000, int(record.get("duration_ms", 215000))))
    record["explicit"] = 1 if int(record.get("explicit", 0)) == 1 else 0
    record["year"] = max(1950, min(2026, int(record.get("year", 2022))))
    record["track_name"] = track_title
    record["artist_name"] = artist_title
    record["album_name"] = str(record.get("album_name", "")).strip() or "Soundtrack / Album"

    return record

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 groq_metadata.py <song_name> [artist_hint]")
        sys.exit(1)
    
    song = sys.argv[1]
    artist = sys.argv[2] if len(sys.argv) > 2 else None
    print(f"Fetching metadata for: '{song}' (Artist hint: {artist})...")
    try:
        res = fetch_song_metadata(song, artist)
        print("Result:")
        print(json.dumps(res, indent=2))
    except ValueError as ve:
        print(f"Validation Error: {ve}", file=sys.stderr)
        sys.exit(1)
