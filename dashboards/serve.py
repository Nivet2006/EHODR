#!/usr/bin/env python3
"""
EHODR Live Dashboard Server
- Serves static files from dashboards/
- Ticks shared state every second (vitals, ETA, distance, incoming units)
- GET  /api/state           → full JSON state snapshot
- POST /api/chat            → append chat message, return coordinator reply
- POST /api/actions/*       → update-triage, emergency-override, enroute-log, dismiss-alert, activate-protocol
"""
import json
import math
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# ──────────────────────────────────────────────────────
# Shared live state (all dashboards read this)
# ──────────────────────────────────────────────────────
_lock = threading.Lock()

STATE: dict = {
    "case": {
        "id": "772-B",
        "label": "TRAUMA L1",
        "triageLevel": "RED - CRITICAL (TRAUMA)",
    },
    "patient": {
        "name": "Johnathan Doe",
        "age": 45,
        "condition": "TRAUMA L1",
        "priority": "PRIORITY 1"
    },
    "vitals": {
        "heartRate": 104,
        "spo2": 96,
        "bpSystolic": 128,
        "bpDiastolic": 84,
        "bpMean": 98
    },
    "transport": {
        "etaSeconds": 480,
        "distanceKm": 5.2,
        "distanceMi": 3.2,
        "speedMph": 40.0,
        "speedKmh": 65.0,
        "traffic": "MODERATE",
        "navigationHint": "Main St. Clear — Take 4th exit",
        "destinationName": "St. Jude Medical Center",
        "destinationDetail": "ER Bay 4"
    },
    "hospital": {
        "traumaBay": "Bay #4 Secured",
        "traumaBayNote": "Team scrubbed in. Blood units O- ready.",
        "specialist": {
            "name": "Dr. Sarah Vance",
            "role": "NEUROSURGEON"
        }
    },
    "enRouteLog": [
        {"title": "Intravenous Started", "detail": "20 ml Saline | R-Arm", "time": "17:40"},
        {"title": "Oxygen Therapy", "detail": "15L/min Non-Rebreather", "time": "17:45"}
    ],
    "guardian": {
        "timeline": [
            {"title": "Ambulance Dispatched", "detail": "Unit 704 responding", "time": "17:15", "status": "done"},
            {"title": "En Route to Hospital", "detail": "ETA 8 minutes", "time": "17:20", "status": "active"},
            {"title": "ER Handover", "detail": "Trauma Bay #4 standing by", "time": "pending", "status": "pending"}
        ],
        "chat": [
            {"from": "coordinator", "text": "Hello. I'm the coordinator for Unit 704. Johnathan is stable and receiving supplemental oxygen. Any questions?", "time": "17:18"},
            {"from": "guardian",    "text": "Thank you. Which entrance at St. Jude's?", "time": "17:22"},
            {"from": "coordinator", "text": "Head directly to Emergency Bay 4. I've pre-registered your arrival.", "time": "17:23"}
        ],
        "typing": False,
        "forms": [
            {"id": "insurance", "label": "Upload Health Insurance Card", "status": "pending"},
            {"id": "consent",   "label": "Emergency Consent Form",       "status": "complete"}
        ],
        "coordinator": {
            "name": "Sarah Jenkins",
            "online": True,
            "phone": "+18005551234"
        }
    },
    "er": {
        "massTraumaAlert": False,
        "activeUnitsCount": 4,
        "incomingUnits": [
            {
                "isPrimary": True,
                "etaMinutes": 8,
                "statusTone": "error",
                "status": "CRITICAL",
                "label": "BLS-A (Unit 704)",
                "complaint": "Chest Pain, Tachypnea (45M)",
                "metricLabel": "HEART RATE",
                "metricValue": 104,
                "search": "704 critical chest pain"
            },
            {
                "isPrimary": False,
                "etaMinutes": 4,
                "statusTone": "error",
                "status": "CRITICAL",
                "label": "BLS-A (Unit 302)",
                "complaint": "Multiple Fractures (58M)",
                "metricLabel": "HEART RATE",
                "metricValue": 142,
                "search": "302 critical fracture"
            },
            {
                "isPrimary": False,
                "etaMinutes": 12,
                "statusTone": "secondary",
                "status": "STABLE",
                "label": "ALS-B (Unit 119)",
                "complaint": "Lower Limb Fracture (22F)",
                "metricLabel": "O2 SAT",
                "metricValue": 98,
                "search": "119 stable fracture"
            },
            {
                "isPrimary": False,
                "etaMinutes": 19,
                "statusTone": "neutral",
                "status": "PENDING DATA",
                "label": "RESCUE (Unit 045)",
                "complaint": "Dispatched to MVA A-12",
                "metricLabel": "STATUS",
                "metricValue": "EN ROUTE",
                "search": "045 pending mva"
            }
        ],
        "capacity": {
            "bedsAvailable": 3,
            "bedsTotal": 24,
            "bedsUsedPct": 87,
            "traumaBaysAvailable": 1,
            "traumaBaysTotal": 4,
            "traumaBaysUsedPct": 75,
            "staff": "14 Physicians / 28 Nurses"
        },
        "surgicalTeams": [
            {"or": "OR 1 (Cardiac)", "status": "ACTIVE (IN-SURGERY)", "tone": "error"},
            {"or": "OR 2 (Trauma)", "status": "ON STANDBY", "tone": "secondary"},
            {"or": "OR 3 (General)", "status": "AVAILABLE", "tone": "neutral"}
        ],
        "region": "Bangalore Metro Area",
        "facility": {
            "bloodBank": "82 units (O- critical)",
            "imaging": "CT 1 online, CT 2 online",
            "lab": "Running (12m turnaround)",
            "security": "Level 2 Alert Active"
        }
    },
    "flags": {
        "emergencyOverride": False
    },
    "updatedAt": "",
    "tick": 0,
    "unit": {
        "id": "704"
    }
}

COORDINATOR_REPLIES = [
    "Copy that. Coordinator is monitoring Unit 704 and will update you shortly.",
    "Understood. The medical team has been informed.",
    "We are approaching the hospital entrance now. Please proceed to Emergency Bay 4.",
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

            s["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            # ETA + distance countdown
            if s["transport"]["etaSeconds"] > 0:
                s["transport"]["etaSeconds"] = max(0, s["transport"]["etaSeconds"] - 1)
                s["transport"]["distanceKm"] = round(max(0.0, s["transport"]["distanceKm"] - s["transport"]["speedKmh"] / 3600), 2)
                s["transport"]["distanceMi"] = round(s["transport"]["distanceKm"] * 0.621371, 2)

            # Speed sinusoidal fluctuation
            s["transport"]["speedKmh"] = round(58 + 15 * abs(math.sin(t * 0.1)), 1)
            s["transport"]["speedMph"] = round(s["transport"]["speedKmh"] * 0.621371, 1)

            # Vitals fluctuation every 3 s
            if t % 3 == 0:
                v = s["vitals"]
                v["heartRate"] = max(96, min(120, v["heartRate"] + random.randint(-1, 2)))
                if random.random() > 0.6:
                    v["spo2"] = max(93, min(99, v["spo2"] + random.choice([-1, 0, 1])))
                v["bpMean"] = round(v["bpDiastolic"] + (v["bpSystolic"] - v["bpDiastolic"]) / 3)

            # Incoming unit ETAs every 15 s
            if t % 15 == 0:
                for u in s["er"]["incomingUnits"]:
                    if u["isPrimary"]:
                        continue
                    if isinstance(u["etaMinutes"], int) and u["etaMinutes"] > 1 and random.random() > 0.3:
                        u["etaMinutes"] = u["etaMinutes"] - 1

            # Keep Unit 704 row in sync with live vitals + ETA
            for u in s["er"]["incomingUnits"]:
                if u["isPrimary"]:
                    u["metricValue"] = s["vitals"]["heartRate"]
                    u["etaMinutes"] = max(0, math.ceil(s["transport"]["etaSeconds"] / 60))


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
                self._json(STATE)
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
                    STATE["guardian"]["chat"].append({"from": "guardian", "text": msg, "time": now})
                    reply = random.choice(COORDINATOR_REPLIES)
                    STATE["guardian"]["chat"].append({"from": "coordinator", "text": reply, "time": now})
                self._json({"ok": True, "reply": reply})
            else:
                self._json({"ok": False})
            return

        if url == "/api/actions/update-triage":
            level = body.get("level", "").strip()
            if level:
                with _lock:
                    STATE["case"]["triageLevel"] = level
                self._json({"ok": True})
            else:
                self._json({"ok": False})
            return

        if url == "/api/actions/emergency-override":
            with _lock:
                STATE["flags"]["emergencyOverride"] = True
                STATE["transport"]["traffic"] = "CRITICAL"
                # Update status of primary unit to OVERRIDE
                for u in STATE["er"]["incomingUnits"]:
                    if u["isPrimary"]:
                        u["status"] = "OVERRIDE"
                        u["statusTone"] = "error"
            self._json({"ok": True})
            return

        if url == "/api/actions/enroute-log":
            title = body.get("title", "Medication logged").strip()
            detail = body.get("detail", "").strip()
            now = time.strftime("%H:%M")
            with _lock:
                STATE["enRouteLog"].append({"title": title, "detail": detail, "time": now})
            self._json({"ok": True})
            return

        if url == "/api/actions/dismiss-alert":
            with _lock:
                STATE["er"]["massTraumaAlert"] = False
            self._json({"ok": True})
            return

        if url == "/api/actions/activate-protocol":
            with _lock:
                STATE["er"]["massTraumaAlert"] = True
                STATE["er"]["capacity"]["traumaBaysAvailable"] = 0
                STATE["er"]["capacity"]["traumaBaysUsedPct"] = 100
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
