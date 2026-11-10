#!/usr/bin/env python3
"""Generate the static animated SVGs used by README.md.

    python3 scripts/build_assets.py

Everything is plain SVG + CSS/SMIL animation (GitHub strips JS), no external
fonts or services, so nothing can break when a third-party server is down.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
USER = "takosasi-dev"


def save(name, svg):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print("wrote", name, len(svg))


# --------------------------------------------------------------------------- header
def header():
    W, H = 1200, 440
    title = "TAKOSASI-DEV"
    t_attr = f'x="150" y="218" textLength="700" lengthAdjust="spacingAndGlyphs" font-family="{MONO}" font-size="96" font-weight="800"'
    vertical = "全系統正常稼働"
    vtext = "".join(
        f'<text x="78" y="{108 + i * 40}" text-anchor="middle" font-family="{MIN}" font-size="32" font-weight="900" fill="{ORANGE}">{c}</text>'
        for i, c in enumerate(vertical))
    # perspective floor
    floor = ""
    for k in range(-14, 15):
        floor += f'<line x1="600" y1="322" x2="{600 + k * 150}" y2="410"/>'
    hl = "".join(f'<line class="fl" style="animation-delay:{-i * 0.5:.1f}s" x1="0" y1="324" x2="{W}" y2="324"/>' for i in range(6))
    # radar
    cx, cy = 1015, 180
    rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>' for r in (38, 76, 114))
    ticks = ""
    for a in range(0, 360, 15):
        r1, r2 = (118, 128) if a % 45 else (118, 134)
        x1, y1 = cx + r1 * math.cos(math.radians(a)), cy + r1 * math.sin(math.radians(a))
        x2, y2 = cx + r2 * math.cos(math.radians(a)), cy + r2 * math.sin(math.radians(a))
        ticks += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'
    blips = ""
    for i, (a, r, col) in enumerate([(310, 60, GREEN), (40, 92, CYAN), (150, 48, MAG), (215, 98, AMBER)]):
        bx, by = cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
        # sweep passes angle a at (a/360)*4s
        blips += f'<circle class="blip" style="animation-delay:{a / 360 * 4 - 4:.2f}s" cx="{bx:.1f}" cy="{by:.1f}" r="4" fill="{col}"/>'
    ticker = ("SYSTEM ONLINE  //  INFRASTRUCTURE  //  NETWORK  //  SECURITY  //  GAME DEV  //  DESKTOP TOOLS  //  "
              "OBSIDIAN PLUGINS  //  CHROME EXTENSIONS  //  MINECRAFT ADD-ONS  //  ALL SYSTEMS NOMINAL  //  ")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{USER} - infrastructure, network, security, games and tools">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a1020"/><stop offset=".7" stop-color="{BG}"/><stop offset="1" stop-color="#12041a"/></linearGradient>
<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset=".85" stop-color="{CYAN}" stop-opacity=".16"/><stop offset="1" stop-color="{CYAN}" stop-opacity=".5"/></linearGradient>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG}"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient>
<linearGradient id="ttl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#bfefff"/></linearGradient>
<radialGradient id="glow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{CYAN}" stop-opacity=".22"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
<linearGradient id="sw" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{GREEN}" stop-opacity="0"/><stop offset="1" stop-color="{GREEN}" stop-opacity=".55"/></linearGradient>
{hex_pattern("hex", 26, CYAN, 0.085)}
<pattern id="lines" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".28"/></pattern>
<clipPath id="c"><rect width="{W}" height="{H}" rx="16"/></clipPath>
<clipPath id="slice"><rect x="0" y="168" width="{W}" height="22"/></clipPath>
<clipPath id="tk"><rect x="0" y="408" width="{W}" height="32"/></clipPath>
</defs>
<style>
.fl{{stroke:{MAG};stroke-width:1.4;animation:fl 3s cubic-bezier(.6,0,1,.6) infinite}}
@keyframes fl{{0%{{transform:translateY(0);opacity:0}}15%{{opacity:.7}}100%{{transform:translateY(86px);opacity:.9}}}}
.scan{{animation:scan 6s linear infinite}}
@keyframes scan{{0%{{transform:translateY(-140px)}}100%{{transform:translateY(440px)}}}}
.ga{{animation:ga 5s steps(1) infinite}}
.gb{{animation:gb 5s steps(1) infinite}}
@keyframes ga{{0%,100%{{transform:translate(-3px,0)}}60%{{transform:translate(-9px,2px)}}62%{{transform:translate(6px,-1px)}}64%{{transform:translate(-3px,0)}}90%{{transform:translate(-14px,0)}}92%{{transform:translate(-3px,0)}}}}
@keyframes gb{{0%,100%{{transform:translate(3px,0)}}60%{{transform:translate(10px,-2px)}}62%{{transform:translate(-5px,1px)}}64%{{transform:translate(3px,0)}}90%{{transform:translate(12px,0)}}92%{{transform:translate(3px,0)}}}}
.sl{{animation:sl 5s steps(1) infinite;opacity:0}}
@keyframes sl{{0%,100%{{opacity:0}}60%{{opacity:1;transform:translateX(26px)}}62%{{opacity:1;transform:translateX(-18px)}}64%{{opacity:0}}90%{{opacity:1;transform:translateX(-34px)}}92%{{opacity:0}}}}
.sweep{{transform-origin:{cx}px {cy}px;animation:rot 4s linear infinite}}
.rot2{{transform-origin:{cx}px {cy}px;animation:rot 40s linear infinite reverse}}
@keyframes rot{{to{{transform:rotate(360deg)}}}}
.blip{{opacity:0;animation:blip 4s linear infinite}}
@keyframes blip{{0%{{opacity:1}}55%{{opacity:.15}}100%{{opacity:0}}}}
.bl{{animation:bl 1.2s steps(1) infinite}}
@keyframes bl{{50%{{opacity:.15}}}}
.tick{{animation:tick 38s linear infinite}}
@keyframes tick{{to{{transform:translateX(-50%)}}}}
.in{{animation:in .6s ease-out both}}
@keyframes in{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
.bar{{transform-origin:150px 0;animation:bar 1.1s cubic-bezier(.2,.8,.2,1) both}}
@keyframes bar{{from{{transform:scaleX(0)}}}}
{REDUCED}
</style>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="{H}" fill="url(#hex)"/>
<circle cx="{cx}" cy="{cy}" r="230" fill="url(#glow)"/>
<g stroke="{MAG}" stroke-opacity=".38" stroke-width="1">{floor}</g>
{hl}
<rect x="0" y="300" width="{W}" height="60" fill="url(#fade)"/>
<line x1="0" y1="322" x2="{W}" y2="322" stroke="{MAG}" stroke-opacity=".8" stroke-width="1.5"/>

<!-- left vertical banner -->
<rect x="48" y="62" width="60" height="302" fill="{BG}" fill-opacity=".75" stroke="{ORANGE}" stroke-width="2"/>
<rect x="48" y="62" width="60" height="8" fill="{ORANGE}"/><rect x="48" y="356" width="60" height="8" fill="{ORANGE}"/>
{vtext}

<!-- title -->
<text class="in" style="animation-delay:.2s" x="152" y="100" font-family="{MONO}" font-size="15" letter-spacing="4" fill="{CYAN}">IDENT // GITHUB OPERATOR FILE</text>
<g>
<text class="ga" {t_attr} fill="{CYAN}" fill-opacity=".85">{title}</text>
<text class="gb" {t_attr} fill="{MAG}" fill-opacity=".85">{title}</text>
<text {t_attr} fill="url(#ttl)">{title}</text>
<g clip-path="url(#slice)"><text class="sl" {t_attr} fill="#fff">{title}</text></g>
</g>
<rect class="bar" x="150" y="238" width="700" height="4" fill="{CYAN}"/>
<rect class="bar" style="animation-delay:.25s" x="150" y="246" width="260" height="2" fill="{MAG}"/>
<text class="in" style="animation-delay:.7s" x="152" y="280" font-family="{MONO}" font-size="19" letter-spacing="2.5" fill="{TEXT}">INFRASTRUCTURE / NETWORK / SECURITY</text>
<text class="in" style="animation-delay:1s" x="152" y="306" font-family="{MONO}" font-size="15" letter-spacing="2.5" fill="{DIM}">+ GAMES, DESKTOP TOOLS, PLUGINS AND WHATEVER COMES TO MIND</text>

<!-- radar -->
<g fill="none" stroke="{CYAN}" stroke-opacity=".5" stroke-width="1">{rings}<line x1="{cx-126}" y1="{cy}" x2="{cx+126}" y2="{cy}"/><line x1="{cx}" y1="{cy-126}" x2="{cx}" y2="{cy+126}"/></g>
<g class="rot2" stroke="{CYAN}" stroke-opacity=".8" stroke-width="1.5">{ticks}</g>
<g class="sweep"><path d="M{cx} {cy}L{cx+114} {cy}A114 114 0 0 0 {cx + 114*math.cos(math.radians(-55)):.1f} {cy + 114*math.sin(math.radians(-55)):.1f}Z" fill="url(#sw)"/><line x1="{cx}" y1="{cy}" x2="{cx+114}" y2="{cy}" stroke="{GREEN}" stroke-width="2"/></g>
{blips}
<circle cx="{cx}" cy="{cy}" r="3" fill="{GREEN}"/>
<text x="{cx-126}" y="{cy+158}" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{CYAN}">SCAN // 4 CONTACTS</text>
<text x="{cx+126}" y="{cy+158}" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{GREEN}" class="bl">TRACKING</text>

<!-- HUD -->
{brackets(18, 18, W - 36, 380, 22, CYAN, 2)}
<text x="150" y="44" font-family="{MONO}" font-size="12" letter-spacing="3" fill="{DIM}">SYS.BOOT OK</text>
<text x="300" y="44" font-family="{MONO}" font-size="12" letter-spacing="3" fill="{DIM}">NODE: JP</text>
<text x="420" y="44" font-family="{MONO}" font-size="12" letter-spacing="3" fill="{DIM}">LINK: ENCRYPTED</text>
<circle class="bl" cx="{W-170}" cy="40" r="5" fill="{GREEN}"/>
<text x="{W-156}" y="44" font-family="{MONO}" font-size="12" letter-spacing="3" fill="{GREEN}">ONLINE</text>

<!-- ticker -->
<rect x="0" y="408" width="{W}" height="32" fill="{ORANGE}"/>
<g clip-path="url(#tk)"><g class="tick"><text x="0" y="430" font-family="{MONO}" font-size="15" font-weight="700" letter-spacing="2" fill="#0a0a0a" xml:space="preserve">{esc(ticker * 4)}</text></g></g>

<rect class="scan" x="0" y="0" width="{W}" height="140" fill="url(#scan)"/>
<rect width="{W}" height="{H}" fill="url(#lines)"/>
</g>
</svg>'''
    save("header.svg", svg)


# --------------------------------------------------------------------------- section headers
def section(name, no, jp, en, color):
    W, H = 1200, 84
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{esc(en)}">
<defs><pattern id="hz" width="28" height="28" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="14" height="28" fill="{color}"/></pattern>
<clipPath id="c"><rect x="{W-250}" y="30" width="230" height="24"/></clipPath></defs>
<style>.m{{animation:m 1.6s linear infinite}}@keyframes m{{to{{transform:translateX(39.6px)}}}}
.p{{animation:p 2.4s ease-in-out infinite}}@keyframes p{{50%{{opacity:.35}}}}
.d{{stroke-dasharray:6 10;animation:d 1.2s linear infinite}}@keyframes d{{to{{stroke-dashoffset:-16}}}}{REDUCED}</style>
<rect width="{W}" height="{H}" rx="10" fill="{BG}"/>
<rect x="20" y="18" width="84" height="48" fill="{color}"/>
<text x="62" y="54" text-anchor="middle" font-family="{MONO}" font-size="32" font-weight="800" fill="#06080c">{no}</text>
<text x="126" y="57" font-family="{MIN}" font-size="40" font-weight="900" fill="#fff" letter-spacing="6">{jp}</text>
<text x="{126 + len(jp) * 46 + 26}" y="40" font-family="{MONO}" font-size="13" letter-spacing="4" fill="{color}">{esc(en)}</text>
<text class="p" x="{126 + len(jp) * 46 + 26}" y="60" font-family="{MONO}" font-size="11" letter-spacing="3" fill="{DIM}">SECTION {no} / ACCESS GRANTED</text>
<line class="d" x1="{126 + len(jp) * 46 + 330}" y1="42" x2="{W-270}" y2="42" stroke="{color}" stroke-opacity=".7" stroke-width="2"/>
<g clip-path="url(#c)"><rect class="m" x="{W-330}" y="30" width="330" height="24" fill="url(#hz)"/></g>
<rect x="{W-250}" y="30" width="230" height="24" fill="none" stroke="{color}" stroke-width="1.5"/>
</svg>'''
    save(name, svg)


# --------------------------------------------------------------------------- terminal
def terminal():
    W, H = 1200, 330
    lines = [
        ("cmd", "whoami"),
        ("out", "takosasi-dev"),
        ("cmd", "cat focus.txt"),
        ("out", "infrastructure / network / security  (Windows Server, VMware, Linux, AWS, ModSecurity, Snort)"),
        ("cmd", "ls ~/builds"),
        ("out", "games/  desktop-tools/  server-tools/  obsidian-plugins/  chrome-extensions/  minecraft-addons/"),
        ("cmd", "uptime"),
        ("out", "up since day one,  load average: too many ideas"),
    ]
    CYC = 18.0
    t = 0.6
    css, body = "", ""
    y = 78
    CH = 10.0  # approx glyph advance at 16.5px mono
    for i, (kind, text) in enumerate(lines):
        x = 34
        if kind == "cmd":
            body += f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="16.5" fill="{GREEN}">$</text>'
            tx = x + 22
            n = len(text)
            dur = n * 0.07
            ps, pe = t / CYC * 100, (t + dur) / CYC * 100
            css += (f"@keyframes k{i}{{0%,{ps:.2f}%{{transform:translateX(0);animation-timing-function:steps({n},end)}}"
                    f"{pe:.2f}%{{transform:translateX({n * CH * 1.15:.0f}px);animation-timing-function:steps(1,end)}}"
                    f"{pe + 0.05:.2f}%,96%{{transform:translateX(1300px)}}96.1%,100%{{transform:translateX(0)}}}}"
                    f".k{i}{{animation:k{i} {CYC}s linear infinite}}")
            body += f'<text x="{tx}" y="{y}" font-family="{MONO}" font-size="16.5" fill="#fff" xml:space="preserve">{esc(text)}</text>'
            body += f'<rect class="k{i}" x="{tx - 2}" y="{y - 18}" width="1300" height="26" fill="#070b14"/>'
            t += dur + 0.35
        else:
            ps = t / CYC * 100
            css += (f"@keyframes k{i}{{0%,{ps:.2f}%{{opacity:0}}{ps + 0.05:.2f}%,96%{{opacity:1}}96.1%,100%{{opacity:0}}}}"
                    f".k{i}{{animation:k{i} {CYC}s steps(1,end) infinite}}")
            body += f'<text class="k{i}" x="{x}" y="{y}" font-family="{MONO}" font-size="16.5" fill="{CYAN}" xml:space="preserve">{esc(text)}</text>'
            t += 0.9
        y += 29
    ps = t / CYC * 100
    css += (f"@keyframes kp{{0%,{ps:.2f}%{{opacity:0}}{ps + 0.05:.2f}%,96%{{opacity:1}}96.1%,100%{{opacity:0}}}}"
            f".kp{{animation:kp {CYC}s steps(1,end) infinite}}.cur{{animation:cur 1s steps(1) infinite}}@keyframes cur{{50%{{opacity:0}}}}")
    body += (f'<g class="kp"><text x="34" y="{y}" font-family="{MONO}" font-size="16.5" fill="{GREEN}">$</text>'
             f'<rect class="cur" x="56" y="{y - 16}" width="10" height="20" fill="{GREEN}"/></g>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="terminal: whoami takosasi-dev, focus on infrastructure, network and security">
<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="12"/></clipPath>
<pattern id="lines" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".25"/></pattern></defs>
<style>{css}{REDUCED}</style>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="#070b14"/>
{body}
<rect width="{W}" height="38" fill="#101829"/>
<circle cx="24" cy="19" r="6" fill="{RED}"/><circle cx="46" cy="19" r="6" fill="{AMBER}"/><circle cx="68" cy="19" r="6" fill="{GREEN}"/>
<text x="{W/2}" y="24" text-anchor="middle" font-family="{MONO}" font-size="13" letter-spacing="2" fill="{DIM}">takosasi@node-jp: ~</text>
<rect width="{W}" height="{H}" fill="url(#lines)"/>
</g>
<rect x=".75" y=".75" width="{W-1.5}" height="{H-1.5}" rx="12" fill="none" stroke="{CYAN}" stroke-opacity=".45" stroke-width="1.5"/>
</svg>'''
    save("terminal.svg", svg)


# --------------------------------------------------------------------------- status (hex panel)
def status():
    W, H = 1200, 400
    R, DX, DY = 64, 111, 96
    y1, y2, y3 = 104, 200, 296
    rows = [
        (y1, 645.5, [("LINUX", ORANGE), ("WIN SERVER", ORANGE), ("VMWARE", ORANGE), ("AWS", ORANGE)]),
        (y2, 590.0, [("NETWORK", RED), ("SECURITY", RED), ("MODSEC", RED), ("SNORT", RED), ("GODOT", CYAN)]),
        (y3, 645.5, [("C++ / JUCE", CYAN), ("TYPESCRIPT", CYAN), ("PYTHON", CYAN), ("C#", CYAN)]),
    ]
    cells, n = "", 0
    for y, x0, items in rows:
        for i, (label, col) in enumerate(items):
            cx = x0 + i * DX
            n += 1
            cells += (f'<g><polygon points="{hex_points(cx, y, R - 4)}" fill="{col}" fill-opacity=".1" stroke="{col}" stroke-width="2.5"/>'
                      f'<polygon class="hx" style="animation-delay:{n * 0.35 - 5:.2f}s" points="{hex_points(cx, y, R - 4)}" fill="{col}"/>'
                      f'<text x="{cx}" y="{y - 22}" text-anchor="middle" font-family="{MONO}" font-size="11" letter-spacing="2" fill="{col}">{n:02d}</text>'
                      f'<text x="{cx}" y="{y + 5}" text-anchor="middle" font-family="{MONO}" font-size="14" font-weight="800" fill="#fff">{esc(label)}</text>'
                      f'<text x="{cx}" y="{y + 26}" text-anchor="middle" font-family="{MONO}" font-size="10" letter-spacing="2" fill="{col}">ACTIVE</text></g>')
    deco = "".join(f'<polygon points="{hex_points(x, y, R - 4)}" fill="none" stroke="{DIM}" stroke-opacity=".5" stroke-width="1.5" stroke-dasharray="4 6"/>'
                   for x, y in [(645.5 - DX, y1), (645.5 + 4 * DX, y1), (645.5 - DX, y3), (645.5 + 4 * DX, y3), (590 + 5 * DX, y2)])
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Skill domains: Linux, Windows Server, VMware, AWS, network, security, ModSecurity, Snort, Godot, C++/JUCE, TypeScript, Python, C#">
<defs>{hex_pattern("hex", 22, ORANGE, 0.07)}
<pattern id="hz" width="32" height="32" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="16" height="32" fill="{ORANGE}"/></pattern>
<clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath>
<clipPath id="s1"><rect x="40" y="40" width="410" height="20"/></clipPath>
<clipPath id="s2"><rect x="40" y="340" width="410" height="20"/></clipPath></defs>
<style>
.hx{{opacity:0;animation:hx 5s linear infinite}}
@keyframes hx{{0%{{opacity:.75}}6%{{opacity:.1}}9%{{opacity:.45}}16%,100%{{opacity:0}}}}
.m{{animation:m 1.4s linear infinite}}@keyframes m{{to{{transform:translateX(45.25px)}}}}
.m2{{animation:m 1.4s linear infinite reverse}}
.bl{{animation:bl 1s steps(1) infinite}}@keyframes bl{{50%{{opacity:.2}}}}
.g{{transform-origin:60px 0;animation:g 2.2s cubic-bezier(.2,.8,.2,1) both}}@keyframes g{{from{{transform:scaleX(0)}}}}
{REDUCED}</style>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="{BG}"/><rect width="{W}" height="{H}" fill="url(#hex)"/>
<g clip-path="url(#s1)"><rect class="m" x="-60" y="40" width="570" height="20" fill="url(#hz)"/></g>
<g clip-path="url(#s2)"><rect class="m2" x="-60" y="340" width="570" height="20" fill="url(#hz)"/></g>
<text x="40" y="96" font-family="{MONO}" font-size="13" letter-spacing="4" fill="{ORANGE}">SKILL DOMAINS // DIAGNOSTIC</text>
<text x="36" y="182" font-family="{MIN}" font-size="84" font-weight="900" fill="#fff" letter-spacing="4">技術領域</text>
<text x="40" y="222" font-family="{MIN}" font-size="24" font-weight="900" fill="{ORANGE}" letter-spacing="10">全項目 稼働中</text>
<g font-family="{MONO}" font-size="12" letter-spacing="2">
<text x="40" y="262" fill="{ORANGE}">INFRA</text><rect x="130" y="252" width="320" height="10" fill="{ORANGE}" fill-opacity=".15"/><rect class="g" x="130" y="252" width="270" height="10" fill="{ORANGE}"/>
<text x="40" y="286" fill="{RED}">SEC/NET</text><rect x="130" y="276" width="320" height="10" fill="{RED}" fill-opacity=".15"/><rect class="g" style="animation-delay:.2s" x="130" y="276" width="250" height="10" fill="{RED}"/>
<text x="40" y="310" fill="{CYAN}">DEV</text><rect x="130" y="300" width="320" height="10" fill="{CYAN}" fill-opacity=".15"/><rect class="g" style="animation-delay:.4s" x="130" y="300" width="300" height="10" fill="{CYAN}"/>
</g>
<circle class="bl" cx="46" cy="326" r="4" fill="{GREEN}"/><text x="58" y="330" font-family="{MONO}" font-size="11" letter-spacing="3" fill="{GREEN}">STATUS: NOMINAL / 13 OF 13</text>
{deco}{cells}
</g>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="none" stroke="{ORANGE}" stroke-opacity=".6" stroke-width="2"/>
</svg>'''
    save("status.svg", svg)


# --------------------------------------------------------------------------- network
def network():
    W, H = 1200, 340

    def node(x, y, w, h, title, sub, col):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{BG2}" stroke="{col}" stroke-width="2"/>'
                f'<rect x="{x}" y="{y}" width="6" height="{h}" fill="{col}"/>'
                f'<text x="{x + 20}" y="{y + h/2 - 2}" font-family="{MONO}" font-size="14" font-weight="800" fill="#fff">{esc(title)}</text>'
                f'<text x="{x + 20}" y="{y + h/2 + 15}" font-family="{MONO}" font-size="10.5" letter-spacing="1" fill="{col}">{esc(sub)}</text>'
                f'<circle class="bl" cx="{x + w - 14}" cy="{y + 14}" r="3.5" fill="{GREEN}"/>')

    mid = 180
    servers = [(62, "LINUX", "AlmaLinux / Arch / Debian"), (128, "WINDOWS SERVER", "AD / DNS / IIS"),
               (194, "VMWARE", "ESXi / vSphere"), (260, "AWS", "EC2 / VPC")]
    p_in = f"M150 {mid}H300"
    p_fw = f"M500 {mid}H580"
    paths, packets = "", ""
    for i, (y, _, _) in enumerate(servers):
        cy = y + 24
        route = f"M150 {mid}L640 {mid}L760 {mid}L820 {cy}L900 {cy}"
        paths += f'<path d="M700 {mid}H760L820 {cy}H900" />'
        for j in range(2):
            col = CYAN if j == 0 else GREEN
            packets += (f'<circle r="4.5" fill="{col}"><animateMotion dur="{3.2 + i * 0.5:.1f}s" begin="{-(i * 0.9 + j * 1.7):.1f}s" '
                        f'repeatCount="indefinite" path="{route}" keyPoints="{"0;1" if j == 0 else "1;0"}" keyTimes="0;1" calcMode="linear"/></circle>')
    # blocked packet: travels to the WAF and gets dropped
    bad = (f'<g><circle r="5" fill="{RED}"><animateMotion dur="4s" repeatCount="indefinite" path="M150 {mid - 0.01}L318 {mid}" keyPoints="0;1;1" keyTimes="0;0.45;1" calcMode="linear"/>'
           f'<animate attributeName="opacity" dur="4s" repeatCount="indefinite" values="1;1;0;0" keyTimes="0;0.45;0.6;1"/></circle>'
           f'<text x="400" y="{mid - 48}" text-anchor="middle" font-family="{MONO}" font-size="13" font-weight="800" letter-spacing="3" fill="{RED}" opacity="0">DROP'
           f'<animate attributeName="opacity" dur="4s" repeatCount="indefinite" values="0;0;1;1;0;0" keyTimes="0;0.44;0.46;0.7;0.75;1"/></text></g>')
    srv = "".join(node(900, y, 260, 48, t, s, CYAN) for y, t, s in servers)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Animated network topology: internet, WAF and IDS, core switch, Linux, Windows Server, VMware and AWS">
<defs><pattern id="gr" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="{CYAN}" stroke-opacity=".07"/></pattern>
<clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>
<style>.bl{{animation:bl 1.4s steps(1) infinite}}@keyframes bl{{50%{{opacity:.2}}}}
.w{{stroke-dasharray:5 7;animation:w 1s linear infinite}}@keyframes w{{to{{stroke-dashoffset:-12}}}}
.r{{transform-origin:90px {mid}px;animation:r 3s ease-out infinite}}@keyframes r{{from{{transform:scale(.6);opacity:.9}}to{{transform:scale(1.5);opacity:0}}}}
.sh{{animation:sh 4s steps(1) infinite}}@keyframes sh{{0%,44%{{stroke:{RED}}}46%,60%{{stroke:#fff}}62%,100%{{stroke:{RED}}}}}{REDUCED}</style>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="{BG}"/><rect width="{W}" height="{H}" fill="url(#gr)"/>
<text x="30" y="36" font-family="{MONO}" font-size="13" letter-spacing="4" fill="{CYAN}">NETWORK TOPOLOGY // LIVE</text>
<text x="{W-30}" y="36" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="3" fill="{DIM}">PACKET FLOW MONITOR</text>
<g fill="none" stroke="{CYAN}" stroke-opacity=".55" stroke-width="2" class="w"><path d="{p_in}"/><path d="{p_fw}"/>{paths}</g>
<!-- internet -->
<circle class="r" cx="90" cy="{mid}" r="46" fill="none" stroke="{MAG}" stroke-width="2"/>
<circle cx="90" cy="{mid}" r="46" fill="{BG2}" stroke="{MAG}" stroke-width="2"/>
<ellipse cx="90" cy="{mid}" rx="20" ry="46" fill="none" stroke="{MAG}" stroke-opacity=".6"/><line x1="44" y1="{mid}" x2="136" y2="{mid}" stroke="{MAG}" stroke-opacity=".6"/>
<path d="M50 {mid-22}Q90 {mid-12} 130 {mid-22}M50 {mid+22}Q90 {mid+12} 130 {mid+22}" fill="none" stroke="{MAG}" stroke-opacity=".6"/>
<text x="90" y="{mid+72}" text-anchor="middle" font-family="{MONO}" font-size="12" letter-spacing="3" fill="{MAG}">INTERNET</text>
<!-- waf -->
<rect class="sh" x="300" y="{mid-34}" width="200" height="68" rx="6" fill="{BG2}" stroke="{RED}" stroke-width="2.5"/>
<path d="M326 {mid-16}l14 -6l14 6v12c0 9 -6 15 -14 18c-8 -3 -14 -9 -14 -18z" fill="none" stroke="{RED}" stroke-width="2"/>
<text x="366" y="{mid-3}" font-family="{MONO}" font-size="14" font-weight="800" fill="#fff">WAF / IDS</text>
<text x="366" y="{mid+15}" font-family="{MONO}" font-size="10.5" fill="{RED}">ModSecurity + Snort</text>
<!-- core switch -->
<rect x="580" y="{mid-30}" width="120" height="60" rx="6" fill="{BG2}" stroke="{AMBER}" stroke-width="2"/>
<text x="640" y="{mid-4}" text-anchor="middle" font-family="{MONO}" font-size="14" font-weight="800" fill="#fff">CORE SW</text>
<g fill="{AMBER}">{"".join(f'<rect class="bl" style="animation-delay:{-k*0.23:.2f}s" x="{598 + k*12}" y="{mid+8}" width="7" height="7"/>' for k in range(8))}</g>
{srv}
{packets}{bad}
</g>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="none" stroke="{CYAN}" stroke-opacity=".45" stroke-width="1.5"/>
</svg>'''
    save("network.svg", svg)


# --------------------------------------------------------------------------- project cards
PROJECTS = [
    ("kanade-daw", "KANADE DAW", "AI 音楽生成・自動採譜を核にした統合 DAW。C++20 / JUCE 8、ローカル完結", "C++", CYAN),
    ("koe-loom", "KoeLoom", "Discord などで使える Windows 11 向けボイスチェンジャー。DSP のみ、JUCE / C++", "C++", MAG),
    ("rail-rampage", "RailRampage", "トロッコ問題を題材にした横スクロールの1ボタン破壊ゲーム（Godot 4）", "GDScript", ORANGE),
    ("packet-bouncer", "Packet Bouncer", "ブラウザで遊ぶパケット検問ゲーム（Godot 4・開発中）", "GDScript", GREEN),
    ("padlab", "PadLab", "Windows 向けゲームコントローラー診断ツール。入力の可視化・ドリフト・チャタリング・精度テスト", "C#", AMBER),
    ("net-diag", "net-diag", "自宅回線のボトルネックを推測ではなく実測で切り分けるネットワーク診断ツール", "Python", RED),
]


def card(i, repo, name, desc, lang, col):
    W, H = 590, 190
    per = 2 * (W + H) - 80
    dl = "".join(f'<text x="34" y="{112 + k * 22}" font-family="{GOTH}" font-size="14.5" fill="{TEXT}">{esc(l)}</text>'
                 for k, l in enumerate(wrap(desc, 35.5, 2)))
    lc = LANG_COLOR.get(lang, col)
    bars = "".join(f'<rect class="eq" style="animation-delay:{-k * 0.17:.2f}s" x="{W - 96 + k * 9}" y="150" width="5" height="18" fill="{col}"/>' for k in range(7))
    shape = f"M22 1.5H{W-1.5}V{H-22}L{W-22} {H-1.5}H1.5V22Z"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{esc(name)}: {esc(desc)}">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{col}" stop-opacity=".16"/><stop offset=".55" stop-color="{BG}" stop-opacity="0"/></linearGradient>
{hex_pattern("hex", 16, col, 0.07)}</defs>
<style>.t{{stroke-dasharray:140 {per - 140};animation:t 5s linear infinite}}@keyframes t{{to{{stroke-dashoffset:-{per}}}}}
.eq{{transform-box:fill-box;transform-origin:bottom;animation:eq 1.1s ease-in-out infinite alternate}}@keyframes eq{{from{{transform:scaleY(.2)}}to{{transform:scaleY(1)}}}}
.bl{{animation:bl 1.4s steps(1) infinite}}@keyframes bl{{50%{{opacity:.2}}}}{REDUCED}</style>
<path d="{shape}" fill="{BG}"/><path d="{shape}" fill="url(#hex)"/><path d="{shape}" fill="url(#g)"/>
<path d="{shape}" fill="none" stroke="{col}" stroke-opacity=".4" stroke-width="1.5"/>
<path class="t" d="{shape}" fill="none" stroke="{col}" stroke-width="3" stroke-linecap="round"/>
<text x="34" y="40" font-family="{MONO}" font-size="12" letter-spacing="3" fill="{col}">PRJ-{i:02d} // {esc(repo)}</text>
<circle class="bl" cx="{W-36}" cy="35" r="4" fill="{col}"/>
<text x="34" y="80" font-family="{MONO}" font-size="30" font-weight="800" fill="#fff">{esc(name)}</text>
{dl}
<circle cx="40" cy="162" r="5" fill="{lc}"/><text x="54" y="167" font-family="{MONO}" font-size="12.5" fill="{TEXT}">{esc(lang)}</text>
<text x="{W - 110}" y="167" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="2" fill="{DIM}">OPEN REPO &gt;</text>
{bars}
</svg>'''
    save(f"card-{repo}.svg", svg)


# --------------------------------------------------------------------------- footer
def footer():
    W, H = 1200, 170
    pts = []
    for x in range(0, 2401, 8):
        t = x / 2400 * math.tau
        y = 62 + 20 * math.sin(t * 6) + 12 * math.sin(t * 17 + 1) + 6 * math.sin(t * 31)
        pts.append(f"{x},{y:.1f}")
    wave = "M" + "L".join(pts)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="End of transmission">
<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath>
<pattern id="hz" width="28" height="28" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="14" height="28" fill="{ORANGE}"/></pattern>
<linearGradient id="f" x1="0" x2="1"><stop offset="0" stop-color="{BG}"/><stop offset=".12" stop-color="{BG}" stop-opacity="0"/><stop offset=".88" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>
<style>.w{{animation:w 9s linear infinite}}@keyframes w{{to{{transform:translateX(-1200px)}}}}
.w2{{animation:w 14s linear infinite reverse}}
.m{{animation:m 1.6s linear infinite}}@keyframes m{{to{{transform:translateX(39.6px)}}}}
.bl{{animation:bl 1.2s steps(1) infinite}}@keyframes bl{{50%{{opacity:.2}}}}{REDUCED}</style>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="{BG}"/>
<path class="w2" d="{wave}" fill="none" stroke="{MAG}" stroke-opacity=".5" stroke-width="1.5"/>
<path class="w" d="{wave}" fill="none" stroke="{CYAN}" stroke-width="2"/>
<rect width="{W}" height="120" fill="url(#f)"/>
<text x="600" y="126" text-anchor="middle" font-family="{MIN}" font-size="26" font-weight="900" letter-spacing="14" fill="#fff">通信終了</text>
<text x="600" y="146" text-anchor="middle" font-family="{MONO}" font-size="11" letter-spacing="6" fill="{DIM}">END OF TRANSMISSION // THANKS FOR VISITING</text>
<circle class="bl" cx="412" cy="118" r="4" fill="{RED}"/><circle class="bl" cx="788" cy="118" r="4" fill="{RED}"/>
<rect class="m" x="-60" y="158" width="1320" height="12" fill="url(#hz)"/>
</g></svg>'''
    save("footer.svg", svg)


if __name__ == "__main__":
    header()
    section("sec-01.svg", "01", "操作員", "OPERATOR", CYAN)
    section("sec-02.svg", "02", "技術領域", "SKILL DOMAINS", ORANGE)
    section("sec-03.svg", "03", "制作物", "PROJECTS", MAG)
    section("sec-04.svg", "04", "活動記録", "ACTIVITY LOG", GREEN)
    terminal()
    status()
    network()
    for i, p in enumerate(PROJECTS, 1):
        card(i, *p)
    footer()
