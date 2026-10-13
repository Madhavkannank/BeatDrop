import unittest
import yaml
import sys
import os

# Add ingestion module to sys.path
sys.path.insert(0, os.path.abspath("ingestion"))
from validator import DataValidator

class TestDataValidation(unittest.TestCase):
    def setUp(self):
        with open("config/application.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.validator = DataValidator(self.config)

    def test_valid_record(self):
        row = {
            "track_id": "TRK123456",
            "track_name": "Bohemian Rhapsody",
            "artist_name": "Queen",
            "album_name": "A Night at the Opera",
            "genre": "Rock",
            "popularity": "88",
            "duration_ms": "354000",
            "explicit": "0",
            "year": "1975"
        }
        is_valid, reason, cleaned = self.validator.validate_record(row)
        self.assertTrue(is_valid)
        self.assertEqual(reason, "VALID")
        self.assertEqual(cleaned["popularity"], 88)
        self.assertEqual(cleaned["duration_ms"], 354000)

    def test_null_mandatory_field(self):
        row = {
            "track_id": "TRK123456",
            "track_name": "",  # Empty
            "artist_name": "Queen",
            "album_name": "Opera",
            "genre": "Rock",
            "popularity": "80",
            "duration_ms": "200000",
            "explicit": "0",
            "year": "1975"
        }
        is_valid, reason, _ = self.validator.validate_record(row)
        self.assertFalse(is_valid)
        self.assertIn("MISSING_REQUIRED_FIELD_TRACK_NAME", reason)

    def test_popularity_bounds(self):
        # Negative
        row_neg = {
            "track_id": "TRK123", "track_name": "Song", "artist_name": "Band", "genre": "Pop",
            "popularity": "-5", "duration_ms": "180000", "explicit": "0", "year": "2020"
        }
        is_valid, reason, _ = self.validator.validate_record(row_neg)
        self.assertFalse(is_valid)
        self.assertIn("POPULARITY_OUT_OF_BOUNDS", reason)

        # > 100
        row_over = {
            "track_id": "TRK123", "track_name": "Song", "artist_name": "Band", "genre": "Pop",
            "popularity": "105", "duration_ms": "180000", "explicit": "0", "year": "2020"
        }
        is_valid, reason, _ = self.validator.validate_record(row_over)
        self.assertFalse(is_valid)
        self.assertIn("POPULARITY_OUT_OF_BOUNDS", reason)

    def test_duration_bounds(self):
        row_short = {
            "track_id": "TRK123", "track_name": "Song", "artist_name": "Band", "genre": "Pop",
            "popularity": "50", "duration_ms": "500", "explicit": "0", "year": "2020"
        }
        is_valid, reason, _ = self.validator.validate_record(row_short)
        self.assertFalse(is_valid)
        self.assertIn("DURATION_OUT_OF_BOUNDS", reason)

    def test_invalid_explicit_flag(self):
        row_bad_exp = {
            "track_id": "TRK123", "track_name": "Song", "artist_name": "Band", "genre": "Pop",
            "popularity": "50", "duration_ms": "180000", "explicit": "5", "year": "2020"
        }
        is_valid, reason, _ = self.validator.validate_record(row_bad_exp)
        self.assertFalse(is_valid)
        self.assertIn("INVALID_EXPLICIT_FLAG", reason)

if __name__ == "__main__":
    unittest.main()
