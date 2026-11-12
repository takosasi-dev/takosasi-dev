#!/usr/bin/env python3
"""assets/inspect.svg: the inspection pit. A small octopus in a helmet walks up to a train, taps a wheel with a
hammer, then points at it and calls "ヨシ!" (the pointing-and-calling of a railway). The board over it reports
the real thing: how many repos pass their automatic tests (CI) today and how many need repair. The face follows it.

    python3 scripts/ext_inspect.py     # self-check

update_live.py calls live(ctx) once a day. The actor is the stationmaster's body from ext_tako, drawn smaller,
with a helmet. With motion off: the inspector pointing, and the result. Standard library only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from ext_tako import BODY_X, COLS, GROUND, LOOP, ROWS, ROWS_LED, TRAIN_H, canvas, paths, spans, split, track, train  # noqa: E402
from style import *  # noqa: E402,F403

K = 2                         # LEDs per art dot: smaller than the stationmaster, who stands in front on his own board
OX, OY = 62, GROUND + 2 - ROWS * K
TRAIN_X = 148                 # the rear of the train; its first wheel is 20 LEDs further right
WIDE = 58                     # the canvas of an arm, in art dots: the hammer reaches past the body
SHOULDER = (BODY_X + 27, 19)

# The play, in seconds from the start of a loop (the loop is as long as the stationmaster's).
WALK = (.4, 2.8)
TAPS = (3.4, 4.1, 4.8, 5.5)   # the hammer comes down for TAP seconds at each
TAP = .3
YOSHI = 6.4                   # the hammer is put away, the arm points
RESULT = 7.4                  # the result comes up on the board
CUT = 15.4


def helmet(grid):
    """The stationmaster's cap turned into a helmet: all amber, with a green band."""
    for r in range(6):
        grid[r] = ["G" if r == 4 and ch != "." else "A" if ch != "." else "." for ch in grid[r]]
    return grid


def arm(pose):
    """The right arm as a grid of colour letters: "up" (hammer raised), "down" (on the wheel, with sparks) or "point"."""
    g = [["."] * WIDE for _ in range(ROWS)]

    def stroke(a, b, ch, thick=2):
        n = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
        for i in range(n + 1):
            c, r = round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n)
            for t in range(thick):
                g[r - t][c] = ch

    if pose == "point":
        stroke(SHOULDER, (42, 17), "R")
        g[16][43] = g[17][43] = g[17][44] = "R"                  # the finger
        return g
    hand, tip = ((38, 13), (46, 6)) if pose == "up" else ((40, 21), (50, 23))
    stroke(SHOULDER, hand, "R")
    stroke(hand, tip, "D", 1)                                    # the handle
    for r in range(tip[1] - 2, tip[1] + 3):                      # the head
        for c in range(tip[0], tip[0] + 3):
            g[r][c] = "W"
    if pose == "down":
        for c, r in ((54, 19), (56, 21), (55, 25), (52, 18), (57, 24)):
            g[r][c] = "A"
    return g


def result(repos):
    """(what the board says, its colour, the face). Only the repos that have CI are inspected; archived ones are out."""
    live_ = [r for r in repos if not r.get("archived")]
    ok, bad = sum(r.get("ci") == "SUCCESS" for r in live_), sum(r.get("ci") in ("FAILURE", "ERROR") for r in live_)
    if bad:
        return f"要修繕 {bad} 両 / 合格 {ok} 両", RED, "down"
    return (f"{ok} 両 すべて異常なし", GREEN, "glad") if ok else ("検査対象なし", AMBER, "normal")


def play():
    """The CSS of the play. Every class is listed in the last rule, which freezes the still picture."""
    pct = lambda t: f"{t / LOOP * 100:.2f}%"  # noqa: E731
    w0, w1 = WALK
    hop = [(w0 + .4 * i, w0 + .4 * i + .2) for i in range(round((w1 - w0) / .4) + 1) if w0 + .4 * i < w1]
    taps = [(t, t + TAP) for t in TAPS]
    idle = list(zip([0] + [b for _, b in taps], [a for a, _ in taps] + [YOSHI]))  # the hammer is up whenever it is not down
    far = (OX + WIDE * K) // K * K + K                            # off the left edge, hammer and all
    opacity = lambda v: f"opacity:{v}"  # noqa: E731
    css = (
        f"@keyframes iw{{0%,{pct(w0)}{{transform:translateX(-{far}px);animation-timing-function:steps({far // K})}}"
        f"{pct(w1)}{{transform:translateX(0);animation-timing-function:step-end}}{pct(CUT)},100%{{transform:translateX(-{far}px)}}}}"
        + track("ib", spans(hop), lambda v: f"transform:translateY({-K * v}px)")
        + track("ig1", spans(hop), lambda v: f"opacity:{1 - v}") + track("ig2", spans(hop), opacity)
        + track("ia1", spans(idle), opacity) + track("ia2", spans(taps), opacity)
        + track("ia3", spans([(YOSHI, CUT)]), opacity) + track("iy", spans([(YOSHI + .2, CUT)]), opacity)
        + track("ix", spans([(RESULT, CUT)]), opacity)
    )
    hold = ["ib", "ig1", "ig2", "ia1", "ia2", "ia3", "iy", "ix"]
    css += "".join(f".{n}{{animation:{n} {LOOP:g}s step-end infinite}}" for n in hold)
    css += f".iw{{animation:iw {LOOP:g}s linear infinite}}"
    css += ".ig2,.ia1,.ia2{opacity:0}"                            # what the still picture leaves out
    css += "@media (prefers-reduced-motion:reduce){" + ",".join("." + n for n in hold + ["iw"]) + "{animation:none!important}}"
    return css


def board(ctx):
    """(the board, the label of the picture)."""
    text, col, mood = result(ctx["repos"])
    b = Board("i", LED_X, 40, LED_COLS, ROWS_LED)
    b.raw([[1] * (LED_COLS - 4)], 2, GROUND, AMBER, op=.4)
    b.put(F16, "本日の検査", 5, 8, AMBER, invert=True)
    body, legs, sway = split(helmet(canvas(mood)))
    at = dict(k=K, ox=OX, oy=OY)
    b.static.append(
        f'<clipPath id="iq"><rect x="-.5" y="-.5" width="{LED_COLS}" height="{ROWS_LED}"/></clipPath><g clip-path="url(#iq)">'
        f'{paths(train(), k=1, ox=TRAIN_X, oy=GROUND - 1 - TRAIN_H)}'
        f'<g class="iw"><g class="ib">{paths(body, **at)}{paths(legs, "ig1", **at)}{paths(sway, "ig2", **at)}'
        f'{paths(arm("up"), "ia1", **at)}{paths(arm("down"), "ia2", **at)}{paths(arm("point"), "ia3", **at)}</g></g></g>')
    for cls, args in (("iy", ("ヨシ!", 14, 44, GREEN)), ("ix", (text, LED_COLS - 5, 8, col))):
        n = len(b.static)
        b.put(F16, *args, right=cls == "ix")
        b.static[n:] = [f'<g class="{cls}">{"".join(b.static[n:])}</g>']
    b.css += play()
    return b, f"検車区。ヘルメットをかぶったタコの点検員が歩いてきて、列車の車輪をハンマーでたたき、指を差して「ヨシ!」と確かめる。本日の検査(自動テスト): {text}"


def live(ctx):
    b, label = board(ctx)
    h = 40 + b.h + 17
    save("inspect.svg", W, h, casing(W, h, "検車区", "Inspection", "自動テスト(CI)の結果を毎朝点検") + b.svg(), label)
    return {}


if __name__ == "__main__":  # self-check
    from xml.dom.minidom import parseString

    assert 0 < WALK[0] < WALK[1] < TAPS[0] and all(a + TAP < b for a, b in zip(TAPS, TAPS[1:] + (YOSHI,))) and YOSHI < RESULT < CUT < LOOP
    assert OY + ROWS * K == GROUND + 2 and OX + WIDE * K < TRAIN_X + 40  # feet on the ground; the hammer ends at the first wheel
    hel = helmet(canvas("normal"))
    assert not any(ch == "W" for row in hel[:6] for ch in row) and "G" in hel[4] and len(hel[0]) == COLS
    for pose in ("up", "down", "point"):
        g = arm(pose)
        assert len(g) == ROWS and all(len(r) == WIDE for r in g) and g[SHOULDER[1]][SHOULDER[0]] == "R", pose
    assert sum(ch == "A" for r in arm("down") for ch in r) == 5 and not any(ch == "W" for r in arm("point") for ch in r)
    mk = lambda ci, **kw: {"ci": ci, **kw}  # noqa: E731
    assert result([mk("SUCCESS"), mk("SUCCESS"), mk(""), mk("FAILURE", archived=True)]) == ("2 両 すべて異常なし", GREEN, "glad")
    assert result([mk("SUCCESS"), mk("ERROR"), mk("FAILURE")]) == ("要修繕 2 両 / 合格 1 両", RED, "down")
    assert result([mk(""), mk("PENDING")]) == ("検査対象なし", AMBER, "normal")
    for repos in ([mk("SUCCESS")] * 31, [mk("SUCCESS")] * 120 + [mk("FAILURE")] * 15, []):
        b, label = board({"repos": repos})
        assert F16.width(result(repos)[0]) < LED_COLS - 110, result(repos)[0]  # clear of the heading on the left
        parseString(f'<svg xmlns="http://www.w3.org/2000/svg">{b.svg()}</svg>')
    assert "url(" not in play()
    print("inspect ok")
