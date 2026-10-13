#!/usr/bin/env python3
"""
Data Validation Engine for Music Analytics Platform
Enforces schema contracts, numeric boundaries, non-null constraints, and deduplication.
"""

import csv
import time
from typing import Dict, Any, List, Tuple

class DataValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.val_cfg = config.get("validation", {})
        self.pop_min = self.val_cfg.get("popularity_min", 0)
        self.pop_max = self.val_cfg.get("popularity_max", 100)
        self.dur_min = self.val_cfg.get("duration_min_ms", 1000)
        self.dur_max = self.val_cfg.get("duration_max_ms", 3600000)
        self.expected_cols = config.get("dataset", {}).get("expected_columns", [
            "track_id", "track_name", "artist_name", "album_name", 
            "genre", "popularity", "duration_ms", "explicit", "year"
        ])

    def validate_record(self, row: Dict[str, str]) -> Tuple[bool, str, Dict[str, Any]]:
        # 1. Check required non-null fields
        for col in ["track_id", "track_name", "artist_name", "genre"]:
            val = row.get(col, "").strip()
            if not val:
                return False, f"MISSING_REQUIRED_FIELD_{col.upper()}", {}

        # 2. Check track_id format
        track_id = row["track_id"].strip()
        if len(track_id) < 4:
            return False, "INVALID_TRACK_ID_LENGTH", {}

        # 3. Numeric bounds validation
        # Popularity
        try:
            pop = int(row.get("popularity", ""))
            if pop < self.pop_min or pop > self.pop_max:
                return False, f"POPULARITY_OUT_OF_BOUNDS_{pop}", {}
        except (ValueError, TypeError):
            return False, "INVALID_POPULARITY_FORMAT", {}

        # Duration
        try:
            dur = int(row.get("duration_ms", ""))
            if dur < self.dur_min or dur > self.dur_max:
                return False, f"DURATION_OUT_OF_BOUNDS_{dur}", {}
        except (ValueError, TypeError):
            return False, "INVALID_DURATION_FORMAT", {}

        # Explicit
        try:
            exp = int(row.get("explicit", ""))
            if exp not in (0, 1):
                return False, f"INVALID_EXPLICIT_FLAG_{exp}", {}
        except (ValueError, TypeError):
            return False, "INVALID_EXPLICIT_FORMAT", {}

        # Year
        try:
            yr = int(row.get("year", ""))
            if yr < 1950 or yr > 2026:
                return False, f"YEAR_OUT_OF_BOUNDS_{yr}", {}
        except (ValueError, TypeError):
            return False, "INVALID_YEAR_FORMAT", {}

        cleaned_record = {
            "track_id": track_id,
            "track_name": row["track_name"].strip(),
            "artist_name": row["artist_name"].strip(),
            "album_name": row.get("album_name", "").strip() or "Unknown Album",
            "genre": row["genre"].strip(),
            "popularity": pop,
            "duration_ms": dur,
            "explicit": exp,
            "year": yr
        }
        return True, "VALID", cleaned_record

    def process_file(self, input_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        start_time = time.time()
        valid_records = []
        quarantine_records = []
        seen_track_ids = set()
        
        total_records = 0
        duplicate_records = 0
        null_records = 0

        with open(input_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Verify columns exist
            if not set(self.expected_cols).issubset(set(reader.fieldnames or [])):
                missing = set(self.expected_cols) - set(reader.fieldnames or [])
                raise ValueError(f"Input file missing expected columns: {missing}")

            for row_idx, row in enumerate(reader, start=1):
                total_records += 1
                is_valid, reason, cleaned = self.validate_record(row)
                
                if not is_valid:
                    if "MISSING" in reason:
                        null_records += 1
                    quarantine_records.append({
                        "row_number": row_idx,
                        "rejection_reason": reason,
                        "raw_data": dict(row)
                    })
                    continue

                # Deduplication by track_id
                tid = cleaned["track_id"]
                if tid in seen_track_ids:
                    duplicate_records += 1
                    quarantine_records.append({
                        "row_number": row_idx,
                        "rejection_reason": f"DUPLICATE_TRACK_ID_{tid}",
                        "raw_data": dict(row)
                    })
                    continue

                seen_track_ids.add(tid)
                valid_records.append(cleaned)

        processing_time = round(time.time() - start_time, 4)
        metrics = {
            "total_records": total_records,
            "valid_records": len(valid_records),
            "invalid_records": len(quarantine_records),
            "duplicate_records": duplicate_records,
            "null_records": null_records,
            "processing_time_seconds": processing_time,
            "data_quality_score": round((len(valid_records) / total_records * 100) if total_records else 0, 2)
        }
        return valid_records, quarantine_records, metrics
