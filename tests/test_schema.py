import unittest
import json
import os

class TestSchemaContract(unittest.TestCase):
    def setUp(self):
        self.schema_path = "config/schemas/music_schema.json"

    def test_schema_file_exists(self):
        self.assertTrue(os.path.exists(self.schema_path), "Schema JSON file must exist.")

    def test_schema_properties(self):
        with open(self.schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        self.assertEqual(schema.get("type"), "object")
        props = schema.get("properties", {})
        expected_fields = [
            "track_id", "track_name", "artist_name", "album_name",
            "genre", "popularity", "duration_ms", "explicit", "year"
        ]
        for field in expected_fields:
            self.assertIn(field, props, f"Field '{field}' must be present in schema properties.")

    def test_required_fields(self):
        with open(self.schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        required = schema.get("required", [])
        for field in ["track_id", "track_name", "artist_name", "genre", "popularity"]:
            self.assertIn(field, required, f"Field '{field}' must be marked as required.")

    def test_numeric_ranges(self):
        with open(self.schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        pop = schema["properties"]["popularity"]
        self.assertEqual(pop.get("minimum"), 0)
        self.assertEqual(pop.get("maximum"), 100)

        dur = schema["properties"]["duration_ms"]
        self.assertEqual(dur.get("minimum"), 1000)
        self.assertEqual(dur.get("maximum"), 3600000)

if __name__ == "__main__":
    unittest.main()
