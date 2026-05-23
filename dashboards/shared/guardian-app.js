(function () {
  const live = window.EHODR.live;
  const etaMin = window.EHODR.etaMinutes;

  const els = {
    patient: document.getElementById("patient-name"),
    status: document.getElementById("transit-status"),
    etaBadge: document.getElementById("eta-badge"),
    speed: document.getElementById("speed-value"),
    distance: document.getElementById("distance-value"),
    timeline: document.getElementById("journey-timeline"),
    handover: document.getElementById("handover-eta"),
    chat: document.getElementById("chat-messages"),
    forms: document.getElementById("required-forms"),
    coordinator: document.getElementById("coordinator-name"),
    coordinatorStatus: document.getElementById("coordinator-status"),
  };

  let lastChatLen = 0;

  function statusIcon(step) {
    if (step.status === "done") {
      return '<div class="absolute left-0 top-1 w-6 h-6 rounded-full bg-secondary flex items-center justify-center"><span class="material-symbols-outlined text-white text-sm">check</span></div>';
    }
    if (step.status === "active") {
      return '<div class="absolute left-0 top-1 w-6 h-6 rounded-full bg-secondary active-pulse flex items-center justify-center"><div class="w-2 h-2 bg-white rounded-full"></div></div>';
    }
    return '<div class="absolute left-0 top-1 w-6 h-6 rounded-full bg-surface-container-highest flex items-center justify-center"><div class="w-2 h-2 bg-outline rounded-full"></div></div>';
  }

  function renderTimeline(steps) {
    return steps
      .map(function (step) {
        const active = step.status === "active";
        const pending = step.status === "pending";
        return (
          '<div class="relative pl-xl">' +
          statusIcon(step) +
          '<div class="' +
          (pending ? "opacity-50" : "") +
          '"><p class="font-body-bold' +
          (active ? " text-secondary" : "") +
          '">' +
          step.title +
          '</p><p class="text-sm text-on-surface-variant">' +
          step.detail +
          " • " +
          step.time +
          (active ? " (Current)" : "") +
          "</p></div></div>"
        );
      })
      .join("");
  }

  function renderChat(messages, typing) {
    let html = messages
      .map(function (m) {
        const out = m.from === "guardian";
        return (
          '<div class="' +
          (out ? "bg-primary text-white p-md rounded-lg self-end" : "bg-surface-container-low p-md rounded-lg self-start") +
          ' max-w-[85%]"><p class="text-sm">' +
          m.text +
          '</p><p class="text-[10px] mt-1 ' +
          (out ? "text-on-primary-container" : "text-on-surface-variant") +
          '">' +
          m.time +
          "</p></div>"
        );
      })
      .join("");
    if (typing) {
      html +=
        '<div id="typing-indicator" class="text-[10px] text-on-surface-variant italic self-start">Coordinator is typing...</div>';
    }
    return html;
  }

  function renderForms(forms) {
    return forms
      .map(function (f) {
        if (f.status === "complete") {
          return (
            '<div class="flex items-center justify-between p-sm border border-outline-variant rounded-lg bg-surface-container-low">' +
            '<div class="flex items-center gap-sm"><span class="material-symbols-outlined text-on-surface-variant">description</span><span class="text-sm">' +
            f.label +
            '</span></div><span class="material-symbols-outlined text-secondary">check_circle</span></div>'
          );
        }
        if (f.id === "insurance") {
          return (
            '<button type="button" id="upload-insurance" class="w-full flex items-center justify-between p-sm border border-outline-variant rounded-lg border-dashed bg-surface-container-low hover:border-primary transition-colors">' +
            '<div class="flex items-center gap-sm"><span class="material-symbols-outlined text-primary">add_a_photo</span><span class="text-sm font-body-bold">' +
            f.label +
            '</span></div><span class="material-symbols-outlined text-primary">arrow_forward</span></button>'
          );
        }
        return (
          '<div class="flex items-center justify-between p-sm border border-outline-variant rounded-lg hover:bg-surface-container-low cursor-pointer">' +
          '<div class="flex items-center gap-sm"><span class="material-symbols-outlined text-on-surface-variant">medical_information</span><span class="text-sm">' +
          f.label +
          '</span></div><span class="text-xs bg-error-container text-on-error-container px-2 py-0.5 rounded font-bold">URGENT</span></div>'
        );
      })
      .join("");
  }

  function render(s) {
    const mins = etaMin(s.transport.etaSeconds);
    const dest = s.transport.destinationName;
    if (els.patient) els.patient.textContent = "Patient: " + s.patient.name;
    if (els.status) els.status.textContent = "In Transit to " + dest;
    if (els.etaBadge) els.etaBadge.textContent = "EST. ARRIVAL: " + mins + " MINS";
    if (els.speed) {
      els.speed.innerHTML = s.transport.speedMph + ' <span class="text-sm font-normal">mph</span>';
    }
    if (els.distance) {
      els.distance.innerHTML =
        s.transport.distanceMi + ' <span class="text-sm font-normal">mi</span>';
    }
    if (els.timeline) els.timeline.innerHTML = renderTimeline(s.guardian.timeline);
    if (els.handover) {
      const est = new Date();
      est.setMinutes(est.getMinutes() + mins);
      els.handover.textContent =
        "Expected arrival in " + mins + " minutes • Est. " + est.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
    }
    if (els.chat) {
      const shouldScroll = s.guardian.chat.length > lastChatLen;
      els.chat.innerHTML = renderChat(s.guardian.chat, s.guardian.typing);
      if (shouldScroll) els.chat.scrollTop = els.chat.scrollHeight;
      lastChatLen = s.guardian.chat.length;
    }
    if (els.forms) {
      els.forms.innerHTML = renderForms(s.guardian.forms);
      document.getElementById("upload-insurance")?.addEventListener("click", function () {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "image/*,.pdf";
        input.onchange = function () {
          if (input.files?.[0]) alert("Uploaded: " + input.files[0].name + " (demo)");
        };
        input.click();
      });
    }
    if (els.coordinator) els.coordinator.textContent = s.guardian.coordinator.name;
    if (els.coordinatorStatus) {
      els.coordinatorStatus.textContent =
        "Medical Coordinator • " + (s.guardian.coordinator.online ? "Online" : "Away");
    }
  }

  live.onUpdate(render);
  live.start();

  document.getElementById("chat-send")?.addEventListener("click", sendChat);
  document.getElementById("chat-input")?.addEventListener("keydown", function (e) {
    if (e.key === "Enter") sendChat();
  });

  async function sendChat() {
    const input = document.getElementById("chat-input");
    const text = input?.value.trim();
    if (!text) return;
    input.value = "";
    await live.post("/api/chat", { text });
    await live.poll();
  }

  document.getElementById("call-coordinator")?.addEventListener("click", function () {
    const phone = live.state?.guardian?.coordinator?.phone || "+18005551234";
    window.location.href = "tel:" + phone;
  });

  document.getElementById("record-search")?.addEventListener("input", function (e) {
    if (e.target.value.length > 2) {
      e.target.classList.add("ring-2", "ring-secondary");
    } else {
      e.target.classList.remove("ring-2", "ring-secondary");
    }
  });

  document.getElementById("share-status")?.addEventListener("click", async function () {
    const s = live.state;
    const text = s
      ? s.patient.name + " — In transit to " + s.transport.destinationName + " (ETA " + etaMin(s.transport.etaSeconds) + " min)"
      : "EHODR status";
    const url = window.location.href;
    if (navigator.share) {
      await navigator.share({ title: "EHODR Guardian Status", text: text, url: url });
    } else if (navigator.clipboard) {
      await navigator.clipboard.writeText(text + "\n" + url);
      alert("Status copied to clipboard.");
    }
  });

  document.querySelector('[data-nav="dispatch"]')?.addEventListener("click", () => {
    alert("Active Journey: Unit 704 en route to " + (live.state?.transport.destinationName || "St. Jude Medical Center") + ".");
  });

  document.querySelector('[data-nav="records"]')?.addEventListener("click", () => {
    const s = live.state;
    if (s) {
      alert("📋 Guardian Patient Records Intake\n" +
            "---------------------------------\n" +
            "Patient: " + s.patient.name + "\n" +
            "Condition: " + s.patient.condition + "\n" +
            "Age/Priority: " + s.patient.age + " / " + s.patient.priority + "\n" +
            "Handover Bay: " + s.hospital.traumaBay + "\n" +
            "UAMS Secure Storage: Connected");
    }
  });

  document.querySelector('[data-nav="map"]')?.addEventListener("click", () => {
    window.open("http://127.0.0.1:8501", "_blank");
  });

  document.getElementById("privacy-btn")?.addEventListener("click", () => {
    alert("🔒 Privacy Policy & HIPAA Compliance\n" +
          "---------------------------------\n" +
          "All patient vitals and telemetry streams are encrypted en-route using AES-256 standards.\n" +
          " Relational UAMS memories are fully compliant with clinical HIPAA requirements.");
  });

  document.getElementById("terms-btn")?.addEventListener("click", () => {
    alert("⚖️ Terms of Service\n" +
          "---------------------------------\n" +
          "EHODR provides active disaster decision-support telemetry.\n" +
          "Intake forms and pre-registration uploads represent official triage documentations.");
  });

  document.getElementById("support-btn")?.addEventListener("click", () => {
    alert("ℹ️ Guardian Support Center\n" +
          "---------------------------------\n" +
          "Family Support Desk: ext 911\n" +
          "Emergency Bay Lead: Sarah Mitchell\n" +
          "Radio Dispatch Feed: Online");
  });
})();
