#!/usr/bin/env python3
"""
Unit Tests for Datacenter/Web to HDFS, SQL to HDFS, and MongoDB NoSQL Engines.
"""

import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "pipeline"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "nosql"))

from sql_hdfs_connector import init_sql_database, DB_PATH
from mongo_manager import EmbeddedMongoStore

class TestNoSQLAndSQLBridges(unittest.TestCase):
    def test_sql_database_initialization(self):
        init_sql_database(sample_size=10)
        self.assertTrue(os.path.exists(DB_PATH))

        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM tracks")
        cnt = cur.fetchone()[0]
        conn.close()
        self.assertGreater(cnt, 0)

    def test_mongo_embedded_aggregation(self):
        test_dir = os.path.join(PROJECT_ROOT, "results", "scratch", "test_mongo")
        store = EmbeddedMongoStore(test_dir)
        col = store.get_collection("test_tracks")
        col.delete_many({})

        col.insert_many([
            {"track_id": "T1", "genre": "Rock", "popularity": 80, "duration_sec": 200},
            {"track_id": "T2", "genre": "Rock", "popularity": 90, "duration_sec": 220},
            {"track_id": "T3", "genre": "Pop", "popularity": 70, "duration_sec": 180}
        ])

        pipeline = [
            {
                "$group": {
                    "_id": "$genre",
                    "total_tracks": {"$sum": 1},
                    "avg_popularity": {"$avg": "$popularity"}
                }
            },
            {"$sort": {"avg_popularity": -1}}
        ]
        results = col.aggregate(pipeline)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["_id"], "Rock")
        self.assertEqual(results[0]["avg_popularity"], 85.0)
        self.assertEqual(results[0]["total_tracks"], 2)

if __name__ == "__main__":
    unittest.main()
