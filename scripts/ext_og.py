#!/usr/bin/env python3
"""The picture shown when a link to the profile or the Pages site is pasted into X, Discord and the like.

static() draws assets/og.svg (1280x640). Chat apps want a PNG, so it is turned into docs/og.png by hand
with a headless browser whenever the design changes (nothing on Actions does this):

    chrome --headless=new --force-prefers-reduced-motion --window-size=1280,640 --screenshot=docs/og.png assets/og.svg

docs/og.png is what the meta tags of the Pages site point at, and what is uploaded as the repo's
social preview in the GitHub settings.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import flap  # noqa: E402
from style import *  # noqa: E402,F403


def static():
    title, _, _ = flap.board("a", 0, 0, [["TAKOSASI-DEV"]], 12, 64, 80, gap=3)  # 801 wide, drawn 1.4 times as large
    b = Board("b", 37, 340, 402, 64, 3)
    w = b.put(F16, "運行情報", 7, 5, RED, invert=True)
    b.put(F16, "全系統 正常稼働中", 15 + w, 5, GREEN)
    b.put(F16, "のりば 1-5", 397, 5, AMBER, right=True)
    b.put(F16, "インフラ ・ ネットワーク ・ セキュリティ", 7, 25, AMBER)
    b.put(F16, "ゲーム・ツール・プラグインなどを作っています", 7, 45, AMBER)
    spots = "".join(f'<circle cx="{1010 + i * 50}" cy="96" r="17" fill="{c}"/>'
                    f'<text x="{1010 + i * 50}" y="103" text-anchor="middle" font-size="19" font-weight="700" fill="#fff">{i + 1}</text>'
                    for i, c in enumerate(LINE))
    body = (f'<rect width="1280" height="640" fill="#0d1117"/>'
            f'<rect x="250" width="16" height="46" fill="#33373e"/><rect x="1014" width="16" height="46" fill="#33373e"/>'
            f'<rect x="14" y="40" width="1252" height="560" rx="12" fill="{BODY}" stroke="{EDGE}" stroke-width="2"/>'
            f'<rect x="26" y="43" width="1228" height="2" fill="#6a717b" opacity=".45"/>'
            f'<g font-family="{GOTH}"><text x="40" y="106" font-size="32" font-weight="700" fill="#f2f2ee" letter-spacing="5">発車案内</text>'
            f'<text x="208" y="105" font-size="18" fill="#aab0b8" letter-spacing="1">Departures</text>'
            f'<text x="916" y="102" font-size="18" fill="#aab0b8">のりば</text>{spots}'
            f'<text x="1240" y="588" text-anchor="end" font-size="15" fill="#8d949d" font-family="{MONO}" letter-spacing="1">github.com/takosasi-dev</text></g>'
            f'<g transform="translate(79 162) scale(1.4)">{title}</g>' + b.svg() + seam(b, 22) + seam(b, 42))
    save("og.svg", 1280, 640, body, "TAKOSASI-DEV 発車案内。インフラ、ネットワーク、セキュリティ")


if __name__ == "__main__":
    static()
