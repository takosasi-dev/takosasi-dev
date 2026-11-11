"use strict";
/* The transfer gate. The station signs in the READMEs of the featured repos link here:
       line/?from=<repo>&go=prev|next
   The line is the list "line" in ../data.json (rebuilt every day), joined into a ring. The visitor is sent
   to the neighbour of <from>, so a sign pasted once keeps working when the line changes.

   Where to go is always built from a name in that list. "from" and "go" are only compared with it:
   nothing from the address bar is ever put into a link. Not on the line, or no data: the profile. */
(() => {
  const { C, Board, width, fit } = LED;
  const HOME = "https://github.com/takosasi-dev";
  const NAME = /^[A-Za-z0-9._-]{1,100}$/;
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = id => document.getElementById(id);
  const q = new URLSearchParams(location.search);
  const from = (q.get("from") || "").toLowerCase(), back = q.get("go") === "prev";

  const WAIT = 1200;   // ms the board shows the next station before the visitor is sent on
  let head = "のりかえ案内", name = "案内を読んでいます", col = C.GREEN, t0 = 0;
  const b = new Board($("board"), [402, 180], [46, 62]);
  function frame(ms) {
    const N = b.narrow, show = fit(name, b.cols - 12);
    b.begin();
    b.text(head, 7, 5, C.GREEN, { invert: true });
    if (N) b.text(show, (b.cols - width(show)) >> 1, 32, col);
    else b.text(fit(name, (b.cols - 116) >> 1), 110, 4, col, { scale: 2 });
    // the bar along the bottom fills while the visitor waits (drawn full at once when motion is reduced)
    if (t0) b.rect(0, b.rows - 3, Math.ceil(b.cols * (calm ? 1 : Math.min(1, (performance.now() - t0) / WAIT))), 2, C.GREEN);
    b.end();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  /* The neighbour of `from` on the ring, or null. line: [{repo, name}] already checked. */
  function neighbour(line) {
    const i = line.findIndex(s => s.repo.toLowerCase() === from);
    return i < 0 ? null : line[(i + (back ? line.length - 1 : 1)) % line.length];
  }

  function send(url, label, title, text, colour) {
    [head, name, col, t0] = [title, text, colour, performance.now()];
    const a = $("go");
    a.href = url;
    a.lastChild.textContent = label;
    $("say").textContent = `${title} ${text}。まもなくご案内します`;
    setTimeout(() => location.replace(url), WAIT);   // replace: the back button returns to the README, not to this gate
  }

  fetch("../data.json", { cache: "no-cache" })
    .then(r => (r.ok ? r.json() : Promise.reject(r.status)))
    .then(d => {
      const line = (Array.isArray(d.line) ? d.line.slice(0, 20) : []).filter(s => s && NAME.test(s.repo))
        .map(s => ({ repo: s.repo, name: typeof s.name === "string" && s.name ? s.name.slice(0, 40) : s.repo }));
      const to = neighbour(line);
      if (!to) throw new Error("not on the line");
      LED.addGlyphs(d.glyphs);
      Rally.stamp("line");   // passing the gate is one of the six stamps of the concourse
      send(`${HOME}/${encodeURIComponent(to.repo)}`, to.repo, back ? "前の駅は" : "次は", to.name, C.AMBER);
    })
    .catch(() => {   // no data, or not a station of the line
      if (!t0) send(HOME, "GitHub のプロフィール", "ご案内", "プロフィールへ", C.GREEN);
    });
})();
