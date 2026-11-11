#!/usr/bin/env python3
"""Build the profile assets that do not depend on live data. Standard library only.

    python3 scripts/build_assets.py

header.svg (departure board), sec-01..04.svg (station name signs), routemap.svg (skills),
link-x.svg / play-*.svg (guidance signs), footer.svg. Everything that changes with the GitHub API
is built by update_live.py instead.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403


def header():
    b = Board("h", LED_X, 61, LED_COLS, 86)
    b.put(F16, "TAKOSASI-DEV", 5, 4, AMBER, scale=2)
    b.put(F16, "インフラ/ネットワーク", 207, 4, GREEN)
    b.put(F16, "/セキュリティ", 207, 21, GREEN)
    w = b.put(F16, "運行情報", 7, 44, RED, invert=True)
    b.put(F16, "全系統 正常稼働中", 7 + w + 8, 44, GREEN)
    b.put(F16, "のりば 1-4", 397, 44, AMBER, right=True)
    b.ticker(F16, "ゲーム、デスクトップツール、プラグインなど、思いついた物を作っています。　　"
                  "GAMES, DESKTOP TOOLS, PLUGINS AND WHATEVER COMES TO MIND.　　　", 66, AMBER)
    spots = "".join(
        f'<circle cx="{1012 + i * 44}" cy="56" r="15" fill="{c}"/>'
        f'<text x="{1012 + i * 44}" y="62" text-anchor="middle" font-size="17" font-weight="700" fill="#fff">{i + 1}</text>'
        for i, c in enumerate(LINE))
    body = (
        f'<g transform="scale(.705)"><rect x="180" width="14" height="30" fill="#33373e"/><rect x="1006" width="14" height="30" fill="#33373e"/>'
        f'<rect x="6" y="24" width="1188" height="328" rx="10" fill="{BODY}" stroke="{EDGE}"/>'
        f'<rect x="16" y="26" width="1168" height="2" fill="#6a717b" opacity=".45"/>'
        f'<g font-family="{GOTH}"><rect x="30" y="38" width="36" height="36" rx="5" fill="#1d63c4"/>'
        f'<path d="M40 49h16a3 3 0 0 1 3 3v11a3 3 0 0 1-3 3H40a3 3 0 0 1-3-3V52a3 3 0 0 1 3-3zm1 4v6h14v-6zm1 9.5a1.5 1.5 0 1 0 .01 0zm12 0a1.5 1.5 0 1 0 .01 0zM42 66l-3 4m15-4l3 4" fill="#fff" stroke="#fff" stroke-width="1.6" fill-rule="evenodd"/>'
        f'<text x="80" y="66" font-size="26" font-weight="700" fill="#f2f2ee" letter-spacing="4">発車案内</text>'
        f'<text x="214" y="65" font-size="15" fill="#aab0b8" letter-spacing="1">Departures</text>'
        f'<text x="930" y="62" font-size="15" fill="#aab0b8">のりば</text>{spots}</g></g>'
        + b.svg() + seam(b, 41) + seam(b, 63))
    save("header.svg", W, 252, body, "TAKOSASI-DEV 発車案内。インフラ、ネットワーク、セキュリティ。全系統 正常稼働中")


SECTIONS = [("ご案内", "INFORMATION"), ("技術領域", "SKILLS"), ("制作物", "PROJECTS"), ("運行記録", "ACTIVITY")]


def section(n):
    """A station name sign: this section in the middle, the neighbours on the band."""
    c, (ja, en) = LINE[n - 1], SECTIONS[n - 1]
    prev = f'<text x="30" y="88" font-size="15" font-weight="700" fill="#fff">◀ {SECTIONS[n - 2][0]}</text>' if n > 1 else ""
    nxt = f'<text x="1170" y="88" text-anchor="end" font-size="15" font-weight="700" fill="#fff">{SECTIONS[n][0]} ▶</text>' if n < len(SECTIONS) else ""
    body = (
        f'<g font-family="{GOTH}"><rect x="2" y="6" width="1196" height="100" rx="7" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
        f'<rect x="3" y="70" width="1194" height="24" fill="{c}"/>'
        f'<rect x="520" y="70" width="160" height="24" fill="#000" opacity=".28"/>'
        f'<circle cx="64" cy="38" r="24" fill="{c}"/>'
        f'<text x="64" y="48" text-anchor="middle" font-size="30" font-weight="700" fill="#fff">{n}</text>'
        f'<text x="98" y="46" font-size="17" font-weight="700" fill="#333">番線</text>'
        f'<text x="600" y="54" text-anchor="middle" font-size="44" font-weight="700" fill="#111" letter-spacing="10">{ja}</text>'
        f'<text x="600" y="88" text-anchor="middle" font-size="15" font-weight="700" fill="#fff" letter-spacing="5">{en}</text>'
        f'{prev}{nxt}'
        f'<text x="1170" y="44" text-anchor="end" font-size="13" fill="#666" font-family="{MONO}" letter-spacing="2">TAKOSASI-DEV / {n:02d}</text></g>')
    save(f"sec-{n:02d}.svg", 1200, 112, body, f"{n} 番線 {ja} {en}")


# (line name, colour, [(station, [what is under it])])
ROUTES = [
    ("インフラ線", "#f39700", [("Linux", ["AlmaLinux", "Arch", "Debian"]), ("Windows Server", ["AD", "DNS", "IIS"]),
                            ("VMware", ["ESXi", "vSphere"]), ("AWS", ["EC2", "VPC"])]),
    ("セキュリティ線", "#e5404f", [("Network", []), ("Security", []), ("ModSecurity", ["WAF"]), ("Snort", ["IDS"])]),
    ("開発線", "#00a7db", [("Godot", []), ("C++ / JUCE", []), ("TypeScript", []), ("Python", []), ("C#", [])]),
]


def routemap():
    """Skills as a route map: three lines leaving this station. Names are slanted so they stay large on a phone."""
    ys = [155 + i * 175 for i in range(len(ROUTES))]
    H = ys[-1] + 38
    out = (f'<g font-family="{GOTH}"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="7" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
           f'<text x="24" y="38" font-size="23" font-weight="700" fill="#111" letter-spacing="4">路線図</text>'
           f'<text x="112" y="37" font-size="12" fill="#666" font-family="{MONO}" letter-spacing="2">SKILL MAP</text>'
           f'<text x="{W - 24}" y="37" text-anchor="end" font-size="12" fill="#666" font-family="{MONO}" letter-spacing="2">TAKOSASI-DEV / 02</text>')
    for (name, col, stops), y in zip(ROUTES, ys):
        step = 140 if len(stops) <= 4 else 115
        xs = [250 + i * step for i in range(len(stops))]
        pw = len(name) * 20 + 22
        out += (f'<path d="M60 {y}H{xs[-1] + 46}" stroke="{col}" stroke-width="10" stroke-linecap="round"/>'
                f'<rect x="86" y="{y - 48}" width="{pw}" height="30" rx="15" fill="{col}"/>'
                f'<text x="{86 + pw / 2}" y="{y - 26}" text-anchor="middle" font-size="19" font-weight="700" fill="#fff">{name}</text>')
        for x, (stop, under) in zip(xs, stops):
            out += (f'<circle cx="{x}" cy="{y}" r="11" fill="#fff" stroke="#222" stroke-width="4"/>'
                    f'<text transform="translate({x + 8} {y - 20}) rotate(-30)" font-size="26" font-weight="700" fill="#111">{esc(stop)}</text>')
            out += "".join(f'<text x="{x}" y="{y + 32 + k * 16}" text-anchor="middle" font-size="13.5" fill="#555">{esc(u)}</text>'
                           for k, u in enumerate(under))
    out += (f'<rect x="44" y="{ys[0] - 18}" width="32" height="{ys[-1] - ys[0] + 36}" rx="16" fill="#fff" stroke="#222" stroke-width="5"/>'
            f'<text x="60" y="{ys[0] - 30}" text-anchor="middle" font-size="15" font-weight="700" fill="#111">当駅</text></g>')
    label = "路線図。" + "。".join(f"{n}: {'、'.join(s for s, _ in stops)}" for n, _, stops in ROUTES)
    save("routemap.svg", W, H, out, label)


def sign(name, play, small, big):
    """A guidance sign, 440x72: yellow for the way out to X, blue for the games you can play in a browser."""
    if play:
        bg, edge, fg = "#1d4f9e", "#0d2a57", "#fff"
        mark = '<circle cx="36" cy="36" r="24" fill="#fff"/><path d="M28 23v26l22-13z" fill="#1d4f9e"/>'
    else:
        bg, edge, fg = "#ffd500", "#1a1a1a", "#1a1a1a"
        mark = ('<rect x="10" y="10" width="52" height="52" rx="6" fill="#1a1a1a"/>'
                '<path d="M24 23l24 26m0-26l-24 26" stroke="#fff" stroke-width="6" stroke-linecap="round"/>')
    body = (f'<rect x="1" y="1" width="438" height="70" rx="7" fill="{bg}" stroke="{edge}" stroke-width="2"/>{mark}'
            f'<text x="76" y="28" font-family="{GOTH}" font-size="13" font-weight="700" fill="{fg}" opacity=".85" letter-spacing="1">{small}</text>'
            f'<text x="76" y="55" font-family="{MONO}" font-size="22" font-weight="800" fill="{fg}">{esc(big)}</text>'
            f'<path d="M388 36h30m-11-11l11 11l-11 11" fill="none" stroke="{fg}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
    save(name, 440, 72, body, f"{small} {big}")


def footer():
    b = Board("f", LED_X, 14, LED_COLS, 20)
    s = "本日もご利用ありがとうございました"
    b.put(F16, s, (LED_COLS - F16.width(s)) // 2, 2, GREEN)
    save("footer.svg", W, 70, casing(W, 70) + b.svg(), s)


if __name__ == "__main__":
    header()
    for n in range(1, len(SECTIONS) + 1):
        section(n)
    routemap()
    sign("link-x.svg", False, "のりかえ　X (Twitter)", "@kou111011051")
    sign("play-packet-bouncer.svg", True, "ブラウザで遊ぶ　PLAY", "Packet Bouncer")
    sign("play-rail-rampage.svg", True, "ブラウザで遊ぶ　PLAY", "RailRampage")
    footer()
