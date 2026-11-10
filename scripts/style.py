"""Shared palette / helpers for the profile SVG assets."""
from xml.sax.saxutils import escape as esc

MONO = "'JetBrains Mono','Cascadia Code',Consolas,'SFMono-Regular',Menlo,'DejaVu Sans Mono',monospace"
MIN = "'Yu Mincho',YuMincho,'Hiragino Mincho ProN','Noto Serif CJK JP','Noto Serif JP','MS PMincho',serif"
GOTH = "'Yu Gothic UI','Hiragino Sans','Noto Sans CJK JP',Meiryo,sans-serif"

BG = "#05070d"
BG2 = "#0a0f1c"
CYAN = "#00e5ff"
MAG = "#ff2bd6"
ORANGE = "#ff7a00"
RED = "#ff3030"
GREEN = "#39ff88"
AMBER = "#ffc400"
TEXT = "#d8e6f0"
DIM = "#5f7387"

LANG_COLOR = {
    "C++": "#f34b7d", "C#": "#39ff88", "GDScript": "#00e5ff", "Python": "#ffc400",
    "TypeScript": "#3b9dff", "JavaScript": "#f1e05a", "Kotlin": "#a97bff",
}


def hex_points(cx, cy, r):
    """Pointy-top hexagon."""
    import math
    pts = []
    for i in range(6):
        a = math.radians(60 * i - 90)
        pts.append(f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}")
    return " ".join(pts)


def hex_pattern(pid="hex", r=26, color=CYAN, op=0.09):
    w = 1.7320508 * r
    return (f'<pattern id="{pid}" width="{w:.2f}" height="{3*r}" patternUnits="userSpaceOnUse">'
            f'<path d="M{w/2:.2f} 0L{w:.2f} {r/2}L{w:.2f} {1.5*r}L{w/2:.2f} {2*r}L0 {1.5*r}L0 {r/2}Z'
            f'M{w/2:.2f} {2*r}L{w/2:.2f} {3*r}" fill="none" stroke="{color}" stroke-opacity="{op}" stroke-width="1"/></pattern>')


def units(s):
    return sum(1.0 if ord(c) > 0x2E7F else 0.56 for c in s)


def wrap(s, max_units, max_lines=2):
    """Wrap mixed CJK/ASCII text, preferring to break after spaces and punctuation."""
    brk = " 　、。・/／）)"
    lines, cur = [], ""
    for ch in s:
        if units(cur + ch) > max_units:
            cut = max((cur.rfind(b) for b in brk), default=-1)
            if cut >= 0 and units(cur[cut + 1:]) <= 9:
                lines.append(cur[:cut + 1].rstrip())
                cur = cur[cut + 1:] + ch
            else:
                lines.append(cur)
                cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while units(lines[-1]) > max_units - 1.2:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"
    return [l.strip() for l in lines]


def brackets(x, y, w, h, n=18, color=CYAN, sw=2):
    return (f'<path d="M{x} {y+n}V{y}H{x+n}M{x+w-n} {y}H{x+w}V{y+n}M{x+w} {y+h-n}V{y+h}H{x+w-n}M{x+n} {y+h}H{x}V{y+h-n}" '
            f'fill="none" stroke="{color}" stroke-width="{sw}"/>')

REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
