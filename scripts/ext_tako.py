#!/usr/bin/env python3
"""Tako the stationmaster: an octopus in LED dots who sees a train off and says one line a day.

    python3 scripts/ext_tako.py     # self-check: every line fits the board, the scenes come in order

update_live.py calls live(ctx). One loop of the board is a short play (LOOP seconds): a train stands at
the platform, Tako walks in, stops, raises the flag, the train leaves, and the line of the day comes up.
The line is picked with the date as the seed, and the face follows the fortune of the day
(ctx["luck"]): glad on 大吉 / 中吉, downcast on 凶. With motion off: Tako with the flag, and the line.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from led import path_d  # noqa: E402
from style import *  # noqa: E402,F403

WHITE, BLUE, GREY = "#fff1d0", "#59c8ff", "#8a8f98"
K = 3            # LEDs per art dot, each way
TEXT_X = 142     # where the words start, in LED dots
TEXT_W = LED_COLS - TEXT_X - 6
ROWS_LED = 92    # height of the board in LEDs
GROUND = 89      # the row of the platform edge / rail

# The play, in seconds from the start of a loop.
LOOP = 16.0
WALK = (.4, 3.0)        # Tako comes in from the left
FLAG_UP = 4.0           # the flag goes up
DEPART = (4.8, 7.4)     # the train pulls out to the right
SAY = 7.6               # the line of the day comes up, one row every .35s
CUT = 15.4              # everything goes dark until the loop starts again

# Left half of the body, mirrored to make the right half. R red, A amber (cap), W white,
# r = red on the left side only (the arm that hangs down; on the right the flag arm takes its place).
HALF = [
    "........AAAAAAAAA",
    ".......AAAAAAAAAA",
    ".......AAAAAAAAAW",
    "........AAAAAAAAW",
    ".........WWWWWWWW",
    "........AAAAAAAAA",
    "........RRRRRRRRR",
    ".......RRRRRRRRRR",
    "......RRRRRRRRRRR",
    "......RRRRRRRRRRR",
    "......RRRRRRRRRRR",
    "......RRRRRRRRRRR",
    "......RRRRRRRRRRR",
    "......RRRRRRRRRRR",
    "......RRRRRRRRRRR",
    "......RRRRRRRRRRR",
    ".......RRRRRRRRRR",
    "........RRRRRRRRR",
    ".......RRRRRRRRRR",
    "....rrRRRRRRRRRRR",
    "..rrrr.RR.RRR.RR.",
    ".rrr...RR..RR.RR.",
    ".rr...RRR..RR.RR.",
    ".rr...RR..RRR.RR.",
    ".rrr..RR..RR..RR.",
    "..rrr.RRR.RR.RRR.",
    "...r...RR.RRR.RR.",
    ".................",
]
BODY_X = 1                  # where the body starts on the canvas
POLE = BODY_X + 35          # the column of the flag pole
COLS, ROWS = 44, 28         # canvas in art dots; the flag needs the room on the right

# Faces. K turns a dot off, W / B light it white / blue, "." leaves the red as it is.
# (eye, drawn at body column 9 and mirrored; mouth, 6 wide in the middle; extra dots)
FACES = {
    "normal": (["WWWW", "WKKW", "WWWW"], ["..KK..", "..KK.."], []),
    "glad": ([".KK.", "K..K", "...."], ["K....K", ".KKKK."], []),
    "down": (["KKKK", "WWWW", "WKKW"], [".KKKK.", "K....K"], [(13, 10, "B"), (14, 10, "B"), (15, 10, "B")]),
}

LINES = [
    "まもなく、締切が参ります。黄色い線の内側でコミットしてお待ちください。",
    "駆け込みマージは、たいへん危険です。おやめください。",
    "本日のビルドは、定刻どおり通りました。奇跡です。",
    "お忘れ物のないよう、git push をお確かめください。",
    "ただいまバグの影響で、5分ほどの遅れが出ております。",
    "この列車は、仕様変更のため、行先が変わります。",
    "次は、テスト。テストです。お出口はありません。",
    "足が8本あっても、手が足りません。",
    "車内での大きな設計変更は、ご遠慮ください。",
    "「あとで直す」は、当駅には止まりません。",
    "コメントのないコードが到着します。ご注意ください。",
    "金曜日の本番反映は、運転を見合わせております。",
    "寝不足のお客様は、無理をなさらず、次の列車をお待ちください。",
    "動いているコードには、手を触れないでください。",
    "本日も、小さく作って、早く出します。出発、進行。",
    "バックアップは、お手元にございますか。",
    "タコ足配線は、駅長の足だけにしてください。",
    "エラーメッセージは、最後までお読みください。",
    "仕様書をお持ちでないお客様は、ご乗車になれません。",
    "次の停車駅は、リリースです。タグをお忘れなく。",
    "白線の内側までお下がりください。本番環境が通過します。",
    "変数名に迷ったら、駅長にはきかないでください。",
]


def canvas(mood):
    """The body with its face, as a grid of colour letters ('.' = unlit)."""
    g = [["."] * COLS for _ in range(ROWS)]
    for r, half in enumerate(HALF):
        half = half[:17]
        for c, ch in enumerate(half + half[::-1].replace("r", ".")):
            if ch != ".":
                g[r][BODY_X + c] = ch.upper()
    eye, mouth, extra = FACES[mood]
    for r, row in enumerate(eye):
        for c, ch in enumerate(row):
            for col in (BODY_X + 9 + c, BODY_X + 33 - 9 - c):  # the left eye and its mirror image
                if ch != ".":
                    g[10 + r][col] = "." if ch == "K" else ch
    for r, row in enumerate(mouth):
        for c, ch in enumerate(row):
            if ch != ".":
                g[14 + r][BODY_X + 14 + c] = "." if ch == "K" else ch
    for r, c, ch in extra:
        g[r][BODY_X + c] = ch
    return g


def flag(up):
    """The right arm and its flag: raised (up) or held out. Grid of letters like canvas()."""
    g = [["."] * COLS for _ in range(ROWS)]
    top = 1 if up else 9                      # the row where the pole starts
    for r in range(top, top + 12):            # the pole
        g[r][POLE] = "A"
    for r in range(top, top + 6):             # the flag
        for c in range(POLE + 1, POLE + 7):
            g[r][c] = "G"
    r0, r1 = 19, top + 10                      # the arm: from the shoulder to the hand on the pole
    for i in range(9):
        c = BODY_X + 27 + i
        r = round(r0 + (r1 - r0) * i / 8)
        g[r][c] = g[r - 1][c] = "R"
    return g


def paths(grid, cls="", k=K, ox=4, oy=7):
    """One path per colour (with class `cls`), each art dot blown up to k x k LEDs, the top-left dot at LED (ox, oy)."""
    out, cls = "", f' class="{cls}"' if cls else ""
    for ch, col in (("R", RED), ("A", AMBER), ("W", WHITE), ("G", GREEN), ("B", BLUE), ("D", GREY)):
        rows = [[1 if x == ch else 0 for x in row for _ in range(k)] for row in grid for _ in range(k)]
        d = path_d(rows, ox, oy)
        if d:
            out += f'<path{cls} stroke="{col}" d="{d}"/>'
    return out


LEGS = 20  # the tentacles start at this row of the canvas


def split(grid):
    """(the body without tentacles, the tentacles, the tentacles swayed one dot to the side): two frames to walk with."""
    blank = ["."] * COLS
    body = [row if r < LEGS else blank for r, row in enumerate(grid)]
    legs = [row if r >= LEGS else blank for r, row in enumerate(grid)]
    sway = [["."] + row[:-1] if r >= LEGS + 3 else row for r, row in enumerate(legs)]
    return body, legs, sway


TRAIN_W, TRAIN_H = 262, 52  # LEDs; drawn at one LED per dot. The last car and the start of the next one.


def train():
    """The rear of a commuter train seen from the platform, heading right. Grid of colour letters."""
    g = [["."] * TRAIN_W for _ in range(TRAIN_H)]

    def box(x0, y0, x1, y1, ch, fill=True):
        for y in range(y0, y1 + 1):
            for x in range(max(x0, 0), min(x1, TRAIN_W - 1) + 1):
                if fill or y in (y0, y1) or x in (x0, x1):
                    g[y][x] = ch

    for x0, x1, tail in ((2, 203, True), (210, 411, False)):
        box(x0, 5, x1, 41, "W", fill=False)                       # the body
        for dx in (30, 120):
            box(x0 + dx, 2, x0 + dx + 40, 3, "D")                 # roof gear
        box(x0 + 1, 31, x1 - 1, 32, "G")                          # the line colour
        doors = [x0 + d for d in (40, 108, 170)]
        for d in doors:
            box(d, 9, d + 15, 38, "W", fill=False)
            box(d + 7, 9, d + 8, 38, "W")
            box(d + 2, 12, d + 5, 22, "A")
            box(d + 10, 12, d + 13, 22, "A")
        for a, b in zip([x0 + (12 if tail else 2)] + [d + 15 for d in doors], doors + [x1 - 2]):
            box(a + 5, 11, b - 5, 22, "A")                        # the lit windows between the doors
        box(x0 + 4, 42, x1 - 4, 42, "D")
        box(x0 + 70, 43, x0 + 130, 46, "D")                       # boxes under the floor
        for cx in (x0 + 18, x0 + 34, x1 - 34, x1 - 18):           # wheels
            for y in range(44, 51):
                for x in range(cx - 3, cx + 4):
                    if 0 <= x < TRAIN_W and 2 <= (x - cx) ** 2 + (y - 47) ** 2 <= 10:
                        g[y][x] = "D"
        if tail:
            g[5][x0] = g[5][x0 + 1] = g[6][x0] = "."              # a rounded corner at the rear
            box(x0 + 4, 11, x0 + 9, 22, "B")                      # the rear cab window
            box(x0 + 2, 35, x0 + 5, 38, "R")                      # the tail lamp
    box(204, 24, 209, 25, "D")                                    # the coupling
    return g


def track(name, points, css):
    """@keyframes that hold each value until the next point (run them with step-end). points: [(seconds, value)]."""
    at = dict(points)                                             # a later point at the same moment wins
    at.setdefault(0, 0)
    at[LOOP] = at[max(at)]
    return f"@keyframes {name}{{" + "".join(f"{t / LOOP * 100:.2f}%{{{css(v)}}}" for t, v in sorted(at.items())) + "}"


def spans(on):
    """[(from, to)] -> the points for track(): 1 inside a span, 0 outside."""
    return [p for a, b in on for p in ((a, 1), (b, 0))]


def play():
    """The CSS of the play. Every class is listed in the last rule, which freezes the still picture."""
    pct = lambda t: f"{t / LOOP * 100:.2f}%"  # noqa: E731
    w0, w1 = WALK
    hop = [(w0 + .4 * i, w0 + .4 * i + .2) for i in range(round((w1 - w0) / .4) + 1) if w0 + .4 * i < w1]
    up = [(FLAG_UP, FLAG_UP + 1.6)] + [(t / 10, t / 10 + .7) for t in range(round(FLAG_UP * 10) + 23, round(LOOP * 10), 14)]
    far = (COLS + 2) * K                                          # off the left edge
    d0, d1 = DEPART
    gone = TRAIN_W + 4
    run = [(d0 + (d1 - d0) * q, round(gone * q * q)) for q in (0, .25, .5, .75, 1)]  # pulling away faster and faster
    opacity = lambda v: f"opacity:{v}"  # noqa: E731
    css = (
        f"@keyframes zw{{0%,{pct(w0)}{{transform:translateX(-{far}px);animation-timing-function:steps({far // K})}}"
        f"{pct(w1)}{{transform:translateX(0);animation-timing-function:step-end}}{pct(CUT)},100%{{transform:translateX(-{far}px)}}}}"
        + track("zb", spans(hop), lambda v: f"transform:translateY({-K * v}px)")
        + track("zl1", spans(hop), lambda v: f"opacity:{1 - v}") + track("zl2", spans(hop), opacity)
        + track("zf1", spans(up), opacity) + track("zf2", spans(up), lambda v: f"opacity:{1 - v}")
        + track("zt", spans([(0, d1)]), opacity)
        + "@keyframes zr{0%{transform:translateX(0)}"
        + "".join(f"{pct(t)}{{transform:translateX({x}px);animation-timing-function:steps({max(nx - x, 1)})}}"
                  for (t, x), (_, nx) in zip(run, run[1:]))
        + f"{pct(d1)},100%{{transform:translateX({gone}px)}}}}"
        + "".join(track(f"zx{i}", spans([(SAY + .35 * i, CUT)]), opacity) for i in range(3))
    )
    hold, move = ["zb", "zl1", "zl2", "zf1", "zf2", "zt", "zx0", "zx1", "zx2"], ["zw", "zr"]
    css += "".join(f".{n}{{animation:{n} {LOOP:g}s step-end infinite}}" for n in hold)
    css += "".join(f".{n}{{animation:{n} {LOOP:g}s linear infinite}}" for n in move)
    css += ".zl2,.zf2,.zt{opacity:0}"                             # what the still picture leaves out
    css += "@media (prefers-reduced-motion:reduce){" + ",".join("." + n for n in hold + move) + "{animation:none!important}}"
    return css


def mood_of(luck):
    return {"大吉": "glad", "中吉": "glad", "凶": "down"}.get(luck, "normal")


def pick(today):
    return random.Random(today + ":tako").choice(LINES)


def live(ctx):
    mood, line = mood_of(ctx["luck"][0]), pick(ctx["today"])
    b = Board("z", LED_X, 40, LED_COLS, ROWS_LED)
    b.raw([[1] * (LED_COLS - 4)], 2, GROUND, AMBER, op=.4)
    b.put(F16, "駅長の一言", TEXT_X + 1, 8, AMBER, invert=True)
    b.put(F16, "たこ駅長", LED_COLS - 5, 8, AMBER, right=True)
    # Board has no hook for moving art, so the actors go in as ready-made paths. They stay inside the window (zq).
    body, legs, sway = split(canvas(mood))
    b.static.append(
        f'<clipPath id="zq"><rect x="-.5" y="-.5" width="{LED_COLS}" height="{ROWS_LED}"/></clipPath><g clip-path="url(#zq)">'
        f'<g class="zt"><g class="zr">{paths(train(), k=1, ox=TEXT_X + 6, oy=GROUND - 1 - TRAIN_H)}</g></g>'
        f'<g class="zw"><g class="zb">{paths(body)}{paths(legs, "zl1")}{paths(sway, "zl2")}'
        f'{paths(flag(True), "zf1")}{paths(flag(False), "zf2")}</g></g></g>')
    for i, ln in enumerate(F16.wrap(line, TEXT_W, lines=3)):
        n = len(b.static)
        b.put(F16, ln, TEXT_X, 32 + i * 19, GREEN)
        b.static[n:] = [f'<g class="zx{i}">{"".join(b.static[n:])}</g>']
    b.css += play()
    h = 40 + b.h + 17
    save("tako.svg", W, h, casing(W, h, "駅長室", "Stationmaster", "一言は毎朝かわります") + b.svg(),
         f"タコの駅長が歩いてきて旗を上げ、列車が発車していく。駅長の一言: {line}")
    return {}


if __name__ == "__main__":  # self-check
    for s in LINES:
        got = F16.wrap(s, TEXT_W, lines=3)
        assert "".join(got) == s and all(F16.width(x) <= TEXT_W + 16 for x in got), (s, got)  # 3 lines, nothing cut
    assert all(len(r) >= 17 for r in HALF) and len(HALF) == ROWS
    assert mood_of("大吉") == "glad" and mood_of("凶") == "down" and mood_of("吉") == "normal"
    assert pick("2026-11-11") == pick("2026-11-11")
    assert 0 < WALK[0] < WALK[1] < FLAG_UP < DEPART[0] < DEPART[1] < SAY < CUT < LOOP  # the scenes come in order
    assert track("k", [(4, 1), (8, 0)], lambda v: f"o:{v}") == "@keyframes k{0.00%{o:0}25.00%{o:1}50.00%{o:0}100.00%{o:0}}"
    t = train()
    assert len(t) == TRAIN_H and all(len(r) == TRAIN_W for r in t) and TEXT_X + 6 + TRAIN_W + TRAIN_W + 4 > LED_COLS
    body, legs, sway = split(canvas("normal"))
    assert sum(x != "." for r in legs for x in r) == sum(x != "." for r in sway for x in r) > 0  # swaying loses no dot
    assert 7 + ROWS * K <= GROUND + 2 and "url(" not in play()
    print("tako ok")
