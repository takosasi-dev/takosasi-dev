#!/usr/bin/env python3
"""assets/depot.svg and depot-m.svg: the depot sign under the route map. The route map says what I can build
with; this one says what is on the desk: the two machines, what is plugged in, the tools.

GEAR below is written by hand. Model names only: no host name, no serial number, no settings.
README.md and README.en.md repeat the list in the alt text of the picture, for readers who do not see it;
the self-check fails when a value is missing there. build_assets.py calls static(). Standard library only.

    python3 scripts/ext_depot.py    # self-check
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

# (track, what it holds, English tag, colour, [(label, value)]). On the wide sign the first two tracks are the
# left column and the last two the right one; on the phone they follow one another in this order.
GEAR = [
    ("1 号車", "デスクトップ", "DESKTOP", "#00a650", [
        ("CPU", "Intel Core i7-11700F"),
        ("GPU", "GeForce RTX 3070 Ti"),
        ("GPU 2", "GeForce GTX 1050 Ti"),
        ("メモリ", "32GB DDR4"),
        ("マザーボード", "MSI MPG Z490 GAMING PLUS"),
        ("ストレージ", "NVMe 1TB + SATA 1TB"),
        ("OS", "Windows 11 Home"),
    ]),
    # The laptop. CPU, GPU, memory and screen were read on the machine; the exact model (X6 or XZ) is not known,
    # and the storage is the catalogue value of every X-series model with this CPU.
    ("2 号車", "ノート PC", "LAPTOP", "#f39700", [
        ("機種", "dynabook X"),
        ("CPU", "Intel Core i5-1340P"),
        ("GPU", "Intel Iris Xe Graphics"),
        ("メモリ", "16GB"),
        ("ストレージ", "SSD 512GB"),
        ("画面", "13.3 型 WUXGA"),
        ("OS", "Windows 11"),
    ]),
    ("装備", "周辺機器", "GEAR", "#8f76d6", [
        ("モニター", "iiyama ×2 + SHARP ×1"),
        ("サウンド", "Sound BlasterX AE-5 Plus"),
        ("マイク", "M-AUDIO Uber Mic"),
        ("カメラ", "Logicool C920"),
        ("キャプチャ", "AVerMedia Live Gamer Ultra"),
        ("キーボード", "Logicool G913 TKL"),
        ("マウス", "Logicool PRO X SUPERLIGHT 2"),
    ]),
    ("工具", "ソフト", "TOOLS", "#009bbf", [
        ("エディタ", "VS Code"),
        ("AI", "Claude Code"),
        ("ノート", "Obsidian"),
        ("Linux", "WSL2 / Arch Linux"),
        ("版管理", "Git / GitHub CLI"),
        ("ブラウザ", "Chrome"),
    ]),
]
NOTE = "使っている機材とソフト"
COL, KEY = (W - 48) // 2, 104   # a track on the wide sign, and the part of it that holds the label
ROOM = COL - 32 - KEY - 14      # what is left for a value
ONE = WM - 20 - 58              # the room on the phone sign for a label and its value on one line


def label():
    return f"車両基地。{NOTE}。" + "。".join(f"{name}({what}): " + "、".join(f"{k} {v}" for k, v in rows) for name, what, _, _, rows in GEAR)


def static():
    step, tops = 36, [58]
    for r in range(len(GEAR) // 2 - 1):  # a row of the grid is as tall as the longer of its two tracks
        tops.append(tops[-1] + 58 + step * (max(len(GEAR[r][4]), len(GEAR[r + 2][4])) - 1) + 46)
    H = tops[-1] + 58 + step * (max(len(GEAR[1][4]), len(GEAR[3][4])) - 1) + 28
    out = (f'<g font-family="{GOTH}"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="7" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
           f'<text x="24" y="38" font-size="23" font-weight="700" fill="#111" letter-spacing="4">車両基地</text>'
           f'<text x="140" y="37" font-size="12" fill="#666" font-family="{MONO}" letter-spacing="2">DEPOT</text>'
           f'<text x="{W - 24}" y="37" text-anchor="end" font-size="13" font-weight="700" fill="#555">{NOTE}</text>')
    for i, (name, what, en, col, rows) in enumerate(GEAR):
        x, y0, pw = 24 + i // 2 * COL, tops[i % 2], text_w(name, 19) + 26
        out += (f'<path d="M{x + 13} {y0 + 16}V{y0 + 58 + step * (len(rows) - 1)}" stroke="{col}" stroke-width="7" stroke-linecap="round"/>'
                f'<rect x="{x}" y="{y0}" width="{pw:.0f}" height="30" rx="15" fill="{col}"/>'
                f'<text x="{x + pw / 2:.0f}" y="{y0 + 22}" text-anchor="middle" font-size="19" font-weight="700" fill="#fff">{name}</text>'
                f'<text x="{x + pw + 10:.0f}" y="{y0 + 21}" font-size="15" font-weight="700" fill="#333">{what}</text>'
                f'<text x="{x + pw + 18 + text_w(what, 15):.0f}" y="{y0 + 20}" font-size="11" fill="#666" font-family="{MONO}" letter-spacing="1.5">{en}</text>')
        for k, (key, value) in enumerate(rows):
            y = y0 + 58 + k * step
            # A long model name is squeezed instead of running into the next track.
            squeeze = f' textLength="{ROOM}" lengthAdjust="spacingAndGlyphs"' if text_w(value, 17) > ROOM else ""
            out += (f'<circle cx="{x + 13}" cy="{y}" r="7" fill="#fff" stroke="#222" stroke-width="3"/>'
                    f'<text x="{x + 32}" y="{y + 5}" font-size="13" font-weight="700" fill="#666">{esc(key)}</text>'
                    f'<text x="{x + 32 + KEY}" y="{y + 6}" font-size="17" font-weight="700" fill="#111"{squeeze}>{esc(value)}</text>')
    save("depot.svg", W, H, out + "</g>", label())
    draw_m()


def draw_m():
    """The same sign for a phone (depot-m.svg): the tracks one under the other. A label and its value share
    a line when they fit; a long model name goes under its label."""
    out, y = f'<text x="20" y="72" font-size="{SMALL}" font-weight="700" fill="#555">{NOTE}</text>', 96
    for name, what, _, col, rows in GEAR:
        pw, body, head = text_w(name, 20) + 28, "", y
        y += 62
        for key, value in rows:
            cy = y - 6
            body += (f'<circle cx="36" cy="{cy}" r="8" fill="#fff" stroke="#222" stroke-width="3.5"/>'
                     f'<text x="58" y="{y}" font-size="{SMALL}" font-weight="700" fill="#666">{esc(key)}</text>')
            if text_w(key, SMALL) + 22 + text_w(value, 20) <= ONE:
                body += f'<text x="{WM - 20}" y="{y}" text-anchor="end" font-size="20" font-weight="700" fill="#111">{esc(value)}</text>'
            else:
                for ln in wrap_px(value, 20, WM - 58 - 16):
                    y += 27
                    body += f'<text x="58" y="{y}" font-size="20" font-weight="700" fill="#111">{esc(ln)}</text>'
            y += 38
        out += (f'<path d="M36 {head + 17}V{cy}" stroke="{col}" stroke-width="7" stroke-linecap="round"/>'
                f'<rect x="20" y="{head}" width="{pw:.0f}" height="34" rx="17" fill="{col}"/>'
                f'<text x="{20 + pw / 2:.0f}" y="{head + 24}" text-anchor="middle" font-size="20" font-weight="700" fill="#fff">{name}</text>'
                f'<text x="{20 + pw + 12:.0f}" y="{head + 24}" font-size="20" font-weight="700" fill="#333">{what}</text>' + body)
        y += 10
    H = y - 22
    save("depot-m.svg", WM, H, f'<g font-family="{GOTH}">' + sign_m(H, "車両基地", "DEPOT") + out + "</g>", label())


if __name__ == "__main__":  # self-check: python3 scripts/ext_depot.py
    assert len(GEAR) == 4 and all(rows and all(k and v for k, v in rows) for *_, rows in GEAR)  # static() lays out 2 x 2
    assert all(text_w(k, 13) <= KEY - 8 and text_w(v, 17) <= ROOM / .85 for *_, rows in GEAR for k, v in rows), "too long for its track: shorten it"
    for name in ("README.md", "README.en.md"):  # the alt text of the picture carries the same list
        with open(os.path.join(ROOT, name), encoding="utf-8") as f:
            text = f.read()
        # The English page says the Japanese values in English; what is written the same in both must be there.
        missing = [v for *_, rows in GEAR for _, v in rows if (name == "README.md" or v.isascii()) and esc(v) not in text]
        assert not missing, f"{name}: the alt of depot.svg lacks {missing}. Japanese alt: {label()}"
    print("depot ok")
