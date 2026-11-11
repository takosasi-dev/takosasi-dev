"""Shared pieces for the profile SVG assets: colours, fonts, the board casing, file output."""
import os
from xml.sax.saxutils import escape as esc  # noqa: F401

from led import AMBER, GREEN, RED, Board, Font  # noqa: F401

ROOT = os.path.join(os.path.dirname(__file__), "..")
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


def save(name, w, h, body, label):
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
