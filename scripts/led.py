"""LED dot-matrix text for the profile boards. Standard library only.

The glyphs come from the Shinonome bitmap fonts (public domain, scripts/fonts/), and every lit
dot is drawn into the SVG itself, so the result does not depend on the fonts of whoever is looking.
A run of lit dots is one line drawn with "zero-length dashes + round caps", which keeps files small.
"""
import gzip

AMBER, GREEN, RED = "#ffab1f", "#4df06c", "#ff4a36"
OFF = "#1f1b13"  # an unlit LED


def load(path):
    glyphs, enc, rows, w = {}, None, None, 0
    with gzip.open(path, "rt", encoding="latin-1", newline=None) as f:
        for ln in f:
            if ln.startswith("ENCODING"):
                enc = int(ln.split()[1])
            elif ln.startswith("BBX"):
                w = int(ln.split()[1])
            elif ln.startswith("BITMAP"):
                rows = []
            elif ln.startswith("ENDCHAR"):
                glyphs[enc], rows = (w, rows), None
            elif rows is not None:
                h = ln.strip()
                rows.append(int(h, 16) >> (len(h) * 4 - w))
    return glyphs


class Font:
    def __init__(self, kanji, ascii_, h):
        self.k, self.a, self.h = load(kanji), load(ascii_), h

    def glyph(self, ch):
        if ord(ch) < 0x80:
            return self.a.get(ord(ch)) or self.a[ord("?")]
        try:
            b = ch.encode("euc_jp")
        except UnicodeEncodeError:
            b = b""
        if len(b) == 2 and b[0] != 0x8E:  # JIS X 0208
            g = self.k.get(((b[0] & 0x7F) << 8) | (b[1] & 0x7F))
            if g:
                return g
        return self.a[ord("?")]

    def width(self, s):
        return sum(self.glyph(ch)[0] for ch in s)

    def fit(self, s, maxw):
        if self.width(s) <= maxw:
            return s
        while s and self.width(s + "..") > maxw:
            s = s[:-1]
        return s + ".."

    def wrap(self, s, maxw, lines=2):
        """Greedy wrap by dot width. Closing punctuation never starts a line (it may overhang by one)."""
        out, cur = [], ""
        for ch in s:
            if self.width(cur + ch) > maxw and ch not in "、。）)」ー・ ":
                out.append(cur)
                cur = ch
            else:
                cur += ch
        out.append(cur)
        if len(out) > lines:
            out = out[:lines - 1] + [self.fit("".join(out[lines - 1:]), maxw)]
        return [ln.strip() for ln in out]

    def rows(self, s, scale=1, invert=False, pad=2, bold=False):
        """Text -> rows of 0/1. scale=2 lights 2x2 LEDs per font dot, the way real boards double text.
        bold thickens every stroke by one LED to the right (after scaling, so letters keep a gap)."""
        out = [[] for _ in range(self.h)]
        for ch in s:
            w, g = self.glyph(ch)
            for r in range(self.h):
                out[r] += [(g[r] >> (w - 1 - c)) & 1 for c in range(w)]
        if invert:  # a lit block with dark letters, like the train-type tag
            out = [[1] * pad + [1 - b for b in row] + [1] * pad for row in out]
            out = [[1] * len(out[0])] + out + [[1] * len(out[0])]
        if scale > 1:
            out = [[b for b in row for _ in range(scale)] for row in out for _ in range(scale)]
        if bold:
            out = [[a | b for a, b in zip(row, [0] + row[:-1])] for row in out]
        return out


def path_d(rows, ox=0, oy=0):
    out = []
    for r, row in enumerate(rows):
        c, n = 0, len(row)
        while c < n:
            if row[c]:
                e = c
                while e + 1 < n and row[e + 1]:
                    e += 1
                out.append(f"M{ox + c} {oy + r}h{e - c or ''}.01")
                c = e + 1
            else:
                c += 1
    return "".join(out)


class Board:
    """One LED window: top-left x, y, size in dots, dot pitch. Everything is placed in dot coordinates."""

    def __init__(self, uid, x, y, cols, rows, p=2):
        self.uid, self.x, self.y, self.cols, self.nrows, self.p = uid, x, y, cols, rows, p
        self.w, self.h = cols * p, rows * p
        self.static, self.tick, self.css, self.loose, self.top = [], "", "", "", ""

    def raw(self, rows, cx, cy, col, blink=False, op=1):
        a = (f' class="{self.uid}bl"' if blink else "") + (f' opacity="{op}"' if op != 1 else "")
        self.static.append(f'<path{a} stroke="{col}" d="{path_d(rows, cx, cy)}"/>')

    def put(self, font, s, cx, cy, col, scale=1, invert=False, blink=False, right=False, bold=False):
        rows = font.rows(s, scale, invert, bold=bold)
        w = len(rows[0])
        self.raw(rows, cx - w if right else cx, cy - (scale if invert else 0), col, blink)
        return w

    def bar(self, cx, cy, w, h, col):
        self.raw([[1] * w] * h, cx, cy, col)

    def ticker(self, font, s, cy, col, dots_per_sec=34):
        """One scrolling line. It moves a whole dot per step, so it stays on the grid of unlit dots."""
        rows = font.rows(s)
        w, u = len(rows[0]), self.uid
        d = path_d(rows, 0, cy) + path_d(rows, w, cy)
        self.tick = (
            f'<clipPath id="{u}c"><rect x="-.5" y="{cy - 1}" width="{self.cols}" height="{font.h + 2}"/></clipPath>'
            f'<g id="{u}t" clip-path="url(#{u}c)"><path class="{u}tk" stroke="{col}" d="{d}"/></g>'
        )
        self.css += (
            f"@keyframes {u}tk{{to{{transform:translateX(-{w}px)}}}}"
            f".{u}tk{{animation:{u}tk {w / dots_per_sec:.1f}s steps({w}) infinite}}"
        )

    def drift(self, dots, col, secs, op=.55):
        """Loose dots falling through the whole window, one row per step (snow, petals, rain). dots: [(x, y)]."""
        u, n = self.uid, self.nrows
        d = "".join(f"M{x} {y}h.01M{x} {y - n}h.01" for x, y in dots)
        k = f"{u}d{len(self.loose)}"
        self.loose += f'<path class="{u}df {k}" stroke="{col}" opacity="{op}" d="{d}"/>'
        self.css += f"@keyframes {u}df{{to{{transform:translateY({n}px)}}}}.{k}{{animation:{u}df {secs}s steps({n}) infinite}}"

    def fly(self, font, s, cy, col, secs, period, scale=2):
        """Text that crosses the window in `secs` seconds, once every `period`. With motion off it rests in the middle."""
        rows = font.rows(s, scale)
        w, u = len(rows[0]), self.uid
        x0 = (self.cols - w) // 2
        a, b = self.cols - x0, -(x0 + w)  # just outside the right edge -> just outside the left edge
        self.tick = (
            f'<clipPath id="{u}c"><rect x="-.5" y="{cy - 1}" width="{self.cols}" height="{font.h * scale + 2}"/></clipPath>'
            f'<g id="{u}t" clip-path="url(#{u}c)"><path class="{u}tk" stroke="{col}" d="{path_d(rows, x0, cy)}"/></g>'
        )
        self.css += (
            f"@keyframes {u}tk{{0%{{transform:translateX({a}px);animation-timing-function:steps({a - b})}}"
            f"{secs / period * 100:.1f}%,100%{{transform:translateX({b}px)}}}}"
            f".{u}tk{{animation:{u}tk {period}s infinite}}"
        )

    def lamps(self, cols, each=.8, period=60):
        """A lamp test: every dot lit in each colour of `cols` in turn, `each` seconds apiece, once every `period`,
        over everything else. With motion off it never shows."""
        u, d = self.uid, path_d([[1] * self.cols] * self.nrows)
        self.css += f"@media (prefers-reduced-motion:reduce){{.{u}lt{{animation:none!important}}}}"
        for i, c in enumerate(cols):
            a, z = (f"{each * k / period * 100:.2f}" for k in (i, i + 1))
            self.top += f'<path class="{u}lt {u}l{i}" stroke="{c}" opacity="0" d="{d}"/>'
            self.css += (f"@keyframes {u}l{i}{{{a}%{{opacity:1}}{z}%,100%{{opacity:0}}}}"
                         f".{u}l{i}{{animation:{u}l{i} {period}s steps(1) infinite}}")

    def svg(self):
        u, x, y, p = self.uid, self.x, self.y, self.p
        g = (
            f'<g fill="none" stroke-linecap="round" stroke-dasharray="0 1" stroke-width=".86" '
            f'transform="translate({x + p / 2} {y + p / 2}) scale({p})">'
        )
        css = (
            f"{self.css}@keyframes {u}bl{{50%{{opacity:.12}}}}.{u}bl{{animation:{u}bl 1.6s steps(1) infinite}}"
            f"@media (prefers-reduced-motion:reduce){{.{u}tk,.{u}bl,.{u}df{{animation:none!important}}}}"
        )
        out = (
            f'<rect x="{x - 3}" y="{y - 3}" width="{self.w + 6}" height="{self.h + 6}" rx="2" fill="#000" stroke="#15171a"/>'
            f"<style>{css}</style>"
            f'<defs><pattern id="{u}o" x="{x}" y="{y}" width="{p}" height="{p}" patternUnits="userSpaceOnUse">'
            f'<circle cx="{p / 2}" cy="{p / 2}" r="{p * .36:.2f}" fill="{OFF}"/></pattern>'
            f'<filter id="{u}g" x="-5%" y="-30%" width="110%" height="160%"><feGaussianBlur stdDeviation="{min(p * .9, 3):.1f}"/></filter>'
            f'{g}<g id="{u}s">{"".join(self.static)}</g>{self.tick}</g></defs>'
            f'<rect x="{x}" y="{y}" width="{self.w}" height="{self.h}" fill="#080706"/>'
            f'<rect x="{x}" y="{y}" width="{self.w}" height="{self.h}" fill="url(#{u}o)"/>{g}'
        )
        if self.loose:  # drawn first, so the falling dots pass behind the text
            out += (f'<clipPath id="{u}w"><rect x="-.5" y="-.5" width="{self.cols}" height="{self.nrows}"/></clipPath>'
                    f'<g clip-path="url(#{u}w)">{self.loose}</g>')
        out += f'<use href="#{u}s" filter="url(#{u}g)" opacity=".55"/><use href="#{u}s"/>'
        if self.tick:
            out += f'<use href="#{u}t" filter="url(#{u}g)" opacity=".45"/><use href="#{u}t"/>'
        return out + self.top + "</g>"


if __name__ == "__main__":  # self-check: python3 scripts/led.py
    import os

    assert path_d([[1, 1, 0, 1], [0, 0, 0, 0], [0, 1, 0, 0]]) == "M0 0h1.01M3 0h.01M1 2h.01"
    d = os.path.join(os.path.dirname(__file__), "fonts")
    f = Font(f"{d}/shnmk12.bdf.gz", f"{d}/shnm6x12a.bdf.gz", 12)
    assert f.width("aあ") == 18 and len(f.rows("aあ")) == 12 and len(f.rows("a", scale=2)[0]) == 12
    assert f.glyph("\U0001F600") == f.glyph("?")  # no glyph -> "?", never a crash
    assert f.wrap("あいう、えお", 36) == ["あいう、", "えお"]  # the comma does not start a line
    assert f.fit("abcdefgh", 30) == "abc.."
    print("led ok")
