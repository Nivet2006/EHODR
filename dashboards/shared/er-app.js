(function () {
  const live = window.EHODR.live;

  const els = {
    alert: document.getElementById("mass-trauma-alert"),
    units: document.getElementById("incoming-units"),
    activeCount: document.getElementById("active-units-count"),
    beds: document.getElementById("beds-available"),
    trauma: document.getElementById("trauma-bays"),
    staff: document.getElementById("staff-on-call"),
    surgical: document.getElementById("surgical-teams"),
    facility: document.getElementById("facility-stats"),
    region: document.getElementById("region-name"),
    primaryHr: document.getElementById("primary-unit-hr"),
  };

  let searchQuery = "";

  const toneMap = {
    error: { badge: "bg-error-container text-error", eta: "bg-error-container text-error" },
    secondary: { badge: "bg-secondary-container text-secondary", eta: "bg-secondary-container text-secondary" },
    neutral: { badge: "bg-surface-container text-on-surface-variant", eta: "bg-surface-container-highest text-on-surface-variant" },
  };

  function renderUnit(u) {
    const t = toneMap[u.statusTone] || toneMap.neutral;
    const eta = String(u.etaMinutes).padStart(2, "0");
    const hidden = searchQuery && u.search.toLowerCase().indexOf(searchQuery) === -1;
    return (
      '<div class="unit-card flex items-center gap-md p-md border border-outline-variant rounded-xl hover:bg-surface-container-low transition-colors' +
      (u.isPrimary ? " ring-2 ring-primary/30" : "") +
      '" data-search="' +
      u.search +
      '" style="' +
      (hidden ? "display:none" : "") +
      '">' +
      '<div class="w-12 h-12 flex flex-col items-center justify-center ' +
      t.eta +
      ' rounded-lg"><span class="font-label-caps text-[10px]">ETA</span><span class="unit-eta font-stat-vitals text-stat-vitals leading-tight">' +
      eta +
      "</span></div>" +
      '<div class="flex-1"><div class="flex justify-between"><p class="font-body-bold text-primary">' +
      u.label +
      '</p><span class="font-label-caps text-xs px-2 rounded ' +
      t.badge +
      '">' +
      u.status +
      '</span></div><p class="text-on-surface-variant text-sm">' +
      u.complaint +
      '</p></div><div class="text-right mr-4"><p class="text-[10px] text-outline font-label-caps">' +
      u.metricLabel +
      '</p><p class="font-stat-vitals text-xl text-primary">' +
      u.metricValue +
      "</p></div></div>"
    );
  }

  function renderSurgical(teams) {
    return teams
      .map(function (t) {
        const bg =
          t.tone === "secondary"
            ? "bg-secondary-container/20"
            : t.tone === "error"
              ? "bg-error-container/20"
              : "bg-surface-container-high";
        const dot =
          t.tone === "secondary" ? "bg-secondary" : t.tone === "error" ? "bg-error" : "bg-outline";
        const statusClass =
          t.tone === "secondary" ? "text-secondary" : t.tone === "error" ? "text-error" : "text-on-surface-variant";
        return (
          '<div class="flex items-center justify-between p-sm rounded-lg ' +
          bg +
          '"><div class="flex items-center gap-md"><div class="w-2 h-2 rounded-full ' +
          dot +
          '"></div><span class="text-sm font-body-bold text-primary">' +
          t.or +
          '</span></div><span class="text-xs font-label-caps ' +
          statusClass +
          '">' +
          t.status +
          "</span></div>"
        );
      })
      .join("");
  }

  function render(s) {
    if (els.alert) {
      els.alert.style.display = s.er.massTraumaAlert ? "" : "none";
    }
    if (els.units) {
      els.units.innerHTML = s.er.incomingUnits.map(renderUnit).join("");
    }
    if (els.activeCount) els.activeCount.textContent = s.er.activeUnitsCount + " ACTIVE UNITS";
    const c = s.er.capacity;
    if (els.beds) {
      els.beds.innerHTML =
        String(c.bedsAvailable).padStart(2, "0") +
        '<span class="text-sm font-body-base text-outline ml-1">/ ' +
        c.bedsTotal +
        "</span>";
      document.getElementById("beds-bar").style.width = c.bedsUsedPct + "%";
    }
    if (els.trauma) {
      els.trauma.innerHTML =
        String(c.traumaBaysAvailable).padStart(2, "0") +
        '<span class="text-sm font-body-base text-outline ml-1">/ ' +
        c.traumaBaysTotal +
        "</span>";
      document.getElementById("trauma-bar").style.width = c.traumaBaysUsedPct + "%";
    }
    if (els.staff) els.staff.textContent = c.staff;
    if (els.surgical) els.surgical.innerHTML = renderSurgical(s.er.surgicalTeams);
    if (els.region) els.region.textContent = s.er.region;
    const f = s.er.facility;
    if (els.facility) {
      document.getElementById("stat-blood").textContent = f.bloodBank;
      document.getElementById("stat-imaging").textContent = f.imaging;
      document.getElementById("stat-lab").textContent = f.lab;
      document.getElementById("stat-security").textContent = f.security;
    }
    const primary = s.er.incomingUnits.find((u) => u.isPrimary);
    if (primary && els.primaryHr) {
      els.primaryHr.textContent = primary.metricValue;
    }
    if (s.flags.emergencyOverride) document.body.classList.add("ring-4", "ring-error");
  }

  live.onUpdate(render);
  live.start();

  document.getElementById("unit-search")?.addEventListener("input", function (e) {
    searchQuery = e.target.value.trim().toLowerCase();
    if (live.state) render(live.state);
  });

  document.getElementById("dismiss-alert")?.addEventListener("click", async () => {
    await live.post("/api/actions/dismiss-alert");
    await live.poll();
  });

  document.getElementById("activate-protocol")?.addEventListener("click", async () => {
    await live.post("/api/actions/activate-protocol");
    await live.poll();
    alert("Mass trauma protocol activated — all trauma bays on standby.");
  });

  document.getElementById("er-emergency-override")?.addEventListener("click", async () => {
    if (confirm("Trigger facility-wide emergency override?")) {
      await live.post("/api/actions/emergency-override");
      await live.poll();
    }
  });

  document.getElementById("new-incident")?.addEventListener("click", function () {
    alert("New incident logged: INC-" + Math.floor(1000 + Math.random() * 9000));
  });

  document.getElementById("map-fullscreen")?.addEventListener("click", function () {
    const img = document.querySelector("#regional-map img");
    if (img?.requestFullscreen) img.requestFullscreen();
  });

  const navLinks = document.querySelectorAll("#sidebar-nav a");
  navLinks.forEach(function (link) {
    link.addEventListener("click", function () {
      navLinks.forEach(function (l) {
        l.classList.remove("bg-primary", "text-on-primary");
        l.classList.add("text-on-surface-variant", "hover:bg-surface-container-high");
      });
      link.classList.add("bg-primary", "text-on-primary");
      link.classList.remove("text-on-surface-variant", "hover:bg-surface-container-high");
    });
  });
})();
