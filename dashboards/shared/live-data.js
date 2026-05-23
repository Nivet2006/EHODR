(function (global) {
  const API_BASE = "";
  const POLL_MS = 1000;

  function formatEta(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0") + " MIN";
  }

  function etaMinutes(seconds) {
    return Math.max(1, Math.ceil(seconds / 60));
  }

  const MOCK_STATE = {
    case: {
      id: "772-B",
      label: "TRAUMA L1",
      triageLevel: "RED - CRITICAL (TRAUMA)",
    },
    patient: {
      name: "Johnathan Doe",
      age: 45,
      condition: "TRAUMA L1",
      priority: "PRIORITY 1"
    },
    vitals: {
      heartRate: 104,
      spo2: 96,
      bpSystolic: 128,
      bpDiastolic: 84,
      bpMean: 98
    },
    transport: {
      etaSeconds: 480,
      distanceKm: 5.2,
      distanceMi: 3.2,
      speedMph: 40.0,
      speedKmh: 65.0,
      traffic: "MODERATE",
      navigationHint: "Main St. Clear — Take 4th exit",
      destinationName: "St. Jude Medical Center",
      destinationDetail: "ER Bay 4"
    },
    hospital: {
      traumaBay: "Bay #4 Secured",
      traumaBayNote: "Team scrubbed in. Blood units O- ready.",
      specialist: {
        name: "Dr. Sarah Vance",
        role: "NEUROSURGEON"
      }
    },
    enRouteLog: [
      {title: "Intravenous Started", detail: "20 ml Saline | R-Arm", time: "17:40"},
      {title: "Oxygen Therapy", detail: "15L/min Non-Rebreather", time: "17:45"}
    ],
    guardian: {
      timeline: [
        {title: "Ambulance Dispatched", detail: "Unit 704 responding", time: "17:15", status: "done"},
        {title: "En Route to Hospital", detail: "ETA 8 minutes", time: "17:20", status: "active"},
        {title: "ER Handover", detail: "Trauma Bay #4 standing by", time: "pending", status: "pending"}
      ],
      chat: [
        {from: "coordinator", text: "Hello. I'm the coordinator for Unit 704. Johnathan is stable and receiving supplemental oxygen. Any questions?", time: "17:18"},
        {from: "guardian",    text: "Thank you. Which entrance at St. Jude's?", time: "17:22"},
        {from: "coordinator", text: "Head directly to Emergency Bay 4. I've pre-registered your arrival.", time: "17:23"}
      ],
      typing: false,
      forms: [
        {id: "insurance", label: "Upload Health Insurance Card", status: "pending"},
        {id: "consent",   label: "Emergency Consent Form",       status: "complete"}
      ],
      coordinator: {
        name: "Sarah Jenkins",
        online: true,
        phone: "+18005551234"
      }
    },
    er: {
      massTraumaAlert: false,
      activeUnitsCount: 4,
      incomingUnits: [
        {
          isPrimary: true,
          etaMinutes: 8,
          statusTone: "error",
          status: "CRITICAL",
          label: "BLS-A (Unit 704)",
          complaint: "Chest Pain, Tachypnea (45M)",
          metricLabel: "HEART RATE",
          metricValue: 104,
          search: "704 critical chest pain"
        },
        {
          isPrimary: false,
          etaMinutes: 4,
          statusTone: "error",
          status: "CRITICAL",
          label: "BLS-A (Unit 302)",
          complaint: "Multiple Fractures (58M)",
          metricLabel: "HEART RATE",
          metricValue: 142,
          search: "302 critical fracture"
        },
        {
          isPrimary: false,
          etaMinutes: 12,
          statusTone: "secondary",
          status: "STABLE",
          label: "ALS-B (Unit 119)",
          complaint: "Lower Limb Fracture (22F)",
          metricLabel: "O2 SAT",
          metricValue: 98,
          search: "119 stable fracture"
        },
        {
          isPrimary: false,
          etaMinutes: 19,
          statusTone: "neutral",
          status: "PENDING DATA",
          label: "RESCUE (Unit 045)",
          complaint: "Dispatched to MVA A-12",
          metricLabel: "STATUS",
          metricValue: "EN ROUTE",
          search: "045 pending mva"
        }
      ],
      capacity: {
        bedsAvailable: 3,
        bedsTotal: 24,
        bedsUsedPct: 87,
        traumaBaysAvailable: 1,
        traumaBaysTotal: 4,
        traumaBaysUsedPct: 75,
        staff: "14 Physicians / 28 Nurses"
      },
      surgicalTeams: [
        {or: "OR 1 (Cardiac)", status: "ACTIVE (IN-SURGERY)", tone: "error"},
        {or: "OR 2 (Trauma)", status: "ON STANDBY", tone: "secondary"},
        {or: "OR 3 (General)", status: "AVAILABLE", tone: "neutral"}
      ],
      region: "Bangalore Metro Area",
      facility: {
        bloodBank: "82 units (O- critical)",
        imaging: "CT 1 online, CT 2 online",
        lab: "Running (12m turnaround)",
        security: "Level 2 Alert Active"
      }
    },
    flags: {
      emergencyOverride: false
    },
    updatedAt: new Date().toISOString(),
    tick: 0,
    unit: {
      id: "704"
    }
  };

  const MOCK_REPLIES = [
    "Copy that. Coordinator is monitoring Unit 704 and will update you shortly.",
    "Understood. The medical team has been informed.",
    "We are approaching the hospital entrance now. Please proceed to Emergency Bay 4.",
    "Patient vitals are stable — being transmitted to the ER team in real time.",
    "Acknowledged. The trauma team is standing by at Bay 4.",
    "Please remain calm. Johnathan is in good hands with our team.",
  ];

  class LiveDataClient {
    constructor() {
      this.state = null;
      this.listeners = new Set();
      this._timer = null;
      this._connected = false;
      this.isMock = false;
    }

    onUpdate(fn) {
      this.listeners.add(fn);
      return () => this.listeners.delete(fn);
    }

    async fetchState() {
      const res = await fetch(API_BASE + "/api/state", { cache: "no-store" });
      if (!res.ok) throw new Error("API " + res.status);
      return res.json();
    }

    async post(path, body) {
      if (this.isMock) {
        this.simulateAction(path, body);
        return { ok: true };
      }
      const res = await fetch(API_BASE + path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body || {}),
      });
      if (!res.ok) throw new Error("API " + res.status);
      return res.json();
    }

    simulateAction(path, body) {
      const s = this.state;
      if (!s) return;
      const now = new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });

      if (path === "/api/actions/update-triage") {
        s.case.triageLevel = body.level || s.case.triageLevel;
      }
      else if (path === "/api/actions/emergency-override") {
        s.flags.emergencyOverride = true;
        s.transport.traffic = "CRITICAL";
        s.er.incomingUnits.forEach((u) => {
          if (u.isPrimary) {
            u.status = "OVERRIDE";
            u.statusTone = "error";
          }
        });
      }
      else if (path === "/api/actions/enroute-log") {
        s.enRouteLog.push({
          title: body.title || "Action logged",
          detail: body.detail || "",
          time: now
        });
      }
      else if (path === "/api/actions/dismiss-alert") {
        s.er.massTraumaAlert = false;
      }
      else if (path === "/api/actions/activate-protocol") {
        s.er.massTraumaAlert = true;
        s.er.capacity.traumaBaysAvailable = 0;
        s.er.capacity.traumaBaysUsedPct = 100;
      }
      else if (path === "/api/chat") {
        const text = body.text || "";
        if (text) {
          s.guardian.chat.push({ from: "guardian", text: text, time: now });
          s.guardian.typing = true;
          this.triggerUpdate();

          // Simulate coordinator typing reply after 1.5s
          setTimeout(() => {
            s.guardian.typing = false;
            const reply = MOCK_REPLIES[Math.floor(Math.random() * MOCK_REPLIES.length)];
            s.guardian.chat.push({ from: "coordinator", text: reply, time: now });
            this.triggerUpdate();
          }, 1500);
        }
      }
      this.triggerUpdate();
    }

    tickSimulation() {
      const s = this.state;
      if (!s) return;
      s.tick += 1;
      const t = s.tick;
      s.updatedAt = new Date().toISOString();

      // ETA + distance countdown
      if (s.transport.etaSeconds > 0) {
        s.transport.etaSeconds = Math.max(0, s.transport.etaSeconds - 1);
        s.transport.distanceKm = Math.round(Math.max(0.0, s.transport.distanceKm - s.transport.speedKmh / 3600) * 100) / 100;
        s.transport.distanceMi = Math.round((s.transport.distanceKm * 0.621371) * 100) / 100;
      }

      // Speed sinusoidal fluctuation
      s.transport.speedKmh = Math.round((58 + 15 * Math.abs(Math.sin(t * 0.1))) * 10) / 10;
      s.transport.speedMph = Math.round((s.transport.speedKmh * 0.621371) * 10) / 10;

      // Vitals fluctuation every 3 ticks
      if (t % 3 === 0) {
        const v = s.vitals;
        v.heartRate = Math.max(96, Math.min(120, v.heartRate + (Math.random() > 0.5 ? 1 : -1)));
        if (Math.random() > 0.6) {
          v.spo2 = Math.max(93, Math.min(99, v.spo2 + (Math.random() > 0.5 ? 1 : -1)));
        }
        v.bpMean = Math.round(v.bpDiastolic + (v.bpSystolic - v.bpDiastolic) / 3);
      }

      // Incoming unit ETAs every 15 ticks
      if (t % 15 === 0) {
        s.er.incomingUnits.forEach((u) => {
          if (!u.isPrimary && typeof u.etaMinutes === "number" && u.etaMinutes > 1 && Math.random() > 0.3) {
            u.etaMinutes -= 1;
          }
        });
      }

      // Sync Unit 704 row with primary EKG
      s.er.incomingUnits.forEach((u) => {
        if (u.isPrimary) {
          u.metricValue = s.vitals.heartRate;
          u.etaMinutes = Math.max(0, Math.ceil(s.transport.etaSeconds / 60));
        }
      });

      this.triggerUpdate();
    }

    triggerUpdate() {
      this.listeners.forEach((fn) => fn(this.state));
    }

    async poll() {
      try {
        const next = await this.fetchState();
        this._connected = true;
        this.isMock = false;
        this.state = next;
        this.triggerUpdate();
        document.body.classList.remove("ehodr-api-offline");
      } catch (err) {
        this._connected = false;
        document.body.classList.add("ehodr-api-offline");
        
        // Unreachable API -> activate dynamic local simulation
        if (!this.isMock) {
          console.log("[EHODR] Live API unavailable — Running client-side simulation.");
          this.isMock = true;
          this.state = JSON.parse(JSON.stringify(MOCK_STATE));
          this.triggerUpdate();
        }
        
        this.tickSimulation();
      }
    }

    start() {
      this.poll();
      this._timer = setInterval(() => this.poll(), POLL_MS);
    }

    stop() {
      if (this._timer) clearInterval(this._timer);
    }
  }

  global.EHODR = global.EHODR || {};
  global.EHODR.live = new LiveDataClient();
  global.EHODR.formatEta = formatEta;
  global.EHODR.etaMinutes = etaMinutes;
})(window);
