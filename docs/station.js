"use strict";
/* The concourse page: the departure board on the real clock, the bell, and the two keyboard games.
   Everything that comes from data.json or from the GitHub API is checked, then drawn as LED dots
   on a canvas or set with textContent. Nothing from outside is ever parsed as HTML. */
(() => {
  const { C, Board, Sound, width, fit, midi } = LED;
  const USER = "takosasi-dev";
  const $ = id => document.getElementById(id);
  const two = n => String(n).padStart(2, "0");
  const pickOf = a => a[Math.floor(Math.random() * a.length)];
  const say = (id, s) => { $(id).textContent = s; };
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const NAME = /^[A-Za-z0-9._-]{1,100}$/, DATE = /^\d{4}-\d\d-\d\d$/;

  // ------------------------------------------------------------------ data
  let data = { repos: [], counts: null, streak: 0, idle: 0, updated: "" };
  let pushes = [];   // [{name, at}] from the API, newest first
  let tick = "ただいま案内のデータを読めません。時計と発車ベル、ゲームはご利用いただけます。　　　";

  function sane(d) {
    const str = (v, n) => (typeof v === "string" ? v.slice(0, n) : "");
    const num = v => (Number.isFinite(v) && v >= 0 ? Math.floor(v) : 0);
    const out = { repos: [], counts: null, streak: num(d.streak), idle: num(d.idle), updated: DATE.test(d.updated) ? d.updated : "" };
    for (const r of Array.isArray(d.repos) ? d.repos.slice(0, 300) : []) {
      if (!r || !NAME.test(r.name)) continue;
      out.repos.push({ name: r.name, cat: str(r.cat, 12), col: str(r.col, 7), desc: str(r.desc, 200), tag: str(r.tag, 24),
                       tag_date: DATE.test(r.tag_date) ? r.tag_date : "", pushed: DATE.test(r.pushed) ? r.pushed : "" });
    }
    if (d.counts && out.repos.length) out.counts = { repos: num(d.counts.repos), releases: num(d.counts.releases), langs: num(d.counts.langs) };
    return out;
  }

  async function load() {
    try {
      const r = await fetch("data.json", { cache: "no-cache" });
      if (!r.ok) throw new Error(r.status);
      const d = await r.json();
      const got = sane(d);
      if (!got.repos.length) throw new Error("empty");
      LED.addGlyphs(d.glyphs);
      data = got;
      const c = data.counts, pick = data.repos[Math.floor(Date.now() / 864e5) % data.repos.length];
      tick = `構内放送: 本日のおすすめは ${pick.name}。${pick.desc}　　`
        + (c ? `公開リポジトリ ${c.repos} 本、リリース ${c.releases} 回、言語 ${c.langs} 種。　　` : "")
        + "本日もご利用ありがとうございます。　　　";
      say("main-say", "新着リリース: " + releases().map(r => `${r.name} ${r.tag} (${md(r.tag_date)})`).join("、"));
    } catch (e) { /* the board runs on the clock alone */ }
  }

  async function poll() {
    try {
      const r = await fetch(`https://api.github.com/users/${USER}/events/public?per_page=40`, { headers: { Accept: "application/vnd.github+json" } });
      if (!r.ok) throw new Error(r.status);
      const seen = new Set(), out = [];
      for (const e of await r.json()) {
        const name = String((e && e.repo && e.repo.name) || "").split("/")[1] || "", at = Date.parse(e && e.created_at);
        if (e.type !== "PushEvent" || !NAME.test(name) || !Number.isFinite(at) || seen.has(name)) continue;
        seen.add(name);
        out.push({ name, at });
      }
      if (out.length) pushes = out.slice(0, 5);
    } catch (e) { /* keep what we had: data.json still fills the page */ }
  }

  const md = d => `${d.slice(5, 7)}/${d.slice(8, 10)}`;
  const releases = () => data.repos.filter(r => r.tag_date).sort((a, b) => (a.tag_date < b.tag_date ? 1 : -1)).slice(0, 5);

  function ago(at) {
    const m = Math.max(0, Math.floor((Date.now() - at) / 60000));
    return m < 1 ? "たった今" : m < 60 ? `${m}分前` : m < 1440 ? `${Math.floor(m / 60)}時間前` : `${Math.floor(m / 1440)}日前`;
  }

  function pages() {
    const out = [], rel = releases();
    if (rel.length) out.push({ title: "新着リリース", rows: rel.map(r => ({ left: md(r.tag_date), tag: r.cat, col: r.col, name: r.name, right: r.tag })) });
    if (pushes.length) out.push({ title: "最近の push", rows: pushes.map(p => ({ left: ago(p.at), name: p.name })) });
    else if (data.repos.length) out.push({ title: "最近の更新", rows: data.repos.filter(r => r.pushed).slice(0, 5).map(r => ({ left: md(r.pushed), tag: r.cat, col: r.col, name: r.name })) });
    if (!out.length) out.push({ title: "ご案内", rows: [{ left: "", name: "案内を読めませんでした" }, { left: "", name: "時計とベルとゲームは" }, { left: "", name: "ご利用いただけます" }] });
    return out;
  }

  // The same rule as the status line on the README header.
  function status() {
    if (!data.counts) return [C.RED, "案内を取得できません"];
    const yesterday = new Date(Date.parse(data.updated || "1970-01-01") - 864e5).toISOString().slice(0, 10);
    const fresh = releases().find(r => r.tag_date >= yesterday);
    if (fresh) return [C.AMBER, `臨時列車 ${fresh.name} 発車`];
    if (data.idle >= 3) return [C.RED, `運転見合わせ 休養${data.idle}日目`];
    if (data.streak >= 7) return [C.AMBER, `増発中 連続${data.streak}日`];
    return [C.GREEN, "全系統 正常稼働中"];
  }

  // ------------------------------------------------------------------ the departure board
  const main = new Board($("main"), [402, 180], [196, 232]);
  let ring = [0, 0];   // the bell rings until ring[0], the doors close until ring[1] (ms on the page clock)

  function untilUpdate(now) {   // the data is rebuilt at 06:17 JST = 21:17 UTC
    const d = new Date(now);
    d.setUTCHours(21, 17, 0, 0);
    if (d <= now) d.setUTCDate(d.getUTCDate() + 1);
    const s = Math.floor((d - now) / 1000);
    return `${two(Math.floor(s / 3600))}:${two(Math.floor(s / 60) % 60)}:${two(s % 60)}`;
  }

  function drawMain(ms) {
    const b = main, N = b.narrow, R = b.cols - 5, now = new Date(), t = ms / 1000;
    const colon = calm || now.getMilliseconds() < 500 ? ":" : " ";
    b.begin();
    b.text(two(now.getHours()) + colon + two(now.getMinutes()) + colon + two(now.getSeconds()), 6, 4, C.AMBER, { scale: 2 });
    const date = `${now.getMonth() + 1}月${now.getDate()}日(${"日月火水木金土"[now.getDay()]})`;
    if (N) {
      b.text(date, 3, 40, C.GREEN);
      b.text("更新まで " + untilUpdate(now), 3, 58, C.AMBER);
    } else {
      b.text(date, R, 4, C.GREEN, { right: true });
      b.text("次の更新まで " + untilUpdate(now), R, 22, C.AMBER, { right: true });
    }

    // The list changes every 8 seconds and is written in from the left.
    const all = pages(), turn = calm ? 0 : t % 8, page = all[calm ? 0 : Math.floor(t / 8) % all.length];
    const yL = N ? 79 : 45, yR = N ? 100 : 66, x0 = N ? 3 : 5;
    b.clip = turn < .6 ? Math.ceil(b.cols * turn / .6) : Infinity;
    b.text(page.title, x0 + 2, yL, C.GREEN, { invert: true });
    if (all.length > 1) b.text(`${all.indexOf(page) + 1}/${all.length}`, R, yL, C.GREEN, { right: true });
    const lw = Math.max(...page.rows.map(r => width(r.left)));
    page.rows.forEach((r, i) => {
      const y = yR + i * 18;
      let x = x0;
      if (lw) x += lw + 8;
      b.text(r.left, x0, y, C.GREEN);
      if (r.tag && !N) x += b.text(r.tag, x + 2, y, r.col, { invert: true }) + 8;
      const rw = r.right && !N ? b.text(fit(r.right, 80), R, y, C.GREEN, { right: true }) + 8 : 0;
      b.text(fit(r.name, R - rw - x), x, y, C.AMBER);
    });
    b.clip = Infinity;

    const yS = N ? 192 : 159, yT = N ? 212 : 178;
    let x = x0;
    if (!N) x += b.text("運行情報", x0 + 2, yS, C.RED, { invert: true }) + 10;
    if (ms < ring[0]) {
      if (calm || t % .8 < .5) b.text("まもなく発車します", x, yS, C.AMBER);
    } else if (ms < ring[1]) b.text("ドアが閉まります", x, yS, C.RED);
    else {
      const [col, s] = status();
      b.text(fit(s, R - x), x, yS, col);
    }
    b.ticker(tick, yT, C.AMBER, calm ? 0 : t);
    b.end();
  }

  // The bell: a tune written for this page, in D major. [MIDI note, beats]
  const TUNE = [[74, .5], [78, .5], [81, .5], [86, .5], [85, .5], [81, .5], [78, .5], [81, .5],
                [76, .5], [79, .5], [83, .5], [88, .5], [86, .5], [83, .5], [79, .5], [83, .5],
                [78, .5], [81, .5], [86, .5], [90, .5], [88, .5], [86, .5], [85, .5], [81, .5],
                [86, 1], [81, .5], [78, .5], [74, 2]];
  const BEAT = .4;
  $("bell").addEventListener("click", () => {
    let t = 0;
    for (const [n, beats] of TUNE) {
      Sound.note(midi(n), t, beats * BEAT * 2.2, .13);
      t += beats * BEAT;
    }
    Sound.note(midi(88), t + .5, .5, .12);   // the door chime
    Sound.note(midi(84), t + .95, .8, .12);
    ring = [performance.now() + t * 1000, performance.now() + (t + 2) * 1000];
  });
  $("snd").addEventListener("click", e => {
    Sound.on = !Sound.on;
    e.currentTarget.textContent = "ゲームの効果音: " + (Sound.on ? "入" : "切");
    e.currentTarget.setAttribute("aria-pressed", Sound.on);
    Sound.sfx("ok");
  });

  // ------------------------------------------------------------------ game 1: packet check
  // Read top to bottom, the first match decides, no match drops. The same rules as the mini game in the README.
  const RULES = [{ ok: false, src: "198.51.100." }, { ok: true, proto: "TCP", port: 443 },
                 { ok: true, proto: "UDP", port: 53 }, { ok: true, proto: "TCP", src: "192.0.2.", port: 22 }];
  function judge(p) {
    const i = RULES.findIndex(r => (!r.proto || r.proto === p.proto) && (!r.src || p.src.startsWith(r.src)) && (!r.port || r.port === p.port));
    return { ok: i >= 0 && RULES[i].ok, rule: i + 1 };
  }
  const packet = () => ({ proto: pickOf(["TCP", "TCP", "UDP"]), src: pickOf(["198.51.100.", "192.0.2.", "203.0.113."]) + (1 + Math.floor(Math.random() * 254)),
                          port: pickOf([443, 53, 22, 22, 80, 3389]) });

  const pk = { state: "idle", score: 0, miss: 0, end: 0, p: null, fb: null };
  const pkB = new Board($("pk"), [402, 180], [106, 88]);
  const pkRank = () => { const n = pk.score - pk.miss; return n >= 18 ? "鉄壁のファイアウォール" : n >= 10 ? "頼れる検問官" : n >= 4 ? "見習い検問官" : "ほぼ素通し"; };

  function pkNext(said) {
    const want = Math.random() < .5;   // half of the packets pass, so pressing one key all the time does not pay
    do pk.p = packet(); while (judge(pk.p).ok !== want);
    say("pk-say", `${said}${pk.p.proto}、送信元 ${pk.p.src}、宛先ポート ${pk.p.port}`);
  }
  function pkStart() {
    ps.state = "idle";
    Object.assign(pk, { state: "play", score: 0, miss: 0, end: performance.now() + 30000, fb: null });
    pkNext("");
    Sound.sfx("go");
  }
  function pkAnswer(ok) {
    if (pk.state !== "play") return;
    const j = judge(pk.p), right = ok === j.ok;
    if (right) pk.score++; else pk.miss++;
    pk.fb = { text: (right ? "○ " : "× ") + (j.rule ? `規則${j.rule}で` : "規則なしで") + (j.ok ? "通す" : "落とす"), col: right ? C.GREEN : C.RED, until: performance.now() + 1500 };
    Sound.sfx(right ? "ok" : "ng");
    pkNext(`${right ? "正解" : "不正解"}。正解 ${pk.score}、ミス ${pk.miss}。次: `);
  }
  $("pk-start").addEventListener("click", pkStart);
  $("pk-ng").addEventListener("click", () => pkAnswer(false));
  $("pk-ok").addEventListener("click", () => pkAnswer(true));

  function drawPk(ms) {
    const b = pkB, N = b.narrow, R = b.cols - 5, x0 = N ? 3 : 5;
    if (pk.state === "play" && ms >= pk.end) {
      pk.state = "over";
      say("pk-say", `検問終了。正解 ${pk.score}、ミス ${pk.miss}。${pkRank()}`);
    }
    b.begin();
    if (pk.state === "idle") {
      b.text("← 落とす　→ 通す", x0, N ? 6 : 12, C.AMBER, { scale: N ? 1 : 2 });
      b.text("「はじめる」を押す", x0, N ? 28 : 58, C.GREEN, { scale: N ? 1 : 2 });
    } else if (pk.state === "over") {
      b.text("検問終了", x0, 6, C.AMBER);
      b.text(`正解 ${pk.score}　ミス ${pk.miss}`, N ? x0 : 90, N ? 28 : 6, C.GREEN);
      b.text(pkRank(), x0 - 1, N ? 50 : 40, C.AMBER, { scale: N ? 1 : 2 });
    } else {
      const p = pk.p;
      b.text(`残り ${Math.ceil((pk.end - ms) / 1000)}秒`, x0, 3, C.GREEN);
      b.text(N ? `○${pk.score} ×${pk.miss}` : `正解 ${pk.score}　ミス ${pk.miss}`, R, 3, C.AMBER, { right: true });
      if (N) {
        b.text(p.proto, 5, 25, p.proto === "TCP" ? C.AMBER : C.BLUE, { invert: true });
        b.text(p.src, 40, 25, C.AMBER);
        b.text(`宛先ポート ${p.port}`, 5, 45, C.AMBER);
      } else {
        b.text("送信元", 73, 24, C.GREEN);
        b.text("宛先ポート", R, 24, C.GREEN, { right: true });
        b.text(p.proto, 7, 44, p.proto === "TCP" ? C.AMBER : C.BLUE, { invert: true, scale: 2 });
        b.text(p.src, 73, 44, C.AMBER, { scale: 2 });
        b.text(String(p.port), R, 44, C.AMBER, { scale: 2, right: true });
      }
      if (pk.fb && ms < pk.fb.until) b.text(pk.fb.text, x0, N ? 67 : 84, pk.fb.col);
    }
    b.end();
  }

  // ------------------------------------------------------------------ game 2: passing train
  const KINDS = ["回送", "快速", "特急", "急行", "普通"];
  const CROSS = [1.8, 1.2, .8, .55, .4];   // seconds for the text to cross the board, level 1 to 5
  const ps = { state: "idle", level: 0, score: 0, kind: "", num: "", typed: "", t0: 0, last: "", ok: false };
  const psB = new Board($("ps"), [402, 180], [60, 60]);
  const psRank = () => (ps.score === 5 ? "車掌も驚く動体視力" : ps.score >= 3 ? "なかなかの目" : ps.score ? "各駅停車なら読める" : "目を休めましょう");

  function psLaunch() {
    Object.assign(ps, { state: "ready", kind: pickOf(KINDS), num: String(1000 + Math.floor(Math.random() * 9000)), typed: "", t0: performance.now() });
    say("ps-say", `レベル ${ps.level + 1}。まもなく通過します`);
  }
  function psStart() {
    pk.state = "idle";
    ps.level = ps.score = 0;
    psLaunch();
    Sound.sfx("go");
  }
  function psType(d) {   // a digit, or null to take one back
    if (ps.state !== "ask") return;
    ps.typed = d === null ? ps.typed.slice(0, -1) : ps.typed + d;
    if (ps.typed.length < 4) return;
    ps.ok = ps.typed === ps.num;
    if (ps.ok) ps.score++;
    Object.assign(ps, { state: "judge", t0: performance.now(), last: ps.ok ? `○ 正解 ${ps.kind}${ps.num}` : `× 正解は ${ps.num}` });
    Sound.sfx(ps.ok ? "ok" : "ng");
    say("ps-say", ps.ok ? `正解。${ps.kind} ${ps.num} でした` : `不正解。${ps.kind} ${ps.num} でした`);
  }
  $("ps-start").addEventListener("click", psStart);
  for (const d of [..."1234567890", null]) {
    const btn = $("ps-pad").appendChild(document.createElement("button"));
    btn.type = "button";
    btn.textContent = d === null ? "消す" : d;
    btn.addEventListener("click", () => psType(d));
  }

  function drawPs(ms) {
    const b = psB, x0 = b.narrow ? 3 : 5, dt = (ms - ps.t0) / 1000, mid = s => (b.cols - width(s, 2)) >> 1;
    if (ps.state === "ready" && dt >= 1.5) Object.assign(ps, { state: "fly", t0: ms });
    else if (ps.state === "fly" && dt >= CROSS[ps.level]) {
      ps.state = "ask";
      say("ps-say", "列車番号を 4 けたで入力してください");
    } else if (ps.state === "judge" && dt >= 1.6) {
      if (++ps.level < CROSS.length) psLaunch();
      else {
        ps.state = "over";
        say("ps-say", `5 問中 ${ps.score} 問 正解。${psRank()}`);
      }
    }
    b.begin();
    if (ps.state === "idle") {
      b.text("列車番号を読み取れ", x0, 6, C.AMBER);
      b.text("「はじめる」を押す", x0, 28, C.GREEN);
    } else if (ps.state === "ready") {
      b.text(`レベル ${ps.level + 1}/5`, x0, 6, C.GREEN);
      if (dt % .5 < .3) b.text("まもなく通過します", x0, 28, C.RED);
    } else if (ps.state === "fly") {
      const s = `${ps.kind} ${ps.num}`, w = width(s, 2);
      b.text(s, Math.round(b.cols - (b.cols + w) * ((ms - ps.t0) / 1000 / CROSS[ps.level])), 14, C.AMBER, { scale: 2 });
    } else if (ps.state === "ask") {
      b.text("列車番号は?", x0, 4, C.GREEN);
      const s = ps.typed.padEnd(4, "_");
      b.text(s, mid(s), 24, C.AMBER, { scale: 2 });
    } else if (ps.state === "judge") {
      b.text(`レベル ${ps.level + 1}/5`, x0, 6, C.GREEN);
      b.text(ps.last, x0, 28, ps.ok ? C.GREEN : C.RED);
    } else {
      b.text(`5問中 ${ps.score}問 正解`, x0, 6, C.GREEN);
      b.text(psRank(), x0, 28, C.AMBER);
    }
    b.end();
  }

  // Keys are taken only while a game is waiting for them, so the arrows scroll the page at any other time.
  addEventListener("keydown", e => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (pk.state === "play" && (e.key === "ArrowLeft" || e.key === "ArrowRight")) pkAnswer(e.key === "ArrowRight");
    else if (ps.state === "ask" && /^[0-9]$/.test(e.key)) psType(e.key);
    else if (ps.state === "ask" && e.key === "Backspace") psType(null);
    else return;
    e.preventDefault();
  });

  function frame(ms) {
    drawMain(ms);
    drawPk(ms);
    drawPs(ms);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  load();
  poll();
  setInterval(poll, 10 * 60 * 1000);   // 6 calls an hour, far under the 60 an address may make without a token
})();
