#!/usr/bin/env python3
"""
EHODR Live Dashboard Server
- Serves static files from dashboards/
- Ticks shared state every second (vitals, ETA, distance, incoming units)
- GET  /api/state  → full JSON state snapshot
- POST /api/chat   → append chat message, return coordinator reply
- POST /api/action → log_med | override | update_triage
"""
import json, math, random, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# ──────────────────────────────────────────────────────
# Shared live state (all dashboards read this)
# ──────────────────────────────────────────────────────
_lock = threading.Lock()

STATE: dict = {
    "case": "772-B",
    "unit": "704",
    "patient": {"name": "Johnathan Doe", "age": 45, "condition": "TRAUMA L1", "priority": "PRIORITY 1"},
    "vitals": {"hr": 104, "spo2": 96, "bp_sys": 128, "bp_dia": 84},
    "eta_seconds": 480,
    "distance_km": 5.2,
    "speed_kmh": 65.0,
    "triage_level": "RED - CRITICAL (TRAUMA)",
    "hospital": "St. Jude Medical Center",
    "bay": "ER Bay 4",
    "er_capacity": {"beds_available": 3, "beds_total": 24, "trauma_available": 1, "trauma_total": 4},
    "incoming_units": [
        {"id": "704", "type": "BLS-A", "condition": "Chest Pain, Tachypnea", "patient": "45M", "severity": "CRITICAL",
         "eta": 8, "vital_label": "HEART RATE", "vital_value": 104},
        {"id": "302", "type": "BLS-A", "condition": "Chest Pain, Tachypnea", "patient": "58M", "severity": "CRITICAL",
         "eta": 4, "vital_label": "HEART RATE", "vital_value": 142},
        {"id": "119", "type": "ALS-B", "condition": "Lower Limb Fracture",   "patient": "22F", "severity": "STABLE",
         "eta": 12, "vital_label": "O2 SAT",    "vital_value": 98},
        {"id": "045", "type": "RESCUE","condition": "Dispatched to MVA A-12","patient": "—",   "severity": "PENDING DATA",
         "eta": 19, "vital_label": "STATUS",    "vital_value": "EN ROUTE"},
    ],
    "chat_messages": [
        {"from": "coordinator", "text": "Hello. I'm the coordinator for Unit 704. Johnathan is stable and receiving supplemental oxygen. Any questions?", "time": "14:18"},
        {"from": "family",      "text": "Thank you. Which entrance at St. Mary's?", "time": "14:22"},
        {"from": "coordinator", "text": "Head directly to Emergency Bay A. I've pre-registered your arrival.", "time": "14:23"},
    ],
    "enroute_log": [
        {"text": "Intravenous Started", "detail": "20 ml Saline | R-Arm"},
    ],
    "override_active": False,
    "tick": 0,
}

COORDINATOR_REPLIES = [
    "Copy that. Coordinator is monitoring Unit 704 and will update you shortly.",
    "Understood. The medical team has been informed.",
    "We are approaching the hospital entrance now. Please proceed to Emergency Bay A.",
    "Patient vitals are stable — being transmitted to the ER team in real time.",
    "Acknowledged. The trauma team is standing by at Bay 4.",
    "Please remain calm. Johnathan is in good hands with our team.",
]


def _tick_loop():
    while True:
        time.sleep(1)
        with _lock:
            s = STATE
            s["tick"] += 1
            t = s["tick"]

            # ETA + distance countdown
            if s["eta_seconds"] > 0:
                s["eta_seconds"] = max(0, s["eta_seconds"] - 1)
                s["distance_km"] = round(max(0.0, s["distance_km"] - s["speed_kmh"] / 3600), 2)

            # Speed sinusoidal fluctuation
            s["speed_kmh"] = round(58 + 15 * abs(math.sin(t * 0.1)), 1)

            # Vitals fluctuation every 3 s
            if t % 3 == 0:
                v = s["vitals"]
                v["hr"]   = max(96, min(120, v["hr"]   + random.randint(-1, 2)))
                if random.random() > 0.6:
                    v["spo2"] = max(93, min(99, v["spo2"] + random.choice([-1, 0, 1])))

            # Incoming unit ETAs every 15 s
            if t % 15 == 0:
                for u in s["incoming_units"]:
                    eta = u["eta"]
                    if isinstance(eta, int) and eta > 1 and random.random() > 0.3:
                        u["eta"] = eta - 1

            # Keep Unit 704 row in sync with live vitals + ETA
            for u in s["incoming_units"]:
                if u["id"] == "704":
                    u["vital_value"] = s["vitals"]["hr"]
                    u["eta"] = max(0, math.ceil(s["eta_seconds"] / 60))


threading.Thread(target=_tick_loop, daemon=True).start()

# ──────────────────────────────────────────────────────
# HTTP handler
# ──────────────────────────────────────────────────────
DASHBOARD_DIR = Path(__file__).parent

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css":  "text/css",
    ".js":   "application/javascript",
    ".json": "application/json",
    ".png":  "image/png",
    ".ico":  "image/x-icon",
    ".svg":  "image/svg+xml",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silence default access log

    def _json(self, data, status=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _static(self, path: Path):
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(path.suffix.lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        url = self.path.split("?")[0]
        if url == "/api/state":
            with _lock:
                self._json(dict(STATE))
            return
        if url == "/":
            url = "/index.html"
        fp = DASHBOARD_DIR / url.lstrip("/")
        if fp.exists() and fp.is_file():
            self._static(fp)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        url = self.path.split("?")[0]

        if url == "/api/chat":
            msg = body.get("text", "").strip()
            if msg:
                now = time.strftime("%H:%M")
                with _lock:
                    STATE["chat_messages"].append({"from": "family",      "text": msg,                           "time": now})
                    reply = random.choice(COORDINATOR_REPLIES)
                    STATE["chat_messages"].append({"from": "coordinator", "text": reply,                         "time": now})
                self._json({"ok": True, "reply": reply})
            else:
                self._json({"ok": False})
            return

        if url == "/api/action":
            act = body.get("action")
            with _lock:
                if act == "log_med":
                    STATE["enroute_log"].append({"text": "Medication Logged", "detail": body.get("detail", "Medication administered")})
                elif act == "override":
                    STATE["override_active"] = True
                elif act == "update_triage":
                    STATE["triage_level"] = body.get("level", STATE["triage_level"])
            self._json({"ok": True})
            return

        self._json({"error": "not found"}, 404)


if __name__ == "__main__":
    port = 8080
    httpd = HTTPServer(("", port), Handler)
    print(f"\n[EHODR] Live dashboard server running at http://localhost:{port}")
    print(f"[EHODR]    Hub:        http://localhost:{port}/")
    print(f"[EHODR]    Ambulance:  http://localhost:{port}/ambulance.html")
    print(f"[EHODR]    Guardian:   http://localhost:{port}/guardian.html")
    print(f"[EHODR]    ER Command: http://localhost:{port}/er-command.html")
    print(f"[EHODR]    Live API:   http://localhost:{port}/api/state\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[EHODR] Dashboard server stopped.")
