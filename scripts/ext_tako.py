#!/usr/bin/env python3
"""Tako the stationmaster: an octopus in LED dots who waves a flag and says one line a day.

    python3 scripts/ext_tako.py     # self-check: every line fits the board

update_live.py calls live(ctx). The line of the day is picked with the date as the seed, and the
face follows the fortune of the day (ctx["luck"]): glad on 大吉 / 中吉, downcast on 凶.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from led import path_d  # noqa: E402
from style import *  # noqa: E402,F403

WHITE, BLUE = "#fff1d0", "#59c8ff"
K = 3            # LEDs per art dot, each way
TEXT_X = 142     # where the words start, in LED dots
TEXT_W = LED_COLS - TEXT_X - 6

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


def paths(grid, cls=""):
    """One path per colour, each art dot blown up to K x K LEDs."""
    out = ""
    for ch, col in (("R", RED), ("A", AMBER), ("W", WHITE), ("G", GREEN), ("B", BLUE)):
        rows = [[1 if x == ch else 0 for x in row for _ in range(K)] for row in grid for _ in range(K)]
        d = path_d(rows, 4, 4)
        if d:
            out += f'<path{cls} stroke="{col}" d="{d}"/>'
    return out


def mood_of(luck):
    return {"大吉": "glad", "中吉": "glad", "凶": "down"}.get(luck, "normal")


def pick(today):
    return random.Random(today + ":tako").choice(LINES)


def live(ctx):
    mood, line = mood_of(ctx["luck"][0]), pick(ctx["today"])
    b = Board("z", LED_X, 40, LED_COLS, ROWS * K + 8)
    # Board has no hook for two-frame art, so the frames go in as ready-made paths.
    b.static.append(paths(canvas(mood)) + paths(flag(True), ' class="zf1"') + paths(flag(False), ' class="zf2"'))
    w = b.put(F16, "駅長の一言", TEXT_X + 1, 8, AMBER, invert=True)
    for i, ln in enumerate(F16.wrap(line, TEXT_W, lines=3)):
        b.put(F16, ln, TEXT_X, 32 + i * 19, GREEN)
    b.put(F16, "たこ駅長", LED_COLS - 5, 8, AMBER, right=True)
    css = ("<style>@keyframes zf{50%{opacity:0}}.zf1{animation:zf 1.4s steps(1) infinite}"
           ".zf2{animation:zf 1.4s steps(1) -.7s infinite}"
           "@media (prefers-reduced-motion:reduce){.zf1{animation:none}.zf2{display:none}}</style>")
    h = 40 + b.h + 17
    save("tako.svg", W, h, css + casing(W, h, "駅長室", "Stationmaster", "一言は毎朝かわります") + b.svg(),
         f"タコの駅長が旗を振っている。駅長の一言: {line}")
    return {}


if __name__ == "__main__":  # self-check
    for s in LINES:
        got = F16.wrap(s, TEXT_W, lines=3)
        assert "".join(got) == s and all(F16.width(x) <= TEXT_W + 16 for x in got), (s, got)  # 3 lines, nothing cut
    assert all(len(r) >= 17 for r in HALF) and len(HALF) == ROWS
    assert mood_of("大吉") == "glad" and mood_of("凶") == "down" and mood_of("吉") == "normal"
    assert pick("2026-11-11") == pick("2026-11-11")
    print("tako ok")
