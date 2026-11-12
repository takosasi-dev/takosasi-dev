"""Shared pieces for the profile SVG assets: colours, fonts, the board casing, file output."""
import colorsys
import os
import re
from xml.sax.saxutils import escape

from led import AMBER, GREEN, RED, Board, Font  # noqa: F401

ROOT = os.path.join(os.path.dirname(__file__), "..")


def esc(s):
    """Text for SVG and HTML. Safe inside a double-quoted attribute too: a repo description may hold a quote."""
    return escape(s, {'"': "&quot;"})


_F = os.path.join(os.path.dirname(__file__), "fonts")
F16 = Font(f"{_F}/shnmk16.bdf.gz", f"{_F}/shnm8x16a.bdf.gz", 16)
F12 = Font(f"{_F}/shnmk12.bdf.gz", f"{_F}/shnm6x12a.bdf.gz", 12)

MONO = "'JetBrains Mono','Cascadia Code',Consolas,'SFMono-Regular',Menlo,'DejaVu Sans Mono',monospace"
GOTH = "'Yu Gothic UI','Hiragino Sans','Noto Sans CJK JP',Meiryo,sans-serif"

LINE = ["#00a7db", "#f39700", "#e5404f", "#00a650", "#8f76d6"]  # one colour per platform (= README section)
BODY, EDGE = "#25282e", "#444a53"                    # the casing of a board
PLATE, PLATE_EDGE = "#f4f4ef", "#8a9099"             # a printed sign

LANG_COLOR = {
    "C++": "#ff5c8d", "C#": "#4df06c", "GDScript": "#35d6ff", "Python": "#ffc400",
    "TypeScript": "#4aa3ff", "JavaScript": "#f1e05a", "Kotlin": "#b48cff", "C": "#9fb3c6",
}

# Wide boards are drawn 846 units wide = the width of a profile README on a desktop, so one LED
# pitch is exactly 2px there. On a phone the 16-dot text still comes out around 13px tall.
W, LED_X, LED_COLS = 846, 21, 402


# ---- printed signs at night
# A printed sign is white paper with dark ink. For readers on a dark theme the same file repaints itself as a
# navy enamel sign with white lettering: save() adds, to the files in SIGNS, one @media (prefers-color-scheme: dark) rule
# per colour in the drawing. Line colours stay. What must not change (dark ink on a yellow cell, a black cell
# under white digits) carries class="fx". White lettering is left alone, since it nearly always sits on a colour;
# the white lettering on black ink, which turns into white paint at night, carries class="ni" and turns navy.
_CASE = {BODY, EDGE, "#000", "#080706", "#1f1b13", "#15171a", "#050505", "#6a717b", "#f2f2ee", "#aab0b8", "#8d949d"}  # LED boards
_NAVY, _SNOW = (0x12, 0x19, 0x26), (0xee, 0xf1, 0xf5)


def night(c):
    """A colour on paper -> (the colour on the navy sign, kind), or None to keep it. kind: "ink" (greys, flipped),
    "white" (flipped, but never as lettering) or "deep" (a dark saturated ink, lifted where it is a line or lettering)."""
    v = c[1:] if len(c) == 7 else "".join(ch * 2 for ch in c[1:])
    r, g, b = (int(v[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hue, l, s = colorsys.rgb_to_hls(r, g, b)
    if s < .22 or l > .93 or l < .07:
        k = 1 - l
        k = k ** 1.25 if k < .5 else k  # the paper itself stays deep
        return "#%02x%02x%02x" % tuple(round(a + (z - a) * k) for a, z in zip(_NAVY, _SNOW)), "white" if l > .9 else "ink"
    lin = lambda x: x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4  # noqa: E731
    if .2126 * lin(r) + .7152 * lin(g) + .0722 * lin(b) < .14:  # dark to the eye: navy blue, not the green of a line
        return "#%02x%02x%02x" % tuple(round(x * 255) for x in colorsys.hls_to_rgb(hue, .7, min(s, .85))), "deep"
    return None


def night_css(body):
    rules = []
    for attr in ("fill", "stroke", "stop-color"):
        for c in sorted(set(re.findall(rf'\b{attr}="(#[0-9a-f]{{3}}(?:[0-9a-f]{{3}})?)"', body)) - _CASE):
            n = night(c)
            if not n or (n[1] == "deep" and attr == "stop-color"):
                continue
            who = {"ink": "", "white": ":not(text):not(tspan)", "deep": "" if attr == "stroke" else ":is(text,tspan)"}[n[1]]
            rules.append(f'[{attr}="{c}"]:not(.fx){who}{{{attr}:{n[0]}}}')
    return "<style>@media (prefers-color-scheme:dark){" + "".join(rules) + ".ni{fill:#%02x%02x%02x}}</style>" % _NAVY


# The printed signs, by file name. Tickets, the chalkboard and the coloured exit signs are things, not paper: they stay.
SIGNS = ("nav-", "sec-", "arc-", "game-", "routemap", "maze-map", "stamps", "lost-delay", "map-all", "amida", "history",
         "stations/", "timetable", "train.svg", "train-m.svg")


def save(name, w, h, body, label):
    if name.startswith(SIGNS) or name.endswith("-plate.svg"):
        body = night_css(body) + body
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
           f'role="img" aria-label="{esc(label)}">{body}</svg>\n')
    with open(os.path.join(ROOT, "assets", name), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print("wrote", name, len(svg))


def casing(w, h, title="", sub="", note="", y=0):
    """The dark box around a board, with its printed strip. LED windows go below y + 40."""
    t = ""
    if title:
        t = (f'<g font-family="{GOTH}"><text x="22" y="{y + 27}" font-size="17" font-weight="700" fill="#f2f2ee" letter-spacing="3">{title}</text>'
             f'<text x="{22 + len(title) * 20 + 10}" y="{y + 27}" font-size="11.5" fill="#aab0b8" letter-spacing="1">{sub}</text>'
             f'<text x="{w - 22}" y="{y + 27}" text-anchor="end" font-size="11" fill="#8d949d">{note}</text></g>')
    return (f'<rect x=".5" y="{y + .5}" width="{w - 1}" height="{h - y - 1}" rx="8" fill="{BODY}" stroke="{EDGE}"/>'
            f'<rect x="10" y="{y + 2}" width="{w - 20}" height="1.5" fill="#6a717b" opacity=".45"/>' + t)


def plate(name, col, top, bottom, ja, en):
    """The small sign on top of a folded block (420x46): a line symbol like a station number, then the name."""
    body = (f'<g font-family="{GOTH}"><rect x="1" y="1" width="418" height="44" rx="6" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="1.5"/>'
            f'<circle cx="25" cy="23" r="16" fill="#fff" stroke="{col}" stroke-width="5"/>'
            f'<text x="25" y="21" text-anchor="middle" font-size="12" font-weight="800" fill="#111">{top}</text>'
            f'<text x="25" y="33" text-anchor="middle" font-size="11" font-weight="800" fill="#111">{bottom}</text>'
            f'<text x="54" y="30" font-size="19" font-weight="700" fill="#111">{ja}</text>'
            f'<text x="406" y="29" text-anchor="end" font-size="11" fill="#666" font-family="{MONO}" letter-spacing="1.5">{en}</text></g>')
    save(name, 420, 46, body, f"{ja} {en}")


def seam(board, row):
    """A dark line across a board, the joint between two LED modules."""
    return f'<rect x="{board.x}" y="{board.y + row * board.p}" width="{board.w}" height="{board.p}" fill="#050505"/>'


# ---- printed signs for a phone
# A phone shows a README image about 306px wide, so on the 846-wide signs a 16px letter comes out under 6px.
# The signs that carry reading matter are drawn a second time, WM wide and as tall as they need to be
# (name-m.svg; README picks it with <source media="(max-width: 600px)">). On that sheet nothing is set
# smaller than SMALL, which is 13px on the phone.
WM, SMALL = 430, 18.5


def text_w(s, size):
    """About how wide a bold sans text is: a kana or kanji is one em, a Latin letter or digit a bit over half."""
    return sum(size if ord(c) > 0x2000 else size * (.3 if c == " " else .58) for c in s)


def wrap_px(s, size, maxw):
    """Greedy lines by text_w(). A Latin word, and a number with its counter ("75 日"), stay in one piece;
    a closing mark never starts a line."""
    out, cur = [], ""
    for tok in re.findall(r"\d+ [^\x00-\x7f]|[\x21-\x7e]+|.", s):
        if cur.strip() and text_w(cur + tok, size) > maxw and tok not in "、。」）)・ ":
            out.append(cur.strip())
            cur = ""
        cur += tok
    return out + [cur.strip()] if cur.strip() else out


def sign_m(h, title, en, size=27):
    """The paper of a phone-width sign and its heading: the name on the left, the English tag on the right."""
    return (f'<rect x="1" y="1" width="{WM - 2}" height="{h - 2}" rx="7" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
            f'<text x="20" y="42" font-size="{size}" font-weight="700" fill="#111" letter-spacing="3">{title}</text>'
            f'<text x="{WM - 20}" y="41" text-anchor="end" font-size="{SMALL}" fill="#666" font-family="{MONO}" letter-spacing="1">{en}</text>')


if __name__ == "__main__":  # self-check: python3 scripts/style.py
    assert wrap_px("最後のリリース v1.0.0(08/29)から 75 日", 20, 200) == ["最後のリリース", "v1.0.0(08/29)から", "75 日"]
    assert wrap_px("あいうえお。", 10, 50) == ["あいうえお。"] and wrap_px("あいう えお", 10, 30) == ["あいう", "えお"]
    assert wrap_px("", 10, 50) == [] and wrap_px("abcdefghijkl", 10, 20) == ["abcdefghijkl"]  # one long word is left whole
    assert all(text_w(ln, 20) <= 200 for ln in wrap_px("公開中でいちばん古い駅「KANADE DAW」を新設", 20, 200))
    print("style ok")
