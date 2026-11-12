#!/usr/bin/env python3
"""Build the profile assets that do not depend on live data. Standard library only.

    python3 scripts/build_assets.py

sec-01..05.svg (station name signs), nav-*.svg (the way to each platform), routemap.svg (skills),
link-x.svg / play-*.svg (guidance signs), footer.svg, and the pictures of the mini games in the
waiting room (pk-*.svg, pass-*.svg, maze-map.svg, game-*.svg). Everything that changes with the
GitHub API is built by update_live.py instead.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403


def nav():
    """Small signs under the header, one per platform; README links each to its section."""
    for n, (ja, _) in enumerate(SECTIONS, 1):
        body = (f'<g font-family="{GOTH}"><rect x="1" y="1" width="122" height="38" rx="6" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="1.5"/>'
                f'<circle cx="21" cy="20" r="13" fill="{LINE[n - 1]}"/>'
                f'<text x="21" y="25.5" text-anchor="middle" font-size="15" font-weight="700" fill="#fff">{n}</text>'
                f'<text x="41" y="26" font-size="16" font-weight="700" fill="#111">{ja}</text></g>')
        save(f"nav-{n}.svg", 124, 40, body, f"{n} 番線 {ja}")


SECTIONS = [("ご案内", "INFORMATION"), ("制作物", "PROJECTS"), ("技術領域", "SKILLS"), ("運行記録", "ACTIVITY"),
            ("待合室", "WAITING ROOM")]


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
           f'<text x="{W - 24}" y="37" text-anchor="end" font-size="12" fill="#666" font-family="{MONO}" letter-spacing="2">TAKOSASI-DEV / 03</text>')
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
    routemap_m(label)


def routemap_m(label):
    """The same map for a phone: the lines leave this station to the right and turn down, one under the other,
    so every name is set level and large, with what is under it on the next line."""
    tall = lambda stops: 62 + sum(64 if under else 46 for _, under in stops)  # noqa: E731
    tops, y = [], 116
    for _, _, stops in ROUTES:
        tops.append(y)
        y += tall(stops) + 18
    H = y - 24
    out = f'<g font-family="{GOTH}">' + sign_m(H, "路線図", "SKILL MAP")
    for (name, col, stops), y0 in zip(ROUTES, tops):
        pw = text_w(name, 20) + 28
        end = y0 + tall(stops) - 30
        out += (f'<path d="M36 {y0}H86q14 0 14 14V{end}" fill="none" stroke="{col}" stroke-width="10" stroke-linecap="round"/>'
                f'<rect x="122" y="{y0 - 17}" width="{pw:.0f}" height="34" rx="17" fill="{col}"/>'
                f'<text x="{122 + pw / 2:.0f}" y="{y0 + 7}" text-anchor="middle" font-size="20" font-weight="700" fill="#fff">{name}</text>')
        sy = y0 + 62
        for stop, under in stops:
            out += (f'<circle cx="100" cy="{sy}" r="11" fill="#fff" stroke="#222" stroke-width="4"/>'
                    f'<text x="124" y="{sy + 9}" font-size="25" font-weight="700" fill="#111">{esc(stop)}</text>')
            if under:
                out += f'<text x="125" y="{sy + 34}" font-size="{SMALL}" fill="#555">{esc(" ・ ".join(under))}</text>'
            sy += 64 if under else 46
    out += (f'<rect x="20" y="{tops[0] - 20}" width="32" height="{tops[-1] - tops[0] + 40}" rx="16" fill="#fff" stroke="#222" stroke-width="5"/>'
            f'<text x="36" y="{tops[0] - 30}" text-anchor="middle" font-size="{SMALL}" font-weight="700" fill="#111">当駅</text></g>')
    save("routemap-m.svg", WM, H, out, label)


def sign(name, play, small, big):
    """A guidance sign, 440x72: yellow for the way out to X, blue for the games you can play in a browser,
    green (play="gate") for the ticket gate that leads to the Pages site."""
    if play == "gate":
        bg, edge, fg = "#0b7a43", "#064a28", "#fff"
        mark = ('<rect x="12" y="16" width="13" height="42" rx="3" fill="#fff"/><rect x="47" y="16" width="13" height="42" rx="3" fill="#fff"/>'
                '<path d="M25 30l11 7l-11 7zM47 30l-11 7l11 7z" fill="#fff" opacity=".8"/>')
    elif play:
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


# --------------------------------------------------------------------------- waiting room (mini games)
# README cannot run code, so a game is pictures plus folded blocks that hold the answers.
# The answers themselves are written in README.md; keep them in step with the tables here.

# Game 1. Rules are read top to bottom and the first match decides. (verdict, protocol, source, port)
RULES = [("落とす", "すべて", "198.51.100.0/24", "すべて"), ("通す", "TCP", "どこからでも", "443"),
         ("通す", "UDP", "どこからでも", "53"), ("通す", "TCP", "192.0.2.0/24", "22")]
PACKETS = [("TCP", "203.0.113.7", "443"), ("UDP", "203.0.113.20", "53"), ("TCP", "198.51.100.9", "443"),
           ("TCP", "203.0.113.80", "22"), ("UDP", "192.0.2.44", "22")]


def packet_game():
    rows = RULES + [("落とす", "どれにも合わない", "", "")]
    b = Board("k", LED_X, 58, LED_COLS, 4 + 20 * len(rows))
    for i, (verdict, proto, src, port) in enumerate(rows):
        y = 4 + i * 20
        b.put(F16, str(i + 1) if i < len(RULES) else "*", 6, y, AMBER)
        b.put(F16, verdict, 24, y, GREEN if verdict == "通す" else RED, invert=True)
        b.put(F16, proto, 84, y, AMBER)
        b.put(F16, src, 146, y, AMBER)
        b.put(F16, port, 397, y, GREEN, right=True)
    h = 58 + b.h + 17
    heads = (f'<g font-family="{GOTH}" font-size="10.5" fill="#aab0b8"><text x="31" y="50">順</text><text x="69" y="50">判定</text>'
             f'<text x="189" y="50">プロトコル</text><text x="313" y="50">送信元</text><text x="815" y="50" text-anchor="end">宛先ポート</text></g>')
    save("pk-rules.svg", W, h, casing(W, h, "検問の規則", "Rules", "上から順に見て、最初に合った行で決まります") + heads + b.svg(),
         "検問の規則")
    for i, (proto, src, port) in enumerate(PACKETS, 1):
        p = Board("q", LED_X, 14, LED_COLS, 20)
        w = p.put(F16, f"{i}/{len(PACKETS)}", 7, 2, AMBER, invert=True)
        p.put(F16, f"{proto}　{src} から　ポート {port} へ", 15 + w, 2, GREEN)
        save(f"pk-{i}.svg", W, 70, casing(W, 70) + p.svg(), f"パケット {i}: {proto}、{src} から、ポート {port} へ")


# Game 2. (what passes, seconds it takes to cross the board)
TRAINS = [("回送 4821", 1.6), ("快速 7306", 0.9), ("特急 9154", 0.5)]


def passing_game():
    for i, (text, secs) in enumerate(TRAINS, 1):
        b = Board("v", LED_X, 40, LED_COLS, 60)
        b.put(F16, "まもなく列車が通過します", 5, 3, GREEN)
        b.fly(F16, text, 24, AMBER, secs, 5)
        save(f"pass-{i}.svg", W, 177, casing(W, 177, "通過列車", f"Level {i}", "5 秒ごとに通過します") + b.svg() + seam(b, 21),
             f"レベル {i}: 列車の案内が LED の板を通過する")  # the label must not give the answer away


# Game 3. The map for the transfer maze. station: (x, y, where the name goes: dx, dy, anchor)
STOPS = {
    "アイデア": (90, 170, 0, -24, "middle"), "仕様書": (270, 90, 0, -22, "middle"), "完璧な設計": (500, 90, 0, -22, "middle"),
    "実装": (420, 170, 0, -22, "middle"), "テスト": (570, 170, 0, 36, "middle"), "実機確認待ち": (750, 170, 0, -22, "middle"),
    "リリース": (700, 70, 22, 8, "start"), "いきなり実装": (270, 250, 0, -22, "middle"), "バグの山": (500, 250, 0, -22, "middle"),
    "新しい道具": (90, 282, 22, 8, "start"), "積みプロジェクト": (90, 350, 22, 8, "start"),
}
# (line name, colour, path, where its name tag sits)
TRACKS = [
    ("仕様線", "#00a7db", "M90 170L180 90H500", (385, 90)),
    ("開発線", "#e5404f", "M270 90L360 170H750", (495, 170)),
    ("公開線", "#333", "M570 170L700 70", (628, 124)),
    ("実装線", "#f39700", "M90 170L180 250H500", (385, 250)),
    ("道具線", "#00a650", "M90 170V350", (90, 228)),
    ("リファクタリング環状線", "#8f76d6", "M270 250C205 345 335 345 270 250", (402, 310)),
]


def maze_map():
    H = 384
    out = (f'<g font-family="{GOTH}"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="7" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
           f'<text x="24" y="38" font-size="23" font-weight="700" fill="#111" letter-spacing="3">のりかえ迷路</text>'
           f'<text x="{W - 24}" y="37" text-anchor="end" font-size="14" font-weight="700" fill="#555">アイデア駅からリリース駅へ。3 回の乗車で着けるか</text>')
    for name, col, d, (tx, ty) in TRACKS:
        out += f'<path d="{d}" fill="none" stroke="{col}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>'
    for name, col, d, (tx, ty) in TRACKS:
        tw = len(name) * 15 + 16
        out += (f'<rect x="{tx - tw / 2}" y="{ty - 12}" width="{tw}" height="24" rx="12" fill="{col}"/>'
                f'<text x="{tx}" y="{ty + 5}" text-anchor="middle" font-size="14" font-weight="700" fill="#fff">{name}</text>')
    for name, (x, y, dx, dy, anchor) in STOPS.items():
        ring = {"アイデア": "#111", "リリース": "#00a650"}.get(name)
        out += (f'<circle cx="{x}" cy="{y}" r="{14 if ring else 10}" fill="#fff" stroke="{ring or "#222"}" stroke-width="{7 if ring else 4}"/>'
                f'<text x="{x + dx}" y="{y + dy}" text-anchor="{anchor}" font-size="21" font-weight="700" fill="#111">{name}</text>')
    out += (f'<text x="90" y="124" text-anchor="middle" font-size="13" font-weight="700" fill="#555">スタート</text>'
            f'<text x="722" y="54" font-size="13" font-weight="700" fill="#00a650">ゴール</text></g>')
    save("maze-map.svg", W, H, out, "のりかえ迷路の路線図")


def games():
    packet_game()
    passing_game()
    maze_map()
    for i, (ja, en) in enumerate([("パケット検問ミニ", "PACKET CHECK"), ("通過列車の動体視力テスト", "PASSING TRAIN"),
                                  ("のりかえ迷路", "TRANSFER MAZE"), ("本日の運行占い", "FORTUNE")], 1):
        plate(f"game-{i}.svg", LINE[4], "遊", f"{i:02d}", ja, en)


if __name__ == "__main__":
    import importlib
    import importlib.util

    from update_live import EXTENSIONS

    for name in EXTENSIONS:  # optional modules, see update_live.py
        if importlib.util.find_spec(name):
            getattr(importlib.import_module(name), "static", lambda: None)()
    games()
    nav()
    for n in range(1, len(SECTIONS) + 1):
        section(n)
    routemap()
    sign("link-x.svg", False, "のりかえ　X (Twitter)", "@kou111011051")
    sign("gate.svg", "gate", "改札口　GATE", "構内へ入る")
    sign("play-packet-bouncer.svg", True, "ブラウザで遊ぶ　PLAY", "Packet Bouncer")
    sign("play-rail-rampage.svg", True, "ブラウザで遊ぶ　PLAY", "RailRampage")
    footer()
