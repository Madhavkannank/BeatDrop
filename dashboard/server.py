#!/usr/bin/env python3
"""
Dashboard Backend Server for Music Analytics Platform
Serves static dashboard files and provides REST API for Groq song lookup, validation,
and automated pipeline execution.
"""

import os
import sys
import json
import csv
import time
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "ingestion"))

from groq_metadata import fetch_song_metadata
from catalog_search import find_existing_track
from validator import DataValidator

# Pipeline execution tracker
PIPELINE_STATE = {
    "running": False,
    "start_time": 0,
    "elapsed_seconds": 0,
    "current_stage": "IDLE",
    "status": "READY",
    "last_error": None,
    "logs": []
}
STATE_LOCK = threading.Lock()

def run_pipeline_worker():
    global PIPELINE_STATE
    with STATE_LOCK:
        PIPELINE_STATE["running"] = True
        PIPELINE_STATE["start_time"] = time.time()
        PIPELINE_STATE["status"] = "RUNNING"
        PIPELINE_STATE["current_stage"] = "Starting Orchestrator..."
        PIPELINE_STATE["last_error"] = None
        PIPELINE_STATE["logs"] = []

    pipeline_script = os.path.join(PROJECT_ROOT, "pipeline", "run_pipeline.sh")
    sync_script = os.path.join(PROJECT_ROOT, "scripts", "prepare_dashboard_data.py")
    
    try:
        proc = subprocess.Popen(
            [pipeline_script],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in proc.stdout:
            line_str = line.strip()
            with STATE_LOCK:
                PIPELINE_STATE["logs"].append(line_str)
                if len(PIPELINE_STATE["logs"]) > 100:
                    PIPELINE_STATE["logs"].pop(0)
                if ">>> [STAGE" in line_str:
                    PIPELINE_STATE["current_stage"] = line_str.replace(">>>", "").strip()

        proc.wait()
        if proc.returncode == 0:
            # Synchronize dashboard files
            subprocess.run(["python3", sync_script], cwd=PROJECT_ROOT)
            with STATE_LOCK:
                PIPELINE_STATE["status"] = "SUCCESS"
                PIPELINE_STATE["current_stage"] = "Pipeline & Analytics Completed"
        else:
            with STATE_LOCK:
                PIPELINE_STATE["status"] = "FAILED"
                PIPELINE_STATE["last_error"] = f"Pipeline returned exit code {proc.returncode}"
    except Exception as e:
        with STATE_LOCK:
            PIPELINE_STATE["status"] = "ERROR"
            PIPELINE_STATE["last_error"] = str(e)
    finally:
        with STATE_LOCK:
            PIPELINE_STATE["running"] = False
            PIPELINE_STATE["elapsed_seconds"] = int(time.time() - PIPELINE_STATE["start_time"])

class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SCRIPT_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/pipeline/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            with STATE_LOCK:
                state_copy = dict(PIPELINE_STATE)
                if state_copy["running"]:
                    state_copy["elapsed_seconds"] = int(time.time() - state_copy["start_time"])
                # Return last 15 log lines
                state_copy["recent_logs"] = state_copy["logs"][-15:]
            self.wfile.write(json.dumps(state_copy).encode("utf-8"))
            return

        if parsed.path == "/api/search":
            from urllib.parse import parse_qs
            from search_engine import get_search_engine
            qs = parse_qs(parsed.query)
            q = qs.get("q", [""])[0]
            genre = qs.get("genre", ["ALL"])[0]
            sort_by = qs.get("sort", ["popularity"])[0]
            try:
                limit = int(qs.get("limit", [50])[0])
            except ValueError:
                limit = 50

            engine = get_search_engine()
            results = engine.search(query=q, genre=genre, sort_by=sort_by, limit=limit)
            self.send_json_response(200, results)
            return
        
        # Default static file handling
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        
        try:
            req_data = json.loads(body)
        except Exception:
            req_data = {}

        if parsed.path == "/api/song/lookup":
            self.handle_song_lookup(req_data)
        elif parsed.path == "/api/song/ingest":
            self.handle_song_ingest(req_data)
        elif parsed.path == "/api/pipeline/run":
            self.handle_pipeline_run()
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def handle_pipeline_run(self):
        with STATE_LOCK:
            already_running = PIPELINE_STATE["running"]
        if not already_running:
            t = threading.Thread(target=run_pipeline_worker, daemon=True)
            t.start()
            self.send_json_response(200, {"success": True, "message": "Big Data pipeline triggered."})
        else:
            self.send_json_response(200, {"success": True, "message": "Pipeline run already in progress."})

    def handle_song_lookup(self, req_data):
        song_name = req_data.get("song_name", "").strip()
        artist_hint = req_data.get("artist", "").strip() or None
        api_key = req_data.get("api_key", "").strip() or None

        if not song_name:
            self.send_json_error(400, "Song name is required.")
            return

        # 1. Check if track already exists in database
        existing = find_existing_track(song_name, artist_hint)
        if existing:
            self.send_json_response(200, {
                "success": True,
                "metadata": existing,
                "already_in_database": True,
                "source": "database",
                "is_valid": True,
                "validation_reason": "FOUND_IN_CATALOG"
            })
            return

        # 2. Track not in database -> extract via Groq AI
        try:
            metadata = fetch_song_metadata(song_name, artist_hint, api_key)
            
            # Validate against schema
            import yaml
            config_path = os.path.join(PROJECT_ROOT, "config", "application.yaml")
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            validator = DataValidator(config)
            row_str = {k: str(v) for k, v in metadata.items()}
            is_valid, reason, cleaned = validator.validate_record(row_str)

            resp_metadata = cleaned if is_valid else metadata
            if "candidates" in metadata:
                resp_metadata["candidates"] = metadata["candidates"]

            self.send_json_response(200, {
                "success": True,
                "metadata": resp_metadata,
                "already_in_database": False,
                "source": "groq_api",
                "is_valid": is_valid,
                "validation_reason": reason,
                "candidates": metadata.get("candidates", [])
            })
        except Exception as e:
            self.send_json_error(500, str(e))

    def handle_song_ingest(self, req_data):
        metadata = req_data.get("metadata", {})
        run_pipeline = req_data.get("run_pipeline", True)
        already_in_db = req_data.get("already_in_database", False)

        if not metadata or not metadata.get("track_name") or not metadata.get("artist_name"):
            self.send_json_error(400, "Valid track metadata is required.")
            return

        # Append to raw dataset
        import yaml
        config_path = os.path.join(PROJECT_ROOT, "config", "application.yaml")
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        dataset_path = os.path.join(PROJECT_ROOT, config["dataset"]["raw_input_path"])
        expected_cols = config["dataset"]["expected_columns"]

        if not already_in_db:
            try:
                with open(dataset_path, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=expected_cols)
                    row = {col: metadata.get(col, "") for col in expected_cols}
                    writer.writerow(row)
            except Exception as e:
                self.send_json_error(500, f"Failed to append to dataset: {e}")
                return

        # Check if pipeline already running
        with STATE_LOCK:
            already_running = PIPELINE_STATE["running"]

        action_desc = "Track exists in catalog" if already_in_db else "Track appended to dataset"
        if run_pipeline and not already_running:
            t = threading.Thread(target=run_pipeline_worker, daemon=True)
            t.start()
            status_msg = f"{action_desc}. Big Data pipeline execution launched."
        elif already_running:
            status_msg = f"{action_desc}. A pipeline run is already in progress."
        else:
            status_msg = f"{action_desc}. Pipeline run deferred."

        self.send_json_response(200, {
            "success": True,
            "message": status_msg,
            "pipeline_triggered": run_pipeline and not already_running
        })

    def send_json_response(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def send_json_error(self, code, message):
        self.send_json_response(code, {"success": False, "error": message})

def main():
    port = int(os.environ.get("PORT", 8080))
    server_address = ("0.0.0.0", port)
    httpd = ThreadingHTTPServer(server_address, DashboardHandler)
    print(f"Music Analytics Platform Server listening on http://0.0.0.0:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    main()
