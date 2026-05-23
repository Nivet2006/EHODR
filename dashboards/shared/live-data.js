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

  class LiveDataClient {
    constructor() {
      this.state = null;
      this.listeners = new Set();
      this._timer = null;
      this._connected = false;
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
      const res = await fetch(API_BASE + path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body || {}),
      });
      if (!res.ok) throw new Error("API " + res.status);
      return res.json();
    }

    async poll() {
      try {
        const next = await this.fetchState();
        this._connected = true;
        this.state = next;
        this.listeners.forEach((fn) => fn(next));
        document.body.classList.remove("ehodr-api-offline");
      } catch (err) {
        this._connected = false;
        document.body.classList.add("ehodr-api-offline");
        console.warn("[EHODR] Live API unavailable — start serve.py", err);
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
