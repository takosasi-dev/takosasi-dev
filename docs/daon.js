"use strict";
/* The hammer test of the concourse: six wheels, one of them cracked. A tap rings the wheel and draws the shape of
   its ring on an LED board, so the cracked one can be found by ear or by eye alone: it rings lower, shorter and
   rougher. Five questions, the difference smaller each time.
   Sound comes from LED.Sound.note(), called only from the click of a wheel and only while the switch
   "ゲームの効果音" is on (it is off when the page opens).

       node docs/daon.js     # self-check of the rules below (nothing of the page is needed for it)
*/
const Daon = (() => {
  const N = 6;
  // What a crack does to a wheel, question 1 to 5: [pitch, length of the ring (both as a share of a sound wheel), roughness 0..1]
  const LEVELS = [[.8, .45, .5], [.86, .58, .35], [.91, .7, .22], [.945, .8, .12], [.97, .88, .06]];
  const REF = 700, WINDOW = 1.8;   // Hz that is drawn 10 dots to a wave; seconds from the left edge of the picture to the right

  /* One question: which wheel is cracked, and how the sound ones ring. The pitch changes from car to car,
     so a wheel has to be compared with its neighbours, not with the last question. */
  function question(level, rnd = Math.random) {
    return { level, bad: Math.floor(rnd() * N), freq: 620 + rnd() * 260, dur: 1.6 };
  }

  /* How wheel i of question q rings: {freq in Hz, dur in seconds, rough 0..1}. */
  function ring(q, i) {
    const [pitch, len, rough] = i === q.bad ? LEVELS[q.level] : [1, 1, 0];
    return { freq: q.freq * pitch, dur: q.dur * len, rough };
  }

  /* The ring as a picture n dots wide: how far each dot sits above or below the middle line, amp at most.
     Lower = wider waves, shorter = dies away sooner, rougher = the outline flutters. */
  function trace(r, n, amp) {
    return Array.from({ length: n }, (_, x) => {
      const t = x / n * WINDOW;
      const flutter = 1 - r.rough * (.5 + .5 * Math.sin(2 * Math.PI * 11 * t));
      return Math.round(amp * Math.exp(-5 * t / r.dur) * flutter * Math.sin(2 * Math.PI * x / 10 * r.freq / REF));
    });
  }

  const rank = score => (score >= 5 ? "検車区の主任級" : score >= 3 ? "一人前の検車係" : score >= 1 ? "見習い検車係" : "本日は非番です");

  return { N, LEVELS, question, ring, trace, rank };
})();

if (typeof document !== "undefined") (() => {
  const { C, Board, Sound } = LED;
  const $ = id => document.getElementById(id);
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const say = s => { $("dn-say").textContent = s; };
  const b = new Board($("dn"), [402, 180], [78, 96]);
  const st = { state: "idle", level: 0, score: 0, q: null, sel: -1, t0: 0, ok: false };
  const LAST = Daon.LEVELS.length - 1;

  const wheels = Array.from({ length: Daon.N }, (_, i) => {
    const w = $("dn-wheels").appendChild(document.createElement("button"));
    w.type = "button";
    w.textContent = i + 1;
    w.addEventListener("click", () => tap(i));
    return w;
  });
  function label() {   // what each wheel is called, and which one is picked
    wheels.forEach((w, i) => {
      const cracked = st.state === "judge" && i === st.q.bad;
      w.setAttribute("aria-label", `車輪 ${i + 1} をたたく` + (cracked ? "(ひびのある車輪)" : ""));
      w.setAttribute("aria-pressed", i === st.sel);
      w.classList.toggle("bad", cracked);
    });
    $("dn-start").textContent = { idle: "はじめる", play: "最初から", judge: st.level < LAST ? "次の車両へ" : "成績を見る", over: "もう一度" }[st.state];
  }

  function ask() {
    Object.assign(st, { state: "play", q: Daon.question(st.level), sel: -1 });
    label();
    say(`第 ${st.level + 1} 問。${Daon.N} 輪のうち 1 輪に、ひびがあります。たたいて確かめてください`);
  }
  function go() {   // the one button that moves the game on
    if (st.state === "judge" && st.level < LAST) {
      st.level++;
      ask();
    } else if (st.state === "judge") {
      Object.assign(st, { state: "over", sel: -1 });
      label();
      say(`検査終了。${LAST + 1} 問中 ${st.score} 問 正解。${Daon.rank(st.score)}`);
    } else {
      st.level = st.score = 0;
      ask();
      Sound.sfx("go");
    }
  }

  function tap(i) {
    if (st.state === "idle" || st.state === "over") go();   // a tap on a wheel is as good as the start button
    const r = Daon.ring(st.q, i);
    if (Sound.on) {   // like every game here it is silent until the visitor turns the effects on; the board shows the same ring
      Sound.note(140, 0, .04, .1, "square");               // the hammer
      Sound.note(r.freq, 0, r.dur, .15);                   // the wheel
      Sound.note(r.freq * 2.76, 0, r.dur * .3, .05);       // steel: an overtone that is not a harmonic
      if (r.rough) Sound.note(r.freq * 1.06, 0, r.dur * .7, .15 * r.rough, "sawtooth");   // the crack buzzes against the ring
    }
    st.sel = i;
    st.t0 = performance.now();
    label();
    wheels[i].classList.remove("hit");
    void wheels[i].offsetWidth;   // so that the same wheel can jump again
    wheels[i].classList.add("hit");
    say(`車輪 ${i + 1} をたたきました`);
  }

  function report() {
    if (st.state !== "play") return;
    if (st.sel < 0) {
      say("先に、あやしい車輪をたたいて選んでください");
      return;
    }
    st.ok = st.sel === st.q.bad;
    if (st.ok) st.score++;
    st.state = "judge";
    label();
    Sound.sfx(st.ok ? "ok" : "ng");
    say(`${st.ok ? "正解" : "不正解"}。ひびがあったのは車輪 ${st.q.bad + 1} です。正解 ${st.score}`);
    $("dn-start").focus();
  }
  $("dn-start").addEventListener("click", go);
  $("dn-report").addEventListener("click", report);

  function draw(ms) {
    const N = b.narrow, R = b.cols - 5, x0 = N ? 3 : 5;
    b.begin();
    if (st.state === "idle") {
      b.text("車輪をたたいて点検", x0, 6, C.AMBER);
      b.text("「はじめる」を押す", x0, 28, C.GREEN);
    } else if (st.state === "over") {
      b.text("検査終了", x0, 6, C.AMBER);
      b.text(`${LAST + 1}問中 ${st.score}問 正解`, N ? x0 : 90, N ? 28 : 6, C.GREEN);
      b.text(Daon.rank(st.score), x0, N ? 50 : 36, C.AMBER, { scale: N ? 1 : 2 });
    } else {
      if (st.state === "play") {
        b.text(`第${st.level + 1}問/${LAST + 1}`, x0, 3, C.GREEN);
        b.text(`正解 ${st.score}`, R, 3, C.AMBER, { right: true });
      } else {
        b.text((st.ok ? "○" : "×") + (N ? "" : " ") + (st.ok ? "正解" : "不正解"), x0, 3, st.ok ? C.GREEN : C.RED);
        b.text(`ひびは 車輪${st.q.bad + 1}`, R, 3, C.AMBER, { right: true });
      }
      const mid = N ? 68 : 49, n = b.cols - 2 * x0;
      if (st.sel < 0) b.text("車輪をたたいてください", x0, mid - 8, C.AMBER);
      else {
        b.text(`車輪${st.sel + 1}`, N ? x0 + 2 : 112, N ? 23 : 3, C.AMBER, { invert: true });
        // The ring is written in from the left as it sounds; all at once for a visitor who asked for less motion.
        const ys = Daon.trace(Daon.ring(st.q, st.sel), n, 22), c = b.ci(C.AMBER);
        const upto = calm ? n : Math.min(n, Math.ceil(n * (ms - st.t0) / 600));
        for (let x = 0, last = 0; x < upto; last = ys[x++])
          for (let y = Math.min(last, ys[x]); y <= Math.max(last, ys[x]); y++) b.dot(x0 + x, mid + y, c);
      }
    }
    b.end();
    requestAnimationFrame(draw);
  }
  label();
  requestAnimationFrame(draw);
})();

if (typeof module !== "undefined") module.exports = Daon;   // for node; a page has no `module`
if (typeof require !== "undefined" && require.main === module) {   // self-check: node docs/daon.js
  const assert = require("assert");
  const { N, LEVELS, question, ring, trace, rank } = Daon;
  // the cracked wheel is anywhere, and not always in the same place
  const seen = Array(N).fill(0);
  for (let i = 0; i < 1200; i++) seen[question(0).bad]++;
  assert(seen.every(n => n > 120 && n < 300), seen);
  assert.deepStrictEqual([0, .5, .999].map(v => question(2, () => v).bad), [0, 3, 5]);
  // question by question the crack tells less: higher, longer, cleaner, but never the same as a sound wheel
  LEVELS.forEach(([p, d, r], i) => {
    assert(p < 1 && d < 1 && r > 0);
    if (i) assert(p > LEVELS[i - 1][0] && d > LEVELS[i - 1][1] && r < LEVELS[i - 1][2]);
  });
  let before = Infinity;
  LEVELS.forEach((_, level) => {
    const q = question(level, () => .5), sound = ring(q, 0), bad = ring(q, q.bad);
    assert(q.bad === 3 && bad.freq < sound.freq && bad.dur < sound.dur && bad.rough > 0);
    for (let i = 0; i < N; i++) if (i !== q.bad) assert.deepStrictEqual(ring(q, i), sound);   // the sound wheels are all alike
    // without sound: on both widths of the board the picture of the cracked wheel differs, less and less
    for (const n of [392, 190]) {
      const a = trace(sound, n, 22), c = trace(bad, n, 22);
      assert(a.length === n && a.every(y => Math.abs(y) <= 22) && c.every(y => Math.abs(y) <= 22));
      assert(a.filter((y, x) => Math.abs(y - c[x]) >= 2).length >= 12, `level ${level}, ${n} dots: too alike to see`);
    }
    const area = y => trace(y, 392, 22).reduce((s, v) => s + Math.abs(v), 0);
    assert(area(sound) - area(bad) < before, "the pictures must come closer with every level");
    before = area(sound) - area(bad);
  });
  assert.deepStrictEqual([0, 1, 3, 5].map(rank), ["本日は非番です", "見習い検車係", "一人前の検車係", "検車区の主任級"]);
  console.log("daon ok");
}
