#!/usr/bin/env python3
"""The big full-colour LED screen in front of the station: one day goes by in 60 seconds.

    assets/diorama.svg     sky, sun and moon, a skyline, an elevated line with a station, trains, a bus

    python3 scripts/ext_diorama.py     # self-check

update_live.py calls live(ctx). Every building is one week of the contribution calendar: the busier
the week, the taller the building and the more of its windows are lit at night. The newest week is
the building on the right, still under its crane.

The picture is plain vector shapes laid out on the dot grid. A black sheet with one round hole per
dot goes on top, which is what makes it look like LEDs. All the 60-second animations start together,
so DIORAMA_T=20 (seconds into the loop) is enough to look at any time of day in a screenshot.

ctx["weather"] (today in Tokyo, or None) puts the weather on the screen: clouds, rain, snow, fog or
lightning, and one line of text in the corner. DIORAMA_WX=rain (cloud, snow, fog, thunder, clear)
tries one without the network.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

COLS, ROWS, P, Y0 = LED_COLS, 104, 2, 40
H = Y0 + ROWS * P + 17
LOOP = 60
BASE = 72      # the top of the viaduct deck; building heights are measured up from here
GROUND = 100   # the pavement
T0 = float(os.environ.get("DIORAMA_T", 0))

# The day, in seconds of the loop. It opens in the late afternoon so that the first thing a visitor
# sees is the sunset and the lights coming on.
DAY = [(0, 1), (5, 1), (9, .4), (12, 0), (40, 0), (43, .5), (46, 1), (60, 1)]
DUSK = [(0, 0), (3.5, 0), (8, 1), (10, .85), (13.5, 0), (60, 0)]
DAWN = [(0, 0), (39, 0), (42.5, 1), (46.5, 0), (60, 0)]
SUN_UP, SUN_SECS = 43, 26      # sunrise, and how long the sun is up (it sets at 43 + 26 - 60 = 9)
MOON_UP, MOON_SECS = 12, 29
LAMPS = (8, 44)                # street lamps, platform lights, train windows
# Window groups: (on, off, weight). They come on one after another and go dark through the night.
GROUPS = [(8.2, 43, 3), (8.8, 38, 2), (9.4, 30, 2), (10, 24, 2), (10.8, 18, 1), (11.6, 34, 2)]
WARM = ["#ffd27a", "#ffd27a", "#ffe6a8", "#ffb85a", "#cfe6ff"]
FACADES = ["#5b6f95", "#6a7da0", "#50648c", "#7b8aa8", "#64788f", "#8a8fae", "#567a98"]
NIGHT = "#03051a"


def mix(a, b, k):
    wide = lambda c: c if len(c) == 7 else "#" + "".join(ch * 2 for ch in c[1:])  # noqa: E731  "#abc" -> "#aabbcc"
    pa, pb = ([int(wide(c)[i:i + 2], 16) for i in (1, 3, 5)] for c in (a, b))
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * k) for x, y in zip(pa, pb))


def dim(c):
    return mix(c, NIGHT, .82)


class Layer:
    """Boxes on the dot grid. Neighbours of one colour share a path; the drawing order is kept."""

    def __init__(self):
        self.runs = []

    def box(self, x, y, w, h, fill):
        if w > 0 and h > 0:
            if not self.runs or self.runs[-1][0] != fill:
                self.runs.append((fill, []))
            self.runs[-1][1].append(f"M{x} {y}h{w}v{h}h{-w}z")

    def art(self, x, y, rows, pal):
        """rows: strings, one letter per dot; pal: letter -> colour. Any other letter is left empty."""
        for r, row in enumerate(rows):
            c = 0
            while c < len(row):
                e = c
                while e + 1 < len(row) and row[e + 1] == row[c]:
                    e += 1
                if row[c] in pal:
                    self.box(x + c, y + r, e - c + 1, 1, pal[row[c]])
                c = e + 1

    def svg(self, pool=False):
        """pool=True puts every shape of one colour in one path: smaller, but only right when nothing overlaps."""
        runs = self.runs
        if pool:
            by = {}
            for f, d in runs:
                by.setdefault(f, []).extend(d)
            runs = by.items()
        return "".join(f'<path fill="{f}" d="{"".join(d)}"/>' for f, d in runs)


class Pair:
    """The same shapes twice: as they look by day, and at night. The day copy fades in and out on top."""

    def __init__(self):
        self.n, self.d = Layer(), Layer()

    def box(self, x, y, w, h, col, night=None):
        self.d.box(x, y, w, h, col)
        self.n.box(x, y, w, h, night or dim(col))

    def art(self, x, y, rows, pal, night=None):
        self.d.art(x, y, rows, pal)
        self.n.art(x, y, rows, night or {k: dim(v) for k, v in pal.items()})

    def svg(self, pool=False):
        return self.n.svg(pool) + f'<g class="dy" opacity=".12">{self.d.svg(pool)}</g>'


# --------------------------------------------------------------------------- animation
def frames(name, pts, prop="opacity:%s"):
    """@keyframes from [(second, value[, timing function up to the next point])]."""
    out = ""
    for t, v, *f in pts:
        out += f"{t / LOOP * 100:.2f}".rstrip("0").rstrip(".") + "%{" + prop % v + (f";animation-timing-function:{f[0]}" if f else "") + "}"
    return f"@keyframes {name}{{{out}}}"


def loop(cls, timing="linear"):
    return f".{cls}{{animation:{cls} {LOOP}s {timing} {-T0:g}s infinite}}"


def switch(name, on, off):
    return frames(name, [(0, 0, "step-end"), (on, 1, "step-end"), (off, 0, "step-end"), (LOOP, 0)])


def arc(t, up, secs, horizon, peak):
    """Row of the sun or the moon at second t, and whether it is above the horizon at all."""
    u = ((t - up) % LOOP) / secs
    return (round(horizon - (horizon - peak) * math.sin(math.pi * u)), True) if u <= 1 else (ROWS + 20, False)


def rise(name, up, secs, horizon, peak):
    """The up-and-down half of the path, one whole dot at a time."""
    pts, last = [], None
    for i in range(LOOP * 10 + 1):  # the class carries step-end, so a keyframe is only its row
        y = arc(i / 10, up, secs, horizon, peak)[0]
        if y != last or i == LOOP * 10:
            pts.append((i / 10, y))
            last = y
    return frames(name, pts, "transform:translateY(%spx)")


def across(name, up, secs, x0, x1):
    """The sideways half: a steady walk from x0 to x1, one dot a step. It may run over the end of the loop."""
    x = lambda t: round(x0 + (x1 - x0) * (t - up) / secs)  # noqa: E731
    down = up + secs
    if down <= LOOP:
        pts = [(0, x0, "step-end"), (up, x0, f"steps({abs(x1 - x0)})"), (down, x1, "step-end"), (LOOP, x1)]
    else:
        pts = [(0, x(LOOP), f"steps({abs(x1 - x(LOOP))})"), (down - LOOP, x1, "step-end"),
               (up, x0, f"steps({abs(x(LOOP) - x0)})"), (LOOP, x(LOOP))]
    return frames(name, pts, "transform:translateX(%spx)")


TRAIN_LEN = 103
TRAIN_IN, TRAIN_STOP, TRAIN_OUT = -105, 150, 404
BRAKE = [(155, 1.6), (60, 1.2), (28, 1.2), (12, 1.5)]   # dots, seconds: fast, then slower and slower
TIMETABLE = [("stop", 1.5), ("stop", 19.5), ("pass", 36.5), ("stop", 41.5)]


def train_frames():
    pts = [(0, TRAIN_OUT, "step-end")]
    for kind, t in TIMETABLE:
        if kind == "pass":
            pts += [(t, TRAIN_IN, f"steps({TRAIN_OUT - TRAIN_IN})"), (t + 3.2, TRAIN_OUT, "step-end")]
            continue
        x = TRAIN_IN
        for d, s in BRAKE:
            pts.append((t, x, f"steps({d})"))
            x, t = x + d, t + s
        pts.append((t, x, "step-end"))
        t += 3
        for d, s in reversed(BRAKE):  # pulling out is braking played backwards
            d = min(d, TRAIN_OUT - x)
            pts.append((t, x, f"steps({d})"))
            x, t = x + d, t + s
        pts.append((t, x, "step-end"))
    pts.append((LOOP, TRAIN_OUT))
    return pts


def bus_frames():
    pts = [(0, 410, "step-end")]
    for t in (4, 23, 31, 47):
        pts += [(t, 410, "steps(440)"), (t + 6.5, -30, "step-end")]
    return pts + [(LOOP, -30)]


# --------------------------------------------------------------------------- the city
def totals(cal):
    return [sum(d["contributionCount"] for d in w["contributionDays"]) for w in cal["weeks"][-53:]] or [0]


def city(tot):
    """(buildings, their glass by day as SVG, lit windows per group, blinking red lights)."""
    bld, lit, red = Pair(), [Layer() for _ in GROUPS], Layer()
    glass = {"dots": "", "tall": "", "bands": ""}
    n, mx = len(tot), max(tot) or 1
    for i, c in enumerate(tot):
        rnd = random.Random(f"building {i}")
        x = round(i * COLS / n)
        w = round((i + 1) * COLS / n) - x - (rnd.random() < .7)
        k = math.sqrt(c / mx)
        h = 5 + round(52 * k) if c else rnd.randrange(5, 9)
        top, col = BASE - h, rnd.choice(FACADES)
        shade = mix(col, "#000", .28)
        newest = i == n - 1 and n > 1
        roof = "crane" if newest else rnd.choice(["step", "mast", "tank", "flat"] if h >= 28 else ["flat", "tank", "sign", "slope"] if c and h >= 10 else ["flat", "slope"] if c else ["house"])
        body = top
        if roof == "step":       # a narrower crown
            bld.box(x + 1, top, w - 2, 5, col)
            bld.box(x + w - 2, top, 1, 5, shade)
            body = top + 5
        elif roof == "slope":
            for s in range(min(3, w - 2)):
                bld.box(x + s, top + 2 - s, w - s, 1, col)
            body = top + 3
        elif roof == "house":
            for s in range(3):
                bld.box(x + 2 - s, top - 3 + s, w - 4 + 2 * s, 1, "#9a5a48")
            lit[rnd.choice((1, 2, 3, 5))].box(x + rnd.randrange(1, w - 2), top + 1, 2, 2, WARM[i % 3])
        bld.box(x, body, w, GROUND - body, col)
        bld.box(x + w - 1, body, 1, GROUND - body, shade)
        if roof == "mast":
            m = rnd.randrange(4, 8)
            bld.box(x + w // 2, top - m, 1, m, "#8d97a6")
            red.box(x + w // 2, top - m - 1, 1, 1, "#ff3b30")
        elif roof == "tank":
            bld.box(x + 1, top - 2, 3, 2, "#8a8f9c")
        elif roof == "sign":     # a billboard on the roof, lit all night
            sc = rnd.choice(["#ff5c8d", "#35d6ff", "#4df06c", "#ffc400"])
            bld.box(x + 1, top - 4, w - 2, 3, mix(sc, "#333", .45), sc)
            bld.box(x + w // 2, top - 1, 1, 1, "#8d97a6")
        elif roof == "crane":    # this week is still being built
            bld.box(x + 2, top - 9, 1, 9, "#ffb020", "#7a5a20")
            bld.box(x - 11, top - 8, 17, 1, "#ffb020", "#7a5a20")
            bld.box(x - 9, top - 7, 1, 4, "#c9ced6", "#4a5060")
            bld.box(x + 4, top - 7, 2, 2, "#7d8794")
            red.box(x + 2, top - 10, 1, 1, "#ff3b30")
        if h >= 40 and roof != "mast":
            red.box(x, top - 1 if roof != "step" else top - 1, 1, 1, "#ff3b30")
        # windows
        p = .22 + .58 * k
        style = rnd.choice(["dots", "dots", "bands", "tall"])
        step = 2 if style == "dots" else 3
        # Dark glass by day. A column of single windows is one dashed line, which keeps the file small;
        # at night unlit glass is as dark as the wall, so it is not drawn at all.
        if style != "bands":
            glass[style] += "".join(f"M{c2}.5 {body + 2}v{GROUND - body - 4}" for c2 in range(x + 1, x + w - 2, 2))
        for y in range(body + 2, GROUND - 2, step):
            spans = [(x + 1, w - 3)] if style == "bands" else [(c2, 1) for c2 in range(x + 1, x + w - 2, 2)]
            for wx, ww in spans:
                wh = 2 if style == "tall" else 1
                if style == "bands":
                    glass["bands"] += f"M{wx} {y}h{ww}v1h{-ww}z"
                if rnd.random() < p:
                    g = rnd.choices(range(len(GROUPS)), [g[2] for g in GROUPS])[0]
                    lit[g].box(wx, y, ww, wh, rnd.choice(WARM))
    panes = (f'<g class="dy" opacity=".12" fill="#0b1a33" stroke="#0b1a33" fill-opacity=".5" stroke-opacity=".5">'
             f'<path stroke-dasharray="1 1" d="{glass["dots"]}"/><path stroke-dasharray="2 1" d="{glass["tall"]}"/>'
             f'<path stroke="none" d="{glass["bands"]}"/></g>')
    return bld, panes, lit, red


def disc(r, cut=None):
    """A round shape as rows of letters; cut = (dx, dy, r) bites a second disc out of it (the moon)."""
    rows = []
    for y in range(-r, r + 1):
        row = ""
        for x in range(-r, r + 1):
            on = x * x + y * y <= r * r + r * .6
            if on and cut and (x - cut[0]) ** 2 + (y - cut[1]) ** 2 <= cut[2] ** 2:
                on = False
            row += "o" if on else "."
        rows.append(row)
    return rows


CAR = [
    ".bbbbbbbbbbbbbbbbbbbbbbb.",
    "bbbbbbbbbbbbbbbbbbbbbbbbb",
    "bwwwwwbddbwwwwwbddbwwwwwb",
    "bwwwwwbddbwwwwwbddbwwwwwb",
    "bbbbbbbddbbbbbbbddbbbbbbb",
    "sssssssddsssssssddsssssss",
    "bbbbbbbddbbbbbbbddbbbbbbb",
    "uuuuuuuuuuuuuuuuuuuuuuuuu",
]
BUS = [
    ".cccccccccccccccc.",
    "cwwcwwcwwcwwcwwcwc",
    "cwwcwwcwwcwwcwwcwc",
    "cccccccccccccccccc",
    "gggggggggggggggggg",
    "cckkccccccccckkccc",
    "..kk.........kk...",
]
TAKO = [
    ".aaaaa.",
    ".rrrrr.",
    "rwrrrwr",
    "rrrrrrr",
    "rrrrrrr",
    "r.r.r.r",
]


WX_JA = {"clear": "晴れ", "cloud": "くもり", "rain": "雨", "snow": "雪", "thunder": "雷雨", "fog": "霧"}
# kind -> (how much the grey sheet hides the sky, its colour, clouds by day (top, underside) or None)
WX_SKY = {"cloud": (.45, "#5b6675", ("#c3ccd6", "#a7b1bd")), "snow": (.4, "#66717f", ("#c9d1da", "#aeb7c2")),
          "rain": (.55, "#525d6b", ("#8b95a2", "#727c8a")), "thunder": (.68, "#3a4250", ("#727c8a", "#5a6472")),
          "fog": (.38, "#aab4bf", None)}


def weather(wx):
    """Today's weather as layers of the screen: {"css", "sky" (over the sky, behind the hills), "town" (over the
    buildings, behind the viaduct), "front" (over everything), "words" (for the label)}. All of them are empty
    for None or anything that is not a known kind, so the picture is then exactly the one without weather."""
    kind = wx.get("kind") if isinstance(wx, dict) else None
    out = {"css": [], "sky": "", "town": "", "front": "", "words": ""}
    if kind not in WX_JA:
        return out
    rnd = random.Random("weather " + kind)
    fall = lambda n, w, h: "".join(  # noqa: E731  n pieces, each drawn twice one screen apart so the fall loops
        f"M{x} {y}h{w}v{h}h{-w}zM{x} {y - ROWS}h{w}v{h}h{-w}z" for x, y in ((rnd.randrange(COLS), rnd.randrange(ROWS)) for _ in range(n)))
    if kind in WX_SKY:
        veil, grey, cloud = WX_SKY[kind]
        out["sky"] += f'<rect width="{COLS}" height="{BASE + 6}" fill="{grey}" opacity="{veil}"/>'
        if cloud:  # a thick layer of cloud, drifting left; three copies so it has no seam
            c = Pair()
            for i in range(14):
                cx, cy, wide = i * 29 + rnd.randrange(-8, 9), rnd.randrange(0, 22), rnd.randrange(50, 110)
                for off in (-COLS, 0, COLS):
                    for r, (dx, cut) in enumerate(((10, 22), (5, 12), (2, 5), (0, 0), (1, 2), (6, 14))):
                        c.box(cx + off + dx, cy + r, wide - cut, 1, cloud[r > 3])
            out["css"] += [loop("wc"), frames("wc", [(0, 0, f"steps({COLS})"), (LOOP, -COLS)], "transform:translateX(%spx)")]
            out["sky"] += f'<g class="wc">{c.svg(True)}</g>'
    if kind == "thunder":  # two short flashes every nine seconds; hidden when motion is off
        bolt = "".join(f"M{x} {y}h{w}v{h}h{-w}z" for x, y, w, h in ((262, 22, 2, 7), (260, 29, 2, 6), (260, 35, 7, 2), (265, 37, 2, 7), (263, 44, 2, 6), (261, 50, 2, 6), (259, 56, 2, 5), (267, 41, 5, 1), (271, 42, 2, 5)))
        out["css"].append("@keyframes lt{0%{opacity:1}2%{opacity:0}5%{opacity:.7}7%,to{opacity:0}}.lt{animation:lt 9s step-end infinite}")
        out["sky"] += (f'<g class="lt" opacity="0"><rect width="{COLS}" height="{BASE + 6}" fill="#fff" opacity=".4"/>'
                       f'<path fill="#fff7c0" d="{bolt}"/></g>')
    if kind == "fog":  # a pale sheet over the town and two layers of bands drifting past each other
        out["town"] += f'<rect width="{COLS}" height="{GROUND}" fill="#c9d2dc" opacity=".3"/>'
        for cls, to in (("g1", -COLS), ("g2", COLS)):
            d = ""
            for _ in range(10):
                x, y, w, h = rnd.randrange(COLS), rnd.randrange(30, 92), rnd.randrange(60, 150), rnd.randrange(2, 6)
                d += "".join(f"M{x + off} {y}h{w}v{h}h{-w}z" for off in (-COLS, 0, COLS))
            out["css"] += [loop(cls), frames(cls, [(0, 0, f"steps({COLS})"), (LOOP, to)], "transform:translateX(%spx)")]
            out["town"] += f'<path class="{cls}" fill="#d9e1e9" opacity=".38" d="{d}"/>'
    if kind in ("rain", "thunder"):
        out["css"].append(f"@keyframes rn{{to{{transform:translateY({ROWS}px)}}}}.r1{{animation:rn .8s steps({ROWS // 2}) infinite}}"
                          f".r2{{animation:rn 1.15s steps({ROWS // 2}) infinite}}")
        out["front"] += (f'<path class="r1" fill="#d6e6ff" opacity=".75" d="{fall(70, 1, 5)}"/>'
                         f'<path class="r2" fill="#a9c6f5" opacity=".5" d="{fall(70, 1, 3)}"/>')
    if kind == "snow":
        out["css"].append(f"@keyframes sn{{to{{transform:translateY({ROWS}px)}}}}.s1{{animation:sn 7s steps({ROWS}) infinite}}"
                          f".s2{{animation:sn 11s steps({ROWS}) infinite}}")
        white = f"M0 {GROUND}h{COLS}v1h{-COLS}z"  # snow settles along the kerb
        out["front"] += (f'<path fill="#8f9bb5" d="{white}"/><g class="dy" opacity=".12"><path fill="#f2f6fb" d="{white}"/></g>'
                         f'<path class="s1" fill="#fff" opacity=".95" d="{fall(50, 1, 1)}{fall(16, 2, 2)}"/>'
                         f'<path class="s2" fill="#dfe8ff" opacity=".7" d="{fall(60, 1, 1)}"/>')
    # one line in the corner, like the caption of a TV screen
    ja, temps = WX_JA[kind], [wx.get("tmax"), wx.get("tmin")]
    known = all(type(t) is int and -60 < t < 60 for t in temps)
    rows = F12.rows(f"東京 {ja}" + (f" {temps[0]}/{temps[1]}℃" if known else ""))
    cap = Layer()
    cap.art(4, 3, ["".join("#" if b else "." for b in row) for row in rows], {"#": "#ffffff"})
    out["front"] += f'<path fill="#000" opacity=".5" d="M2 2h{len(rows[0]) + 4}v14h{-len(rows[0]) - 4}z"/>' + cap.svg()
    out["words"] = f"今日の東京の天気は{ja}" + (f"、最高 {temps[0]} 度、最低 {temps[1]} 度。" if known else "。")
    return out


def build(cal, wx=None):
    """(SVG body, text for people who cannot see it). wx: ctx["weather"], or None for the picture without weather."""
    tot = totals(cal)
    sky_wx = weather(wx)
    rnd = random.Random("diorama")
    css = [loop("dy"), frames("dy", DAY), loop("dk"), frames("dk", DUSK), loop("dw"), frames("dw", DAWN),
           loop("lp"), switch("lp", *LAMPS),
           "@keyframes tw{50%{opacity:.15}}.tw{animation:tw 2.6s steps(1) infinite}.t2{animation-delay:-.9s}.t3{animation-delay:-1.7s}",
           "@keyframes bk{50%{opacity:0}}.bk{animation:bk 2s steps(1) infinite}",
           "@keyframes fl{50%{opacity:0}}.f1{animation:fl .9s steps(1) infinite}.f2{animation:fl .9s steps(1) -.45s infinite}",
           "@media (prefers-reduced-motion:reduce){*{animation:none!important}.f2{display:none}}"]

    # ---- sky
    sky = ('<rect width="%d" height="%d" fill="url(#gn)"/>' % (COLS, ROWS))
    stars = ["", "", "", ""]
    for i in range(86):
        x, y = rnd.randrange(1, COLS - 1), rnd.randrange(1, 56)
        stars[i % 7 if i % 7 < 4 else 0] += f"M{x} {y}h1v1h-1z"
        if i % 17 == 0:  # a few bigger ones
            stars[0] += f"M{x - 1} {y}h3v1h-3zM{x} {y - 1}h1v3h-1z"
    sky += (f'<path fill="#dfe8ff" d="{stars[0]}"/><path class="tw" fill="#ffffff" d="{stars[1]}"/>'
            f'<path class="tw t2" fill="#ffe9b0" d="{stars[2]}"/><path class="tw t3" fill="#bcd2ff" d="{stars[3]}"/>')
    # a shooting star in the middle of the night
    css += [loop("ss"), frames("ss", [(0, "-40px,-40px);opacity:0", "step-end"), (29, "0,0);opacity:1", "steps(44)"),
                                      (29.7, "44px,22px);opacity:0", "step-end"), (LOOP, "44px,22px);opacity:0")],
                               "transform:translate(%s")]
    sky += '<path class="ss" style="opacity:0" fill="#fff" d="M250 8h2v1h-2zM247 7h3v1h-3zM243 6h3v1h-3z"/>'
    moon = Layer()
    moon.art(-5, -5, disc(5, (3, -2, 5)), {"o": "#f6f1cf"})
    my = arc(MOON_UP + 12, MOON_UP, MOON_SECS, BASE + 4, 16)[0]
    css += [loop("mx"), across("mx", MOON_UP, MOON_SECS, 372, 30), loop("my", "step-end"), rise("my", MOON_UP, MOON_SECS, BASE + 4, 16)]
    sky += (f'<g class="mx" style="transform:translateX({372 - 342 * 12 // MOON_SECS}px)"><g class="my" style="transform:translateY({my}px)">'
            f'{moon.svg()}</g></g>')
    clouds = Layer()
    for cx, cy, wide in ((40, 14, 22), (150, 26, 16), (262, 10, 26), (340, 30, 14)):
        clouds.box(cx + 3, cy, wide - 8, 1, "#e9f1fa")
        clouds.box(cx + 1, cy + 1, wide - 3, 1, "#e9f1fa")
        clouds.box(cx, cy + 2, wide, 1, "#d3e0ee")
    css += [loop("cl"), frames("cl", [(0, 48, "steps(12)"), (12, 60, "step-end"), (12.01, 0, "steps(48)"), (LOOP, 48)],
                               "transform:translateX(%spx)")]
    sky += (f'<g class="dy" opacity=".12"><rect width="{COLS}" height="{ROWS}" fill="url(#gd)"/>'
            f'<g class="cl">{clouds.svg()}</g></g>')
    sky += (f'<rect class="dk" opacity=".8" width="{COLS}" height="{BASE + 6}" fill="url(#gk)"/>'
            f'<rect class="dw" opacity="0" width="{COLS}" height="{BASE + 6}" fill="url(#gw)"/>')
    sun, sun_red = Layer(), Layer()
    sun.art(-6, -6, disc(6), {"o": "#ffe07a"})
    sun_red.art(-6, -6, disc(6), {"o": "#ff6a3c"})
    css += [loop("sx"), across("sx", SUN_UP, SUN_SECS, 372, 30), loop("sy", "step-end"), rise("sy", SUN_UP, SUN_SECS, BASE + 6, 13),
            loop("sr"), frames("sr", [(0, 0), (4, 0), (8, 1), (44, 1), (47.5, 0), (LOOP, 0)])]
    sky += (f'<g class="sx" style="transform:translateX(-30px)"><g class="sy" style="transform:translateY({ROWS + 20}px)">'
            f'{sun.svg()}<g class="sr">{sun_red.svg()}</g></g></g>')

    sky += sky_wx["sky"]

    # ---- hills far away, so the sun has something to set behind (decoration, not data)
    far = Pair()
    bump = lambda x, at, wide: math.exp(-((x - at) / wide) ** 2)  # noqa: E731
    for col, night, ridge in (("#3f7198", "#0b1132", lambda x: 17 * bump(x, 84, 52) + 11 * bump(x, 196, 58) + 5 * bump(x, 300, 50) + 1.4 * math.sin(x / 6) + 2),
                              ("#335f84", "#070b22", lambda x: 9 * bump(x, 18, 44) + 7 * bump(x, 140, 40) + 4 * bump(x, 250, 60) + math.sin(x / 4 + 1) + 1)):
        x = 0
        while x < COLS:
            e, h = x, round(ridge(x))
            while e + 1 < COLS and round(ridge(e + 1)) == h:
                e += 1
            far.box(x, BASE - h, e - x + 1, h, col, night)
            x = e + 1
    far.box(0, BASE, COLS, GROUND - BASE, "#3a4d6a", "#070a1a")
    far.box(84, BASE - 26, 1, 9, "#8d97a6", "#1a2040")   # a radio mast on the hill
    sky += far.svg() + '<g class="lp"><path class="bk" fill="#ff3b30" d="M84 45h1v1h-1z"/></g>'

    # ---- the skyline
    bld, panes, lit, red = city(tot)
    for i, (on, off, _) in enumerate(GROUPS):
        css += [loop(f"l{i}"), switch(f"l{i}", on, off)]
    town = (bld.svg(True) + panes + '<g id="da">' + "".join(f'<g class="l{i}">{g.svg(True)}</g>' for i, g in enumerate(lit))
            + f'</g><g class="lp"><g class="bk">{red.svg()}</g></g>' + sky_wx["town"])

    # ---- behind the train: overhead line, platform roof
    back, glow = Pair(), Layer()
    for x in range(18, COLS, 46):
        back.box(x, 53, 1, 18, "#7d8794")
        back.box(x - 2, 54, 5, 1, "#7d8794")
    back.box(0, 56, COLS, 1, "#566070", "#1c2238")
    back.box(128, 57, 146, 1, "#aab3bf")
    back.box(126, 58, 150, 1, "#7a8592")
    for x in range(132, 274, 23):
        back.box(x, 59, 1, 12, "#8892a0")
    back.art(189, 62, ["wwwwwwwwwwwww", "wnnwnnwnnwnnw", "wwwwwwwwwwwww", "ooooooooooooo"], {"w": "#f4f4ef", "n": "#15223f", "o": LINE[1]},
             {"w": "#cfd6e2", "n": "#15223f", "o": LINE[1]})
    for x in range(130, 274, 6):
        glow.box(x, 59, 2, 1, "#fff0c0")

    # ---- the train
    car_d = {"b": "#d5dbe4", "w": "#2a3852", "d": "#aeb7c4", "s": LINE[1], "u": "#4c5562"}
    car_n = {"b": "#3b4358", "w": "#141b2e", "d": "#30374a", "s": mix(LINE[1], NIGHT, .45), "u": "#151a2a"}
    tr, tr_l = Pair(), Layer()
    for k in range(4):
        tr.art(k * 26, 63, CAR, car_d, car_n)
        tr_l.art(k * 26, 63, [r.replace("b", ".").replace("d", ".").replace("s", ".").replace("u", ".") for r in CAR], {"w": "#ffe9a8"})
        if k % 2:
            tr.art(k * 26 + 9, 61, ["p.p.p", ".ppp."], {"p": "#8d97a6"})
    lamps = ('<path fill="#fff7d6" d="M%d 68h1v1h-1z"/><path fill="#ff3b30" d="M0 68h1v1h-1z"/>' % (TRAIN_LEN - 1))
    css += [loop("tr"), frames("tr", train_frames(), "transform:translateX(%spx)")]
    train = (f'<g class="tr" style="transform:translateX({TRAIN_STOP}px)">{tr.svg()}<g class="lp">{tr_l.svg()}</g>{lamps}</g>')

    # ---- the viaduct, the station under it, the street
    fg, fl = Pair(), Layer()
    fg.box(0, 70, COLS, 1, "#b5bdc8")
    fg.box(0, 71, COLS, 1, "#98a2af")
    fg.box(0, BASE, COLS, 3, "#8892a0")
    fg.box(0, BASE + 3, COLS, 1, "#5b6470")
    for x in range(13, COLS, 30):
        if not 140 < x < 258:
            fg.box(x, BASE + 4, 3, GROUND - BASE - 4, "#7b8592")
            fg.box(x + 2, BASE + 4, 1, GROUND - BASE - 4, "#5f6975")
    # shops under the tracks: (x, width, wall, sign colour)
    for x, w, wall, sc in ((47, 24, "#6b4a3a", "#e5404f"), (77, 24, "#dfe5ec", "#00a650"), (107, 24, "#3a4660", "#35d6ff"),
                           (287, 24, "#dfe5ec", "#f39700"), (317, 24, "#5a4a6a", "#ff5c8d"), (347, 24, "#4a5a50", "#ffc400")):
        fg.box(x, 86, w, 14, wall)
        fg.box(x, 86, w, 3, mix(sc, "#222", .35), sc)                      # the sign above the door, lit at night
        fg.box(x + 3, 91, w - 12, 7, mix(wall, "#0a1428", .6), "#141b2e")   # the shop window
        fg.box(x + w - 7, 91, 4, 9, mix(wall, "#0a1428", .7), "#141b2e")    # the door
        fl.box(x + 3, 91, w - 12, 7, "#ffdc90")
        fl.box(x + w - 7, 91, 4, 9, "#ffe9b0")
    fl.box(50, 90, 2, 3, "#ff4a36")  # a red lantern
    # the station
    fg.box(146, BASE + 4, 110, GROUND - BASE - 4, "#c3cad4")
    fg.box(146, BASE + 4, 110, 1, "#8a94a2")
    for x in range(150, 254, 8):
        fg.box(x, 94, 1, 6, "#a9b2be")
    fg.box(170, 77, 62, 15, "#f4f4ef", "#ffffff")
    fg.box(170, 91, 62, 1, "#8a9099")
    fg.box(172, 90, 58, 1, LINE[1], LINE[1])
    name = F12.rows("たこさし")
    sign = Layer()
    sign.art(201 - len(name[0]) // 2, 78, ["".join("#" if b else "." for b in row) for row in name], {"#": "#15223f"})
    fg.box(187, 93, 28, 7, "#2a3852", "#141b2e")          # the way in
    fl.box(187, 93, 28, 7, "#ffe9b0")
    for x in (193, 200, 207):
        fl.box(x, 96, 2, 4, "#8892a0")                    # ticket gates against the light
    for x in (152, 160, 238, 246):
        fg.box(x, 80, 5, 8, "#2a3852", "#141b2e")
        fl.box(x, 80, 5, 8, "#ffdc90")
        fl.box(x + 2, 80, 1, 8, "#b59a60")
    # the street
    fg.box(0, GROUND, COLS, 1, "#7d8794")
    fg.box(0, GROUND + 1, COLS, ROWS - GROUND - 1, "#2c333f", "#0c0f1c")
    for x in range(4, COLS, 12):
        fg.box(x, GROUND + 2, 5, 1, "#c9c9b0", "#3c4050")
    for x in (34, 136, 266, 280, 376):                    # trees
        fg.box(x + 2, 95, 1, 5, "#6b4a3a")
        fg.art(x, 89, [".ggg.", "ggGgg", "gGggg", "ggggG", ".ggg."], {"g": "#3f8f4f", "G": "#2f7040"})
    for x in (26, 124, 276, 392):                         # street lamps
        fg.box(x, 88, 1, 12, "#56606c")
        fg.box(x - 1, 87, 3, 1, "#56606c")
        fl.box(x - 1, 88, 3, 1, "#fff0c0")
        fl.box(x - 3, GROUND, 7, 1, "#b9a878")
    # the stationmaster by the gate, waving the flag
    tako = Layer()
    tako.art(219, 94, TAKO, {"a": AMBER, "r": "#ff4a36", "w": "#fff1d0"})
    tako_svg = (tako.svg() + '<path class="f1" fill="#4df06c" d="M226 92h3v2h-3zM226 94h1v3h-1z"/>'
                '<path class="f2" fill="#4df06c" d="M227 95h3v2h-3zM226 96h1v1h-1z"/>')
    # the bus
    bus, bus_l = Pair(), Layer()
    bus.art(0, 95, BUS, {"c": "#e9e4d0", "w": "#2a3852", "g": "#00a650", "k": "#1a1d26"},
            {"c": "#4a4a50", "w": "#141b2e", "g": "#0a4a2a", "k": "#05060c"})
    bus_l.art(0, 95, [r.replace("c", ".").replace("g", ".").replace("k", ".") for r in BUS], {"w": "#ffe9a8"})
    css += [loop("bs"), frames("bs", bus_frames(), "transform:translateX(%spx)")]
    bus_svg = (f'<g class="bs" style="transform:translateX(420px)">{bus.svg()}<g class="lp">{bus_l.svg()}'
               f'<path fill="#fff7d6" d="M-1 99h1v1h-1zM-4 101h3v1h-3z"/></g><path fill="#ff3b30" d="M17 99h1v1h-1z"/></g>')

    grads = (
        '<linearGradient id="gn" x2="0" y2="1"><stop stop-color="#02030d"/><stop offset=".35" stop-color="#080e2e"/><stop offset=".69" stop-color="#2b3f8a"/><stop offset="1" stop-color="#2b3f8a"/></linearGradient>'
        '<linearGradient id="gd" x2="0" y2="1"><stop stop-color="#184a8f"/><stop offset=".7" stop-color="#58a4d4"/><stop offset="1" stop-color="#6cb2dc"/></linearGradient>'
        '<linearGradient id="gk" x2="0" y2="1"><stop stop-color="#2a1650" stop-opacity=".55"/><stop offset=".5" stop-color="#b8386e" stop-opacity=".8"/><stop offset=".85" stop-color="#ff8a3a"/><stop offset="1" stop-color="#ffb85a"/></linearGradient>'
        '<linearGradient id="gw" x2="0" y2="1"><stop stop-color="#2a3a80" stop-opacity=".3"/><stop offset=".5" stop-color="#d9709a" stop-opacity=".75"/><stop offset=".85" stop-color="#ffc08a"/><stop offset="1" stop-color="#ffe2a8"/></linearGradient>'
        f'<pattern id="dm" x="{LED_X}" y="{Y0}" width="{P}" height="{P}" patternUnits="userSpaceOnUse">'
        f'<path fill="#070605" fill-rule="evenodd" d="M0 0h{P}v{P}h-{P}zM{P / 2} {P * .07:.2f}a{P * .43:.2f} {P * .43:.2f} 0 1 0 .001 0z"/></pattern>'
        f'<clipPath id="dc"><rect width="{COLS}" height="{ROWS}"/></clipPath>'
        # the glow of the windows stops above the platform roof, or it would shine through the train
        f'<clipPath id="dh"><rect width="{COLS}" height="57"/></clipPath>'
        '<filter id="df" x="-5%" y="-10%" width="110%" height="120%"><feGaussianBlur stdDeviation="1.3"/></filter>')
    w, h = COLS * P, ROWS * P
    place = f'<g transform="translate({LED_X} {Y0}) scale({P})" clip-path="url(#dc)"'
    body = (
        casing(W, H, "たこさし駅前", "Station front", "ビルの高さは週ごとの活動量。60 秒で 1 日")
        + f'<rect x="{LED_X - 3}" y="{Y0 - 3}" width="{w + 6}" height="{h + 6}" rx="2" fill="#000" stroke="#15171a"/>'
        + f'<style>{"".join(css + sky_wx["css"])}</style><defs>{grads}</defs>'
        + f'{place} shape-rendering="crispEdges">'
        + sky + town + back.svg() + f'<g class="lp">{glow.svg()}</g>' + train
        + fg.svg() + sign.svg() + f'<g id="db" class="lp">{fl.svg()}</g>' + tako_svg + bus_svg + sky_wx["front"] + "</g>"
        + f'<rect x="{LED_X}" y="{Y0}" width="{w}" height="{h}" fill="url(#dm)"/>'
        + f'{place}><g filter="url(#df)" opacity=".55"><use href="#da" clip-path="url(#dh)"/><use href="#db"/></g></g>')
    label = (f"たこさし駅前の大型 LED ビジョン。60 秒で朝・昼・夕・夜が巡り、高架の駅に列車が発着する。"
             f"ビル {len(tot)} 棟は過去 1 年の週ごとの活動量で、いちばん高いビルの週は {max(tot)} 回、建設中の右端が今週の {tot[-1]} 回。"
             + sky_wx["words"])
    return body, label


def live(ctx):
    wx = ctx.get("weather")
    if os.environ.get("DIORAMA_WX"):  # try a weather by hand
        wx = {"kind": os.environ["DIORAMA_WX"], "tmax": 15, "tmin": 8}
    body, label = build(ctx["cal"], wx)
    save("diorama.svg", W, H, body, label)
    return {}


if __name__ == "__main__":  # self-check
    fake = lambda f: {"weeks": [{"contributionDays": [{"contributionCount": f(i)} for _ in range(7)]} for i in range(54)]}  # noqa: E731
    for cal in (fake(lambda i: i % 9), fake(lambda i: 0), {"weeks": []}):
        body, label = build(cal)
        assert "nan" not in body.lower() and len(body) < 200_000, len(body)
        assert "53 棟" in label or cal["weeks"] == []
    # a year of nothing is 53 low houses; a busy week makes the tallest building
    assert max(totals(fake(lambda i: i))) == 53 * 7 and len(totals(fake(lambda i: 1))) == 53
    pts = train_frames()
    assert all(a[0] < b[0] for a, b in zip(pts, pts[1:])), "the timetable overlaps"
    assert all(x in (TRAIN_IN, TRAIN_OUT) or TRAIN_IN < x < TRAIN_OUT for _, x, *_ in pts)
    assert sum(1 for _, x, *_ in pts if x == TRAIN_STOP) == 2 * sum(k == "stop" for k, _ in TIMETABLE)
    assert arc(SUN_UP + SUN_SECS / 2, SUN_UP, SUN_SECS, 78, 13) == (13, True) and not arc(20, SUN_UP, SUN_SECS, 78, 13)[1]
    assert H <= 270
    # weather: nothing known -> exactly the picture without it; every kind fits and carries its caption
    cal = fake(lambda i: i % 9)
    plain = build(cal)
    for none in (None, {}, {"kind": "sharknado"}, {"kind": None}, "rain", 3):
        assert build(cal, none) == plain, none
    for kind, ja in WX_JA.items():
        body, label = build(cal, {"kind": kind, "ja": "x", "tmax": -3, "tmin": -11})
        assert len(plain[0]) < len(body) < 200_000 and "nan" not in body.lower() and f"天気は{ja}、最高 -3 度" in label, kind
        assert build(cal, {"kind": kind, "tmax": "<svg>", "tmin": None})[1].endswith(f"天気は{ja}。")  # odd temperatures are left out
    assert all(F12.glyph(ch) != F12.glyph("?") for ch in "東京℃/-0123456789" + "".join(WX_JA.values()))
    print("diorama ok")
