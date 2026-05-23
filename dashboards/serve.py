"""
EHODR command dashboard server: static files + live JSON API.
Run: python dashboards/serve.py  (from repo root)
"""

from __future__ import annotations

import json
import random
import threading
import time
from datetime import datetime, timedelta
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
PORT = 8080

_lock = threading.Lock()
_state: dict = {}


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _now_clock() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _initial_state() -> dict:
    base = datetime.now().replace(hour=14, minute=2, second=0, microsecond=0)
    return {
        "updatedAt": _now_iso(),
        "case": {
            "id": "772-B",
            "label": "TRAUMA L1",
            "priority": 1,
            "triageLevel": "RED - CRITICAL (TRAUMA)",
        },
        "unit": {"id": "704", "status": "ON-CALL", "callSign": "Unit 704"},
        "patient": {
            "name": "Johnathan Doe",
            "age": 34,
            "sex": "M",
            "chiefComplaint": "Multi-system trauma — MVC",
        },
        "vitals": {
            "heartRate": 104,
            "spo2": 96,
            "bpSystolic": 128,
            "bpDiastolic": 84,
            "bpMean": 98,
            "sensor": "APEX-4",
        },
        "transport": {
            "destinationName": "St. Jude Medical Center",
            "destinationDetail": "ER Bay 4",
            "etaSeconds": 262,
            "distanceKm": 1.4,
            "distanceMi": 3.2,
            "traffic": "MODERATE",
            "speedMph": 42,
            "navigationHint": "Main St. Clear — Take 4th exit",
            "progress": 0.62,
        },
        "hospital": {
            "traumaBay": "Bay #4 Secured",
            "traumaBayNote": "Team scrubbed in. Blood units O- ready.",
            "ready": True,
            "specialist": {
                "name": "Dr. Sarah Vance",
                "role": "NEUROSURGEON",
                "image": "https://lh3.googleusercontent.com/aida-public/AB6AXuDe0qys7at5wBunqx5pok1ggKF5RmQHL3b1b_htTb8TSPkjSGUIbZtWUogInLB06NBqXPkjEq688rzjTyozRpoAkoJRJc8wywcd6h4I1Rjj7Rrqw0Q3IcDkC78ddR8xn_sT7nmvf4DydHPoupz5BIbpFKKqAwf6ObMp6Hw9sVJhE_3McLUQogJ9YF1rBU05YspBMc0tj7C6Is4KwzWHGcywj9soH8h_t1giIbYBmq-rBdKqYiwGhPeXy4mslr9VYNIrUWw0OsV7nM0",
            },
        },
        "enRouteLog": [
            {
                "time": _now_clock(),
                "title": "Intravenous Started",
                "detail": "20ml Saline | R-Arm",
            }
        ],
        "guardian": {
            "coordinator": {
                "name": "Sarah Mitchell",
                "online": True,
                "phone": "+18005551234",
            },
            "timeline": [
                {
                    "id": "t1",
                    "title": "Ambulance Dispatched",
                    "detail": "Unit 704 departed from Central Station",
                    "time": (base).strftime("%H:%M"),
                    "status": "done",
                },
                {
                    "id": "t2",
                    "title": "On-Site Stabilization",
                    "detail": "Medical team arrived at scene, vitals stabilized",
                    "time": (base + timedelta(minutes=13)).strftime("%H:%M"),
                    "status": "done",
                },
                {
                    "id": "t3",
                    "title": "Transporting to Hospital",
                    "detail": "En route to St. Jude Medical Center",
                    "time": (base + timedelta(minutes=26)).strftime("%H:%M"),
                    "status": "active",
                },
                {
                    "id": "t4",
                    "title": "ER Handover",
                    "detail": "Expected upon ambulance arrival",
                    "time": (base + timedelta(minutes=40)).strftime("%H:%M"),
                    "status": "pending",
                },
            ],
            "chat": [
                {
                    "id": "c1",
                    "from": "coordinator",
                    "text": "Hello. I am the coordinator for Unit 704. Johnathan is stable and receiving supplemental oxygen. Do you have any questions?",
                    "time": "14:18",
                },
                {
                    "id": "c2",
                    "from": "guardian",
                    "text": "Thank you. Which entrance should I go to at St. Jude?",
                    "time": "14:22",
                },
                {
                    "id": "c3",
                    "from": "coordinator",
                    "text": "Please head directly to Emergency Bay A. I have pre-registered your arrival.",
                    "time": "14:23",
                },
            ],
            "typing": False,
            "forms": [
                {"id": "consent", "label": "Consent for Treatment", "status": "complete"},
                {"id": "insurance", "label": "Upload Insurance Card", "status": "pending"},
                {"id": "history", "label": "Medical History Form", "status": "urgent"},
            ],
        },
        "er": {
            "massTraumaAlert": True,
            "activeUnitsCount": 5,
            "incomingUnits": [
                {
                    "id": "704",
                    "label": "UNIT-704 (ALS-TRAUMA)",
                    "status": "CRITICAL",
                    "statusTone": "error",
                    "complaint": "MVC Trauma L1 • Pt 34M — Johnathan Doe",
                    "etaMinutes": 4,
                    "metricLabel": "HEART RATE",
                    "metricValue": "104",
                    "search": "704 trauma johnathan doe critical",
                    "isPrimary": True,
                },
                {
                    "id": "302",
                    "label": "UNIT-302 (BLS-A)",
                    "status": "CRITICAL",
                    "statusTone": "error",
                    "complaint": "Chest Pain, Tachypnea • Pt 58M",
                    "etaMinutes": 4,
                    "metricLabel": "HEART RATE",
                    "metricValue": "142",
                    "search": "302 chest pain critical",
                    "isPrimary": False,
                },
                {
                    "id": "119",
                    "label": "UNIT-119 (ALS-B)",
                    "status": "STABLE",
                    "statusTone": "secondary",
                    "complaint": "Lower Limb Fracture • Pt 22F",
                    "etaMinutes": 12,
                    "metricLabel": "O2 SAT",
                    "metricValue": "98%",
                    "search": "119 fracture stable",
                    "isPrimary": False,
                },
                {
                    "id": "045",
                    "label": "UNIT-045 (RESCUE)",
                    "status": "PENDING DATA",
                    "statusTone": "neutral",
                    "complaint": "Dispatched to MVA Location A-12",
                    "etaMinutes": 19,
                    "metricLabel": "STATUS",
                    "metricValue": "EN ROUTE",
                    "search": "045 mva rescue",
                    "isPrimary": False,
                },
            ],
            "capacity": {
                "bedsAvailable": 3,
                "bedsTotal": 24,
                "bedsUsedPct": 88,
                "traumaBaysAvailable": 1,
                "traumaBaysTotal": 4,
                "traumaBaysUsedPct": 75,
                "staff": "12 Physicians • 28 RNs",
            },
            "surgicalTeams": [
                {"or": "OR-01 (General)", "status": "READY", "tone": "secondary"},
                {"or": "OR-02 (Neuro)", "status": "IN-SURGERY", "tone": "error"},
                {"or": "OR-03 (Cardiac)", "status": "TURNOVER", "tone": "neutral"},
            ],
            "facility": {
                "bloodBank": "O- NEG: CRITICAL",
                "imaging": "CT: 14 MINS",
                "lab": "28 SAMPLES PENDING",
                "security": "LEVEL 2 SECURED",
            },
            "region": "Central Metropolitan Zone",
        },
        "flags": {"emergencyOverride": False, "protocolActivated": False},
    }


def _tick_state() -> None:
    with _lock:
        t = _state["transport"]
        if t["etaSeconds"] > 0:
            t["etaSeconds"] -= 1
            t["distanceKm"] = max(0.1, round(t["distanceKm"] - 0.004, 2))
            t["distanceMi"] = max(0.2, round(t["distanceMi"] - 0.002, 1))
            t["progress"] = min(0.98, t["progress"] + 0.0015)
            if random.random() < 0.08:
                t["speedMph"] = max(28, min(52, t["speedMph"] + random.choice([-2, -1, 0, 1, 2])))

        v = _state["vitals"]
        v["heartRate"] = max(98, min(118, v["heartRate"] + random.choice([-2, -1, 0, 1, 2])))
        if random.random() < 0.35:
            v["spo2"] = max(93, min(99, v["spo2"] + random.choice([-1, 0, 1])))

        eta_min = max(1, (t["etaSeconds"] + 59) // 60)
        primary = next((u for u in _state["er"]["incomingUnits"] if u.get("isPrimary")), None)
        if primary:
            primary["etaMinutes"] = eta_min
            primary["metricValue"] = str(v["heartRate"])

        for unit in _state["er"]["incomingUnits"]:
            if unit.get("isPrimary"):
                continue
            if random.random() < 0.04 and unit["etaMinutes"] > 1:
                unit["etaMinutes"] -= 1

        _state["updatedAt"] = _now_iso()


def _simulation_loop() -> None:
    while True:
        time.sleep(1)
        _tick_state()


def get_state() -> dict:
    with _lock:
        return json.loads(json.dumps(_state))


def _append_chat(text: str, sender: str = "guardian") -> dict:
    with _lock:
        msg = {
            "id": f"c{len(_state['guardian']['chat']) + 1}",
            "from": sender,
            "text": text,
            "time": datetime.now().strftime("%H:%M"),
        }
        _state["guardian"]["chat"].append(msg)
        return msg


def _coordinator_reply(delay: float = 1.2) -> None:
    def _reply() -> None:
        time.sleep(delay)
        with _lock:
            _state["guardian"]["typing"] = True
        time.sleep(1.5)
        replies = [
            "Copy that. We are monitoring Unit 704 vitals in real time.",
            "Ambulance is still en route. Bay #4 remains secured for Johnathan.",
            "Vitals are stable. I'll notify you when they are 2 minutes out.",
        ]
        with _lock:
            _state["guardian"]["typing"] = False
        _append_chat(random.choice(replies), "coordinator")

    threading.Thread(target=_reply, daemon=True).start()


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format: str, *args) -> None:
        if str(args[0]).startswith("GET /api/"):
            return
        super().log_message(format, *args)

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/state":
            self._send_json(get_state())
            return
        if path == "/api/health":
            self._send_json({"ok": True, "updatedAt": get_state()["updatedAt"]})
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            body = self._read_json()
        except json.JSONDecodeError:
            self._send_json({"error": "invalid json"}, HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/chat":
            text = (body.get("text") or "").strip()
            if not text:
                self._send_json({"error": "empty message"}, HTTPStatus.BAD_REQUEST)
                return
            msg = _append_chat(text, "guardian")
            _coordinator_reply()
            self._send_json({"ok": True, "message": msg, "state": get_state()})
            return

        if path == "/api/actions/emergency-override":
            with _lock:
                _state["flags"]["emergencyOverride"] = True
            self._send_json({"ok": True, "state": get_state()})
            return

        if path == "/api/actions/update-triage":
            with _lock:
                _state["case"]["triageLevel"] = body.get("level") or "RED - CRITICAL (TRAUMA)"
            self._send_json({"ok": True, "state": get_state()})
            return

        if path == "/api/actions/activate-protocol":
            with _lock:
                _state["flags"]["protocolActivated"] = True
                _state["er"]["massTraumaAlert"] = False
            self._send_json({"ok": True, "state": get_state()})
            return

        if path == "/api/actions/dismiss-alert":
            with _lock:
                _state["er"]["massTraumaAlert"] = False
            self._send_json({"ok": True, "state": get_state()})
            return

        if path == "/api/actions/enroute-log":
            with _lock:
                entry = {
                    "time": _now_clock(),
                    "title": body.get("title") or "Clinical event logged",
                    "detail": body.get("detail") or "",
                }
                _state["enRouteLog"].insert(0, entry)
                _state["enRouteLog"] = _state["enRouteLog"][:8]
            self._send_json({"ok": True, "state": get_state()})
            return

        self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)


def main() -> None:
    global _state
    _state = _initial_state()
    threading.Thread(target=_simulation_loop, daemon=True).start()

    server = ThreadingHTTPServer(("", PORT), DashboardHandler)
    print(f"[EHODR] Live dashboards + API at http://localhost:{PORT}")
    print(f"        API: GET http://localhost:{PORT}/api/state")
    print("        Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[EHODR] Stopped.")


if __name__ == "__main__":
    main()
