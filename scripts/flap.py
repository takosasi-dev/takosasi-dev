"""A split-flap (Solari) board as an SVG fragment: black cells, white letters, a seam across the
middle, and flaps that fall through a few other letters before each cell settles.

    board(uid, x, y, lines, cols, cw, ch) -> (svg fragment, width, height)

    python3 scripts/flap.py     # self-check, and the sample assets/flap-demo.svg

Everything is CSS animation, so it runs inside an <img>. Standard library only.
"""
import random
from xml.sax.saxutils import escape


def esc(s):  # the same as style.esc; this file stands alone
    return escape(s, {'"': "&quot;"})


# Latin letters come from the first fonts (bold sans, like the real boards), kana and kanji from the rest.
FACE = "'Helvetica Neue',Helvetica,Arial,'Yu Gothic UI','Hiragino Sans','Noto Sans CJK JP',Meiryo,sans-serif"
DRUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"  # what flickers past on the way to a Latin letter


def _n(v):
    return f"{v:.3f}".rstrip("0").rstrip(".")


def board(uid, x, y, lines, cols, cw, ch, gap=2, hold=7.0, step=.07):
    """`len(lines)` rows of `cols` cells, each cell cw x ch. lines[i] is the list of messages row i shows in turn.

    One message: the row flips in from blank once, when the image loads, and stays.
    Several: every `hold` seconds the row flips to the next one, and from the last back to the first
    (so at load the row shows the last message and flips to the first straight away).
    A message is padded with spaces to `cols` and cut there. A cell whose letter does not change does not flip.
    The cells start one `step` apart from the left; each passes 4-10 other letters, one per `step`.
    Every id, class and keyframe starts with `uid` (a letter first), so several boards fit in one SVG.
    With motion turned off, each row shows its first message.
    The fragment draws a 3px dark bezel around (x, y, width, height), like led.Board.
    """
    u, hh, H = uid, ch / 2, round(hold / step) * step
    assert H > (cols + 12) * step, "hold is too short for the whole row to finish flipping"
    rnd = random.Random(f"{uid}{lines}{cols}")  # the same text flips the same way every day: no churn in git
    w, h = cols * cw + (cols - 1) * gap, len(lines) * ch + (len(lines) - 1) * gap * 2
    fs = min(ch * .72, cw * .9)
    css = [
        # The falling flap: the upper leaf folds down to the seam, then comes down over the lower half.
        f".{u}A{{fill:#3b3f47;transform-box:fill-box;transform-origin:50% 100%;animation:{u}A {step}s linear infinite}}"
        f".{u}B{{fill:#08090a;opacity:.88;transform-box:fill-box;transform-origin:50% 0;animation:{u}B {step}s linear infinite}}"
        f"@keyframes {u}A{{0%{{transform:scaleY(1)}}50%,100%{{transform:scaleY(0)}}}}"
        f"@keyframes {u}B{{0%,50%{{transform:scaleY(0)}}100%{{transform:scaleY(1)}}}}"
        f"@keyframes {u}v{{0%,100%{{opacity:1}}}}@keyframes {u}h{{0%,100%{{opacity:0}}}}"
        # Three flaps a third of a step apart, so that neighbouring cells do not strobe as one band.
        f".{u}p1{{animation-delay:{_n(step / 3)}s}}.{u}p2{{animation-delay:{_n(step * 2 / 3)}s}}"
    ]
    still = [f".{u}A", f".{u}B"]
    cells, texts, flaps, seams = [], [], [], []
    for r, msgs in enumerate(lines):
        c, k, ry = f"{u}{r}", len(msgs), y + r * (ch + gap * 2)
        msgs = [m[:cols].ljust(cols) for m in msgs]
        P = k * H
        kana = sorted({a for m in msgs for a in m if not a.isascii()})
        durs = {round(step * 1000): 0}  # visible time in ms -> keyframes number (looping rows)

        def vis(start, dur=None, base=False):
            """class and style that show an element from `start` for `dur` seconds (None: from then on)."""
            if k > 1:  # a loop of P seconds; a negative delay puts every element at its place in the loop from t = 0
                i = durs.setdefault(round(dur * 1000), len(durs))
                return f'class="{c}i{f" {c}k{i}" if i else ""}{f" {c}s" if base else ""}" style="--d:{_n(start - P)}s"'
            if dur is None:
                return f'class="{c}f" style="--d:{_n(start)}s"'
            if round(dur * 1000) in durs:
                return f'class="{c}i" style="--d:{_n(start)}s"'
            return f'class="{c}w" style="--d:{_n(start)}s;--n:{_n(dur)}s"'

        for i in range(cols):
            cx, col = x + i * (cw + gap), [m[i] for m in msgs]
            cells.append(f'<rect x="{_n(cx)}" y="{_n(ry)}" width="{_n(cw)}" height="{_n(ch)}" rx="{_n(min(cw, ch) * .07)}"/>')
            # (when the cell starts to flip, how many letters pass, the letter it lands on, the letter it leaves)
            ev = [(j * H + (i + i % 3 / 3) * step, rnd.randint(4, 10), col[j], col[j - 1] if k > 1 else " ") for j in range(k)]
            ev = [e for e in ev if e[2] != e[3]]
            out = [] if ev or col[0] == " " else [f"<text>{esc(col[0])}</text>"]
            for e, (d, n, cur, prev) in enumerate(ev):
                pool = DRUM if (cur if cur != " " else prev).isascii() else kana
                out += [f"<text {vis(d + m * step, step)}>{esc(rnd.choice(pool))}</text>" for m in range(n)]
                land = d + n * step
                # the flap keeps falling half a step longer: the last leaf uncovers the top of the final letter
                flaps.append(f'<use href="#{u}o{i % 3}" {vis(d, land - d + step / 2)} x="{_n(cx)}" y="{_n(ry)}"/>')
                if cur == " ":
                    continue
                if k > 1:  # stays until this cell's next flip; H - step is a moment when message 0 is up
                    dur = (ev[(e + 1) % len(ev)][0] - land) % P
                    out.append(f"<text {vis(land, dur, (H - step - land) % P < dur)}>{esc(cur)}</text>")
                else:
                    out.append(f"<text {vis(land)}>{esc(cur)}</text>")
            if out:
                texts.append(f'<g transform="translate({_n(cx + cw / 2)} {_n(ry + hh + fs * .36)})">{"".join(out)}</g>')
        if k > 1:
            css.append(f".{c}i{{opacity:0;animation:{c}k0 {_n(P)}s step-end var(--d) infinite}}")
            for ms, i in durs.items():
                css.append(f"@keyframes {c}k{i}{{0%{{opacity:1}}{ms / 10 / P:.4f}%,100%{{opacity:0}}}}"
                           + (f".{c}k{i}{{animation-name:{c}k{i}}}" if i else ""))
            css.append(f".{c}s{{opacity:1}}")  # after .{c}i on purpose: with motion off, message 0 shows
            still.append(f".{c}i")
        else:
            css.append(f".{c}i{{opacity:0;animation:{u}v {step}s step-end var(--d) 1}}"
                       f".{c}w{{opacity:0;animation:{u}v var(--n) step-end var(--d) 1}}"
                       f".{c}f{{animation:{u}h var(--d) step-end 1}}")
            still += [f".{c}i", f".{c}w", f".{c}f"]
        ym = ry + hh
        seams.append(  # the seam, and the two hinge pins at the sides of every cell
            f'<path d="M{_n(x)} {_n(ym)}h{_n(w)}" stroke="#000" stroke-width="{_n(max(1.2, ch * .03))}" opacity=".9"/>'
            f'<path d="M{_n(x)} {_n(ym)}h{_n(w)}" stroke="#565b64" stroke-width="{_n(max(3, ch * .08))}" '
            f'stroke-dasharray="{_n(cw * .05)} {_n(cw * .9)} {_n(cw * .05)} {_n(gap)}"/>')
    css.append(f"@media (prefers-reduced-motion:reduce){{{','.join(still)}{{animation:none!important}}}}")
    svg = (
        f"<style>{''.join(css)}</style>"
        f'<defs><linearGradient id="{u}g" x2="0" y2="1"><stop stop-color="#2b2e34"/><stop offset=".5" stop-color="#1f2126"/>'
        f'<stop offset=".5" stop-color="#17191c"/><stop offset="1" stop-color="#101113"/></linearGradient>'
        + "".join(f'<g id="{u}o{v}"><rect class="{u}A {u}p{v}" width="{_n(cw)}" height="{_n(hh)}"/>'
                  f'<rect class="{u}B {u}p{v}" y="{_n(hh)}" width="{_n(cw)}" height="{_n(hh)}"/></g>' for v in range(3))
        + "</defs>"
        f'<rect x="{_n(x - 3)}" y="{_n(y - 3)}" width="{_n(w + 6)}" height="{_n(h + 6)}" rx="2" fill="#050506" stroke="#15171a"/>'
        f'<g fill="url(#{u}g)">{"".join(cells)}</g>'
        f'<g font-family="{FACE}" font-size="{_n(fs)}" font-weight="700" fill="#f4f1e6" text-anchor="middle">{"".join(texts)}</g>'
        f'{"".join(flaps)}{"".join(seams)}'
    )
    return svg, w, h


if __name__ == "__main__":  # self-check, then the sample
    import os
    import re
    import sys

    s, w, h = board("t", 0, 0, [["ABCDE"]], 3, 30, 40)
    assert (w, h) == (94, 40)
    assert re.findall(r'class="t0f"[^>]*>(.)<', s) == ["A", "B", "C"]  # cut at cols; one landing per cell
    s, w, h = board("t", 0, 0, [["A B", "A C", "A あ"], ["X"]], 3, 30, 40)
    assert h == 84 and s.count("<text>") == 1  # the "A" that never changes is drawn once, without animation
    assert re.findall(r' t0s"[^>]*>(.)<', s) == ["B"]  # with motion off, message 0 shows
    assert "nan" not in s and "--d:-" in s
    try:
        board("t", 0, 0, [["A", "B"]], 24, 30, 40, hold=1)
        raise SystemExit("a hold that is too short must be refused")
    except AssertionError:
        pass
    print("flap ok")

    sys.path.insert(0, os.path.dirname(__file__))
    from style import BODY, EDGE, W, save  # noqa: E402

    a, aw, ah = board("p", 22.5, 20, [["TAKOSASI-DEV"]], 12, 64, 80, gap=3)
    b, bw, bh = board("q", 22, 114, [["INFRA NETWORK SECURITY", "NEW  KOE-LOOM  V0.6.0", "インフラ ネットワーク 保守", "59 REPOS  104 RELEASES"]],
                      24, 31.5, 40)
    assert aw <= 804 and bw <= 804, (aw, bw)
    save("flap-demo.svg", W, 172, f'<rect x=".5" y=".5" width="{W - 1}" height="171" rx="8" fill="{BODY}" stroke="{EDGE}"/>' + a + b,
         "TAKOSASI-DEV / INFRA NETWORK SECURITY")
