#!/usr/bin/env python3
"""
Quarantine Handler for Music Analytics Platform
Serializes schema-violating and anomalous records with full audit trail.
"""

import json
import csv
from datetime import datetime, timezone
from typing import List, Dict, Any

class QuarantineManager:
    @staticmethod
    def format_quarantine_records(raw_quarantine: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        formatted = []
        now_iso = datetime.now(timezone.utc).isoformat()
        for item in raw_quarantine:
            record = {
                "quarantine_id": f"QRN_{item['row_number']}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "timestamp": now_iso,
                "row_number": item["row_number"],
                "rejection_reason": item["rejection_reason"],
                "raw_payload": json.dumps(item["raw_data"])
            }
            formatted.append(record)
        return formatted

    @staticmethod
    def write_quarantine_csv(formatted_records: List[Dict[str, Any]], output_path: str):
        fieldnames = ["quarantine_id", "timestamp", "row_number", "rejection_reason", "raw_payload"]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(formatted_records)
