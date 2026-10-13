#!/usr/bin/env python3
"""
PySpark Distributed Analytics Job for Music Analytics Platform
Enforces explicit schemas, DataFrame operations, window functions, and distributed HDFS I/O.
"""

import os
import sys
import yaml
import json
from pyspark.sql import SparkSession, Window
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, LongType, DoubleType
)
from pyspark.sql.functions import (
    col, avg, min, max, count, round, row_number, desc, when, floor
)

def create_spark_session(config: dict) -> SparkSession:
    spark_cfg = config.get("spark", {})
    master = spark_cfg.get("master", "local[*]")
    app_name = spark_cfg.get("app_name", "MusicAnalyticsSpark")
    
    return SparkSession.builder \
        .appName(app_name) \
        .master(master) \
        .config("spark.driver.memory", spark_cfg.get("driver_memory", "2g")) \
        .config("spark.executor.memory", spark_cfg.get("executor_memory", "2g")) \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()

def main():
    config_path = "config/application.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    spark = create_spark_session(config)
    spark.sparkContext.setLogLevel("WARN")

    print("=== [1/6] Loading Processed Data from HDFS with Explicit Schema ===")
    schema = StructType([
        StructField("track_id", StringType(), False),
        StructField("track_name", StringType(), False),
        StructField("artist_name", StringType(), False),
        StructField("album_name", StringType(), True),
        StructField("genre", StringType(), False),
        StructField("popularity", IntegerType(), False),
        StructField("duration_ms", LongType(), False),
        StructField("explicit", IntegerType(), False),
        StructField("year", IntegerType(), False)
    ])

    hdfs_input = "hdfs://localhost:9000/music_project/processed/tracks_processed.tsv"
    raw_df = spark.read \
        .format("csv") \
        .option("delimiter", "\t") \
        .schema(schema) \
        .load(hdfs_input)

    # Column pruning and caching for multi-query reuse
    tracks_df = raw_df.select(
        "track_id", "track_name", "artist_name", "album_name",
        "genre", "popularity", "duration_ms", "explicit", "year"
    ).filter(col("duration_ms") >= 1000).cache()

    total_records = tracks_df.count()
    print(f"Loaded {total_records} valid tracks into Spark DataFrame from HDFS.")

    print("\n=== [2/6] Analytical Transformation 1: Genre Aggregations ===")
    genre_metrics = tracks_df.groupBy("genre").agg(
        count("track_id").alias("total_tracks"),
        round(avg("popularity"), 2).alias("avg_popularity"),
        min("popularity").alias("min_popularity"),
        max("popularity").alias("max_popularity"),
        round(avg("duration_ms") / 1000.0, 1).alias("avg_duration_sec")
    ).orderBy(desc("avg_popularity"))

    genre_metrics.show(10, truncate=False)

    print("\n=== [3/6] Analytical Transformation 2: Artist Catalog Performance ===")
    artist_metrics = tracks_df.groupBy("artist_name").agg(
        count("track_id").alias("total_tracks"),
        round(avg("popularity"), 2).alias("avg_popularity"),
        round(avg("duration_ms") / 1000.0, 1).alias("avg_duration_sec"),
        max("year").alias("latest_year"),
        min("year").alias("earliest_year")
    ).filter(col("total_tracks") >= 15).orderBy(desc("avg_popularity"))

    artist_metrics.show(10, truncate=False)

    print("\n=== [4/6] Analytical Transformation 3: Explicit vs Clean Impact ===")
    explicit_metrics = tracks_df.groupBy("genre", "explicit").agg(
        count("track_id").alias("track_count"),
        round(avg("popularity"), 2).alias("avg_popularity")
    ).orderBy("genre", desc("explicit"))

    explicit_metrics.show(10, truncate=False)

    print("\n=== [5/6] Analytical Transformation 4: Window Function - Top 3 Tracks Per Genre ===")
    window_spec = Window.partitionBy("genre").orderBy(desc("popularity"), desc("year"))
    ranked_tracks = tracks_df.withColumn("rank", row_number().over(window_spec)) \
                             .filter(col("rank") <= 3) \
                             .select("genre", "rank", "track_name", "artist_name", "popularity", "year")

    ranked_tracks.show(15, truncate=False)

    print("\n=== [6/6] Writing Analytical Data Lake Outputs to HDFS (Parquet) and Results ===")
    results_dir = "results/spark"
    os.makedirs(results_dir, exist_ok=True)

    # Convert aggregated metrics to JSON files for dashboard consumption
    genre_data = [row.asDict() for row in genre_metrics.collect()]
    with open(f"{results_dir}/genre_metrics.json", "w", encoding="utf-8") as f:
        json.dump(genre_data, f, indent=2)

    top_artists_data = [row.asDict() for row in artist_metrics.limit(20).collect()]
    with open(f"{results_dir}/top_artists.json", "w", encoding="utf-8") as f:
        json.dump(top_artists_data, f, indent=2)

    top_tracks_data = [row.asDict() for row in ranked_tracks.collect()]
    with open(f"{results_dir}/top_tracks_per_genre.json", "w", encoding="utf-8") as f:
        json.dump(top_tracks_data, f, indent=2)

    # Save to HDFS as Parquet
    hdfs_parquet_genre = "hdfs://localhost:9000/music_project/analytics/spark_genre_metrics.parquet"
    genre_metrics.write.mode("overwrite").parquet(hdfs_parquet_genre)

    hdfs_parquet_ranked = "hdfs://localhost:9000/music_project/analytics/spark_ranked_tracks.parquet"
    ranked_tracks.write.mode("overwrite").parquet(hdfs_parquet_ranked)

    print("Spark analytical outputs written to HDFS Parquet and local JSON results.")
    spark.stop()

if __name__ == "__main__":
    main()
