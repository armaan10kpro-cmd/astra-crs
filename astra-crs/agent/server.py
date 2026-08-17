"""Lightweight Python SSE & REST Server streaming live pipeline & runtime events to the React Dashboard UI."""

from __future__ import annotations

import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CURRENT_STATE: dict[str, Any] = {
    "status": "idle",
    "last_run": None,
    "events": [],
}


class ASTRADashboardHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Silence routine HTTP access logging
        pass

    def _set_cors_headers(self, content_type: str = "application/json"):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", content_type)

    def do_OPTIONS(self):
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/api/status":
            self._set_cors_headers()
            self.end_headers()
            run_json = ROOT / "reports/run.json"
            last_run = json.loads(run_json.read_text()) if run_json.exists() else None
            payload = {
                "status": CURRENT_STATE["status"],
                "last_run": last_run,
                "timestamp": time.time(),
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        elif path in ("/api/pipeline", "/run.json"):
            self._set_cors_headers()
            self.end_headers()
            run_json = ROOT / "reports/run.json"
            content = run_json.read_text() if run_json.exists() else json.dumps({"status": "no_data"})
            self.wfile.write(content.encode("utf-8"))

        elif path == "/proof_of_fix.md":
            self._set_cors_headers("text/markdown")
            self.end_headers()
            run_json = ROOT / "reports/run.json"
            content = "No proof generated yet."
            if run_json.exists():
                fid = json.loads(run_json.read_text()).get("finding_id")
                if fid:
                    p_path = ROOT / "reports" / fid / "proof_of_fix.md"
                    if p_path.exists():
                        content = p_path.read_text()
            self.wfile.write(content.encode("utf-8"))

        elif path == "/patch.diff":
            self._set_cors_headers("text/plain")
            self.end_headers()
            run_json = ROOT / "reports/run.json"
            content = ""
            if run_json.exists():
                fid = json.loads(run_json.read_text()).get("finding_id")
                if fid:
                    p_path = ROOT / "reports" / fid / "patch.diff"
                    if p_path.exists():
                        content = p_path.read_text()
            self.wfile.write(content.encode("utf-8"))

        elif path == "/api/events":
            # Server-Sent Events (SSE) Endpoint
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            try:
                # Send initial state event
                init_msg = f"data: {json.dumps({'type': 'init', 'state': CURRENT_STATE})}\n\n"
                self.wfile.write(init_msg.encode("utf-8"))
                self.wfile.flush()

                while True:
                    time.sleep(1)
                    ping_msg = f"data: {json.dumps({'type': 'ping', 'ts': time.time()})}\n\n"
                    self.wfile.write(ping_msg.encode("utf-8"))
                    self.wfile.flush()
            except (ConnectionResetError, BrokenPipeError):
                pass

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/demo/start":
            self._set_cors_headers()
            self.end_headers()
            CURRENT_STATE["status"] = "running"

            def _run():
                from agent.orchestrator import run_pipeline
                res = run_pipeline(root=ROOT, mode="mock", provider_name="mock", clean=True)
                CURRENT_STATE["status"] = "completed"
                CURRENT_STATE["last_run"] = res

            Thread(target=_run, daemon=True).start()
            self.wfile.write(json.dumps({"status": "started"}).encode("utf-8"))
        else:
            self.send_error(404)


def start_server(port: int = 8080) -> HTTPServer:
    server = HTTPServer(("0.0.0.0", port), ASTRADashboardHandler)
    t = Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    print(f"ASTRA-CRS Dashboard Server listening on http://0.0.0.0:{port}")
    server = HTTPServer(("0.0.0.0", port), ASTRADashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server.")
