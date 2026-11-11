"use strict";
/* The stamp rally of the concourse: six stamps, kept in this browser only (localStorage, never sent anywhere).
   Storage may be missing or refuse to work (private windows, blocked site data): then the stamps of this
   visit are kept in memory and the pages go on as usual. What is read back is checked, never trusted. */
const Rally = (() => {
  const KEY = "takosasi-dev.rally";
  const IDS = ["gate", "bell", "packet", "eyes", "line", "kisaragi"];
  const mem = {};   // id -> time, the stamps pressed on this page

  function read() {
    const out = { ...mem };
    try {
      const o = JSON.parse(localStorage.getItem(KEY) || "{}");
      for (const id of IDS) if (o && Number.isFinite(o[id]) && o[id] > 0) out[id] = o[id];
    } catch (e) { /* no storage: this visit only */ }
    return out;
  }

  /* Press one stamp. True if it is new. */
  function stamp(id) {
    if (!IDS.includes(id)) return false;
    const s = read();
    if (s[id]) return false;
    s[id] = mem[id] = Date.now();
    try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) { /* kept in mem */ }
    return true;
  }

  return { IDS, read, stamp };
})();
