"use strict";
/* The live camera: live.svg is the screen of the diorama in the README, where one day goes by in 60 seconds.
   Here everything in it that shows the time of day (the sky, the sun and the moon, lamps, windows) is stopped
   and set to the visitor's own clock, so it is morning there when it is morning here. Trains, the bus, rain and
   blinking lights keep moving. scripts/ext_diorama.py writes on the root of the picture which animations are
   which (data-clock) and where in the 60 seconds the sun comes up (data-up, data-secs).
   Without this script the frame simply shows the 60-second loop. */
(() => {
  const frame = document.getElementById("cam"), box = frame && frame.parentElement, say = document.getElementById("cam-say");
  if (!frame) return;
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Sunrise and sunset in Tokyo in the middle of each month, in hours. The station stands in Tokyo wherever the
  // visitor is; a table is close enough for a picture whose sun moves one dot at a time.
  const SUN = [[6.83, 16.85], [6.5, 17.35], [5.87, 17.8], [5.13, 18.2], [4.63, 18.6], [4.42, 18.97],
               [4.6, 18.92], [5, 18.47], [5.38, 17.77], [5.78, 17.05], [6.25, 16.57], [6.7, 16.5]];
  function sun(d) {
    const m = d.getMonth(), k = (d.getDate() - 15) / 30, a = SUN[m], b = SUN[(m + (k < 0 ? 11 : 1)) % 12];
    return [0, 1].map(i => a[i] + (b[i] - a[i]) * Math.abs(k));
  }
  // The clock as a second of the loop: the day (sunrise to sunset) is `secs` seconds from `up`, the night is the rest.
  function second(d, up, secs) {
    const h = d.getHours() + d.getMinutes() / 60 + d.getSeconds() / 3600, [r, s] = sun(d);
    return (h >= r && h < s ? up + secs * (h - r) / (s - r) : up + secs + (60 - secs) * ((h - s + 24) % 24) / (24 - s + r)) % 60;
  }
  const hm = x => { const t = Math.round(x * 60); return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`; };
  // Between the last train and the first one nothing that is in the timetable runs.
  const closed = d => { const h = d.getHours() + d.getMinutes() / 60; return h >= .75 && h < 4.75; };
  function words(d) {
    const h = d.getHours() + d.getMinutes() / 60, [r, s] = sun(d);
    const part = h < r - 1 ? "深夜" : h < r + .75 ? "夜明け" : h < 11 ? "朝" : h < s - 1.25 ? "昼" : h < s + .6 ? "夕暮れ" : h < 23 ? "夜" : "深夜";
    return `いま ${hm(h)}、${part}の駅前です。` + (closed(d) ? "終電は出ました。始発は 4:45 ごろです。" : `東京の日の出は ${hm(r)} ごろ、日の入りは ${hm(s)} ごろ。`);
  }

  // On a narrow screen the picture is shown twice as large and can be pushed sideways; it starts on the station.
  function fit() {
    const wide = box.scrollWidth > box.clientWidth + 1;
    if (wide && !box.hasAttribute("tabindex")) box.scrollLeft = (box.scrollWidth - box.clientWidth) / 2;
    if (wide) box.tabIndex = 0; else box.removeAttribute("tabindex");
  }
  fit();
  addEventListener("resize", fit);

  let started = false;
  function start() {
    let doc = null;
    try { doc = frame.contentDocument; } catch (e) { /* not ours to read: the plain loop stays */ }
    const root = doc && doc.documentElement;
    if (started || !root || root.localName !== "svg" || !root.dataset.clock || !doc.getAnimations) return;
    started = true;
    // An animation inside a <use> cannot be reached from here, so every <use> becomes a real copy of what it shows.
    for (const u of [...doc.querySelectorAll("use")]) {
      const src = doc.getElementById((u.getAttribute("href") || "").slice(1));
      if (!src) continue;
      const g = doc.createElementNS(root.namespaceURI, "g"), copy = src.cloneNode(true);
      for (const a of u.attributes) if (!["href", "x", "y"].includes(a.name)) g.setAttribute(a.name, a.value);
      if (u.hasAttribute("x")) g.setAttribute("transform", `translate(${u.getAttribute("x")} ${u.getAttribute("y")})`);
      copy.removeAttribute("id");
      g.append(copy);
      u.replaceWith(g);
    }
    // With motion turned off the picture switches its animations off and would always show the same evening.
    // Here it gets them back, and tick() holds every one of them still: a photograph of this moment.
    if (calm) {
      for (const sheet of doc.styleSheets) {
        for (let i = sheet.cssRules.length; i--;) {
          if (/reduced-motion/.test(sheet.cssRules[i].conditionText || "")) sheet.deleteRule(i);
        }
      }
    }
    const clock = new Set(root.dataset.clock.split(" ")), up = +root.dataset.up, secs = +root.dataset.secs;
    function tick() {
      const now = new Date(), s = second(now, up, secs);
      for (const a of doc.getAnimations()) {
        const len = a.effect.getComputedTiming().duration;
        if (clock.has(a.animationName)) { a.pause(); a.currentTime = s / 60 * len; }
        else if (calm) { a.pause(); a.currentTime = .4 * len; }   // a train is at the platform, a firework is open
      }
      for (const el of doc.querySelectorAll(".tr,.bs")) el.style.visibility = closed(now) ? "hidden" : "";   // the train, the bus
      say.textContent = words(now);
    }
    tick();
    setInterval(tick, 20000);
    document.addEventListener("visibilitychange", () => { if (!document.hidden) tick(); });
  }
  frame.addEventListener("load", start);
  start();
})();
