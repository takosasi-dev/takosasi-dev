"use strict";
/* LED boards on <canvas>, in the same Shinonome dots as the README.
   font.js sets window.FONT = {char: [width, the 16 rows as hex]} (written by scripts/ext_site.py). */
const LED = (() => {
  const C = { AMBER: "#ffab1f", GREEN: "#4df06c", RED: "#ff4a36", WHITE: "#fff1d0", BLUE: "#59c8ff" };
  const OFF = "#1f1b13", BG = "#080706", H = 16;
  const P = 4; // canvas pixels per LED. CSS scales the canvas to its box: exact at 2px per LED (desktop), soft elsewhere.
  const FONT = window.FONT || {}, cache = new Map();

  function glyph(ch) {
    let g = cache.get(ch);
    if (!g) {
      const f = FONT[ch] || FONT["?"] || [8, "0".repeat(32)], n = f[0] / 4;
      g = { w: f[0], rows: Array.from({ length: H }, (_, r) => parseInt(f[1].substr(r * n, n), 16)) };
      cache.set(ch, g);
    }
    return g;
  }

  // Glyphs that came with data.json. Only well-formed entries are taken, and they never replace a built-in one.
  function addGlyphs(o) {
    if (!o || typeof o !== "object") return;
    for (const [ch, v] of Object.entries(o))
      if ([...ch].length === 1 && Array.isArray(v) && (v[0] === 8 || v[0] === 16) && typeof v[1] === "string"
          && v[1].length === v[0] * 4 && /^[0-9a-f]+$/.test(v[1]) && !Object.prototype.hasOwnProperty.call(FONT, ch))
        FONT[ch] = [v[0], v[1]];
  }

  function width(s, scale = 1) {
    let w = 0;
    for (const ch of s) w += glyph(ch).w;
    return w * scale;
  }

  function fit(s, maxw) {
    if (width(s) <= maxw) return s;
    const a = [...s];
    while (a.length && width(a.join("") + "..") > maxw) a.pop();
    return a.join("") + "..";
  }

  /* One LED window inside the element el. cols and rows are [wide, narrow]; the narrow layout is used
     when el is under 600px wide. Each frame: begin(), draw, end(). end() repaints only the dots that changed. */
  class Board {
    constructor(el, cols, rows) {
      this.el = el;
      this.spec = [cols, rows];
      this.pal = [OFF];
      this.sprites = [];
      this.c = el.appendChild(document.createElement("canvas"));
      this.g = el.appendChild(document.createElement("canvas")); // one pixel per LED, blurred by CSS: the glow
      this.g.className = "glow";
      this.size();
      addEventListener("resize", () => this.size());
    }

    size() {
      const narrow = this.el.clientWidth < 600;
      if (narrow === this.narrow) return;
      const i = +narrow;
      this.narrow = narrow;
      this.cols = this.spec[0][i];
      this.rows = this.spec[1][i];
      this.c.width = this.cols * P;
      this.c.height = this.rows * P;
      this.g.width = this.cols;
      this.g.height = this.rows;
      this.el.style.aspectRatio = `${this.cols} / ${this.rows}`;
      this.cells = new Uint8Array(this.cols * this.rows);
      this.prev = new Uint8Array(this.cols * this.rows).fill(255); // nothing painted yet
      this.clip = Infinity;
    }

    ci(hex) {
      if (!/^#[0-9a-f]{6}$/i.test(hex)) hex = C.AMBER;
      const i = this.pal.indexOf(hex);
      return i < 0 ? this.pal.push(hex) - 1 : i;
    }

    sprite(i) {
      if (!this.sprites[i]) {
        const s = document.createElement("canvas"), x = s.getContext("2d");
        s.width = s.height = P;
        x.fillStyle = BG;
        x.fillRect(0, 0, P, P);
        x.fillStyle = this.pal[i];
        x.beginPath();
        x.arc(P / 2, P / 2, P * .43, 0, 7);
        x.fill();
        this.sprites[i] = s;
      }
      return this.sprites[i];
    }

    begin() {
      this.cells.fill(0);
      this.clip = Infinity;
    }

    dot(x, y, c) {
      if (x >= 0 && x < this.cols && x < this.clip && y >= 0 && y < this.rows) this.cells[y * this.cols + x] = c;
    }

    rect(x, y, w, h, col) {
      const c = this.ci(col);
      for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) this.dot(x + i, y + j, c);
    }

    /* o.scale: LEDs per font dot. o.invert: a lit block with dark letters. o.right: x is the right edge. Returns the width. */
    text(s, x, y, col, o = {}) {
      const k = o.scale || 1, c = this.ci(col), pad = o.invert ? 2 * k : 0, w = width(s, k) + 2 * pad;
      if (o.right) x -= w;
      if (o.invert) this.rect(x, y - k, w, (H + 2) * k, col);
      let gx = x + pad;
      for (const ch of s) {
        const g = glyph(ch);
        if (gx + g.w * k > 0 && gx < this.cols)
          for (let r = 0; r < H; r++)
            for (let b = 0; b < g.w; b++)
              if ((g.rows[r] >> (g.w - 1 - b)) & 1)
                for (let i = 0; i < k; i++) for (let j = 0; j < k; j++) this.dot(gx + b * k + i, y + r * k + j, o.invert ? 0 : c);
        gx += g.w * k;
      }
      return w;
    }

    /* A line that scrolls one whole dot per step. t: seconds. */
    ticker(s, y, col, t, speed = 34) {
      const w = width(s), off = Math.floor(t * speed) % w;
      for (let x = -off; x < this.cols; x += w) this.text(s, x, y, col);
    }

    end() {
      const { cols, cells, prev } = this, x2 = this.c.getContext("2d"), g2 = this.g.getContext("2d");
      for (let i = 0; i < cells.length; i++) {
        const c = cells[i];
        if (c === prev[i]) continue;
        const x = i % cols, y = (i / cols) | 0;
        x2.drawImage(this.sprite(c), x * P, y * P);
        if (c) {
          g2.fillStyle = this.pal[c];
          g2.fillRect(x, y, 1, 1);
        } else g2.clearRect(x, y, 1, 1);
      }
      prev.set(cells);
    }
  }

  /* Sound. An AudioContext is made only inside note(), and note() is called only from click and key
     handlers, so the page is silent until the visitor asks for sound. */
  const Sound = {
    ac: null,
    on: false, // the switch for the small effects in the games
    note(freq, at = 0, dur = .5, vol = .16, type = "sine") {
      const A = window.AudioContext || window.webkitAudioContext;
      if (!A) return;
      const ac = this.ac = this.ac || new A();
      if (ac.state === "suspended") ac.resume();
      const t = ac.currentTime + at, g = ac.createGain();
      g.gain.setValueAtTime(0, t);
      g.gain.linearRampToValueAtTime(vol, t + .008);
      g.gain.exponentialRampToValueAtTime(.0001, t + dur);
      g.connect(ac.destination);
      for (const [m, v] of [[1, 1], [2, .35], [3, .12]]) { // two overtones make it ring like a bell
        const o = ac.createOscillator(), og = ac.createGain();
        o.type = type;
        o.frequency.value = freq * m;
        og.gain.value = v;
        o.connect(og).connect(g);
        o.start(t);
        o.stop(t + dur + .05);
      }
    },
    sfx(name) {
      if (!this.on) return;
      const s = { ok: [[1319, 0, .12], [1760, .07, .2]], ng: [[147, 0, .28, .12, "square"]], go: [[880, 0, .1], [880, .25, .1], [1760, .5, .3]] }[name];
      for (const a of s || []) this.note(...a);
    },
  };

  const midi = n => 440 * 2 ** ((n - 69) / 12);
  return { C, H, Board, Sound, addGlyphs, width, fit, midi };
})();
