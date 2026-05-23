(function () {
  const live = window.EHODR.live;
  const fmt = window.EHODR.formatEta;

  // Leaflet map elements and high-fidelity Bangalore route coordinate path
  let map, marker, hospitalMarker, routeLine;
  const ROUTE_COORDS = [
    [12.9716, 77.5946], // Kantarava Stadium / Central Bangalore
    [12.9705, 77.5995], // Hudson Circle
    [12.9668, 77.6067], // Richmond Road
    [12.9642, 77.6134], // Richmond Flyover
    [12.9628, 77.6210], // Victoria Layout
    [12.9610, 77.6285], // Domlur Flyover
    [12.9598, 77.6360], // Inner Ring Rd junction
    [12.9595, 77.6410], // Old Airport Road
    [12.9592, 77.6444]  // St. Jude Medical Center / Destination
  ];

  function interpolateRoute(coords, progress) {
    if (progress <= 0) return coords[0];
    if (progress >= 1) return coords[coords.length - 1];
    
    const totalSegments = coords.length - 1;
    const rawIndex = progress * totalSegments;
    const segmentIndex = Math.floor(rawIndex);
    const segmentProgress = rawIndex - segmentIndex;
    
    const start = coords[segmentIndex];
    const end = coords[segmentIndex + 1];
    
    const lat = start[0] + (end[0] - start[0]) * segmentProgress;
    const lon = start[1] + (end[1] - start[1]) * segmentProgress;
    
    return [lat, lon];
  }

  function initMap(mapId) {
    const el = document.getElementById(mapId);
    if (!el || typeof L === 'undefined') return;

    try {
      map = L.map(mapId, {
        zoomControl: false,
        attributionControl: false
      }).setView([12.9628, 77.6210], 13);

      // CartoDB Positron sleek gray tile layer
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 20
      }).addTo(map);

      // Custom divIcon for glowing pulsing ambulance marker
      const ambulanceIcon = L.divIcon({
        className: 'custom-map-marker',
        html: '<div class="w-6 h-6 bg-primary rounded-full border-2 border-white flex items-center justify-center shadow-lg"><span class="material-symbols-outlined text-white text-xs" style="font-variation-settings: \'FILL\' 1; font-size: 14px;">emergency_share</span></div>',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });

      // Custom divIcon for hospital
      const hospitalIcon = L.divIcon({
        className: 'custom-hospital-marker',
        html: '<div class="w-8 h-8 bg-secondary rounded-full border-2 border-white flex items-center justify-center shadow-lg"><span class="material-symbols-outlined text-white text-sm" style="font-variation-settings: \'FILL\' 1; font-size: 18px;">local_hospital</span></div>',
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      });

      // Plot solid dotted route line
      routeLine = L.polyline(ROUTE_COORDS, {
        color: '#1E3A8A',
        weight: 4,
        opacity: 0.8,
        dashArray: '5, 8'
      }).addTo(map);

      hospitalMarker = L.marker(ROUTE_COORDS[ROUTE_COORDS.length - 1], { icon: hospitalIcon }).addTo(map);
      hospitalMarker.bindPopup('<b>St. Jude Medical Center</b><br>Emergency Intake Bay 4');

      marker = L.marker(ROUTE_COORDS[0], { icon: ambulanceIcon }).addTo(map);
      
      // Open hospital popup by default
      setTimeout(() => hospitalMarker.openPopup(), 500);
    } catch (e) {
      console.error("Map initialization failed: ", e);
    }
  }

  const els = {
    case: document.getElementById("case-label"),
    triage: document.getElementById("triage-level"),
    eta: document.getElementById("eta-display"),
    hr: document.getElementById("heart-rate-value"),
    spo2: document.getElementById("spo2-value"),
    spo2Bar: document.getElementById("spo2-bar"),
    bp: document.getElementById("bp-value"),
    dest: document.getElementById("dest-name"),
    distKm: document.getElementById("dist-km"),
    traffic: document.getElementById("traffic-level"),
    navHint: document.getElementById("nav-hint"),
    traumaBay: document.getElementById("trauma-bay"),
    traumaNote: document.getElementById("trauma-note"),
    specialistName: document.getElementById("specialist-name"),
    specialistRole: document.getElementById("specialist-role"),
    enrouteList: document.getElementById("enroute-log-list"),
    liveBadge: document.getElementById("live-sync-badge"),
  };

  function render(s) {
    if (els.case) els.case.textContent = "CASE #" + s.case.id + " | " + s.case.label;
    if (els.triage) els.triage.textContent = s.case.triageLevel;
    if (els.eta) els.eta.textContent = fmt(s.transport.etaSeconds);
    if (els.hr) {
      els.hr.innerHTML =
        s.vitals.heartRate + ' <span class="text-sm font-body-base">Normal 60-100</span>';
    }
    if (els.spo2) {
      els.spo2.innerHTML =
        s.vitals.spo2 + ' <span class="text-sm font-body-base">SpO2 Target 94+</span>';
    }
    if (els.spo2Bar) els.spo2Bar.style.width = s.vitals.spo2 + "%";
    if (els.bp) {
      els.bp.innerHTML =
        s.vitals.bpSystolic +
        "/" +
        s.vitals.bpDiastolic +
        ' <span class="text-sm font-body-base">Mean ' +
        s.vitals.bpMean +
        "</span>";
    }
    if (els.dest) {
      els.dest.textContent = s.transport.destinationName + " - " + s.transport.destinationDetail;
    }
    if (els.distKm) els.distKm.textContent = s.transport.distanceKm + " km";
    if (els.traffic) els.traffic.textContent = s.transport.traffic;
    if (els.navHint) els.navHint.textContent = s.transport.navigationHint;
    if (els.traumaBay) els.traumaBay.textContent = s.hospital.traumaBay;
    if (els.traumaNote) els.traumaNote.textContent = s.hospital.traumaBayNote;
    if (els.specialistName) els.specialistName.textContent = s.hospital.specialist.name;
    if (els.specialistRole) els.specialistRole.textContent = s.hospital.specialist.role;
    if (els.enrouteList) {
      els.enrouteList.innerHTML = s.enRouteLog
        .map(
          (e) =>
            '<div class="bg-primary text-white p-md rounded-xl flex flex-col gap-sm">' +
            '<div class="flex justify-between items-start"><span class="font-label-caps text-[10px] opacity-70">EN-ROUTE LOG</span>' +
            '<span class="font-label-caps text-[10px] opacity-70">' +
            e.time +
            "</span></div>" +
            '<div class="flex items-center gap-md"><div class="w-1 h-12 bg-secondary rounded-full"></div>' +
            '<div class="flex flex-col"><span class="font-body-bold text-sm">' +
            e.title +
            '</span><span class="text-[10px] opacity-70">' +
            e.detail +
            "</span></div></div></div>"
        )
        .join("");
    }
    if (els.liveBadge) {
      els.liveBadge.textContent = "LIVE • " + new Date(s.updatedAt).toLocaleTimeString();
    }
    if (s.flags.emergencyOverride) {
      document.body.classList.add("ring-4", "ring-error");
    }

    // Dynamic Leaflet Map updates matching simulated GPS ticks
    if (!map) {
      initMap("ambulance-map");
    }
    if (map && marker && s.transport) {
      const progress = Math.max(0, Math.min(1, 1 - (s.transport.distanceKm / 5.2)));
      const currentCoord = interpolateRoute(ROUTE_COORDS, progress);
      marker.setLatLng(currentCoord);
      map.panTo(currentCoord);
    }
  }

  live.onUpdate(render);
  live.start();

  document.getElementById("update-triage")?.addEventListener("click", async () => {
    const level = prompt("Update triage level:", live.state?.case.triageLevel || "");
    if (level) await live.post("/api/actions/update-triage", { level });
    await live.poll();
  });

  document.getElementById("emergency-override")?.addEventListener("click", async () => {
    if (confirm("Activate EMERGENCY OVERRIDE for Unit 704?")) {
      await live.post("/api/actions/emergency-override");
      await live.poll();
    }
  });

  document.querySelector('[data-action="log-meds"]')?.addEventListener("click", async () => {
    await live.post("/api/actions/enroute-log", {
      title: "Medication logged",
      detail: "Fentanyl 50mcg IV | Protocol T-12",
    });
    await live.poll();
  });

  document.querySelector('[data-nav="dispatch"]')?.addEventListener("click", () => {
    alert("Active Dispatch: Unit 704 responding to CASE #" + (live.state?.case.id || "772-B") + ".");
  });

  document.querySelector('[data-nav="records"]')?.addEventListener("click", () => {
    const s = live.state;
    if (s) {
      alert("📋 Active Patient Intake Record\n" +
            "---------------------------------\n" +
            "Name: " + s.patient.name + " (" + s.patient.age + "M)\n" +
            "Triage Priority: " + s.patient.priority + "\n" +
            "Condition: " + s.patient.condition + "\n" +
            "UAMS Relational ID: MEM-2026-" + s.case.id);
    }
  });

  document.querySelector('[data-nav="map"]')?.addEventListener("click", () => {
    window.open("http://127.0.0.1:8501", "_blank");
  });

  document.querySelector('[data-nav="comms"]')?.addEventListener("click", () => {
    alert("📡 Secure radio channel active.\nFamily tracker link shared via Guardian Portal.");
  });

  document.getElementById("settings-btn")?.addEventListener("click", () => {
    alert("⚙️ Ambulance Cockpit Settings\n" +
          "---------------------------------\n" +
          "Telemetry Interval: 1000ms\n" +
          "GPS Navigation: Active (OSRM)\n" +
          "System State: Fully Synchronized");
  });

  document.getElementById("support-btn")?.addEventListener("click", () => {
    alert("ℹ️ EHODR Cockpit Support\n" +
          "---------------------------------\n" +
          "Disaster Response Desk: ext 911\n" +
          "Central Coordinator: Sarah Jenkins\n" +
          "Local System: v2.4.6 (Stable)");
  });
})();
