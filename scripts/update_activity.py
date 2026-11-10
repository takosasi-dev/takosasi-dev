#!/usr/bin/env python3
"""Regenerate assets/activity.svg from the most recently pushed public repos.

Run by .github/workflows/activity.yml on a schedule. Standard library only.
    python3 scripts/update_activity.py            # live (uses GITHUB_TOKEN if set)
    python3 scripts/update_activity.py data.json  # from a saved API response
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

USER = "takosasi-dev"
ROWS = 6
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "activity.svg")


def fetch():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            return json.load(f)
    req = urllib.request.Request(
        f"https://api.github.com/users/{USER}/repos?sort=pushed&per_page=30&type=owner",
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def build(repos):
    repos = [r for r in repos if not r.get("fork") and r["name"] != USER]
    repos.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
    repos = repos[:ROWS]
    W, RH, TOP = 1200, 54, 64
    H = TOP + RH * len(repos) + 18
    rows = ""
    for i, r in enumerate(repos):
        y = TOP + i * RH
        lang = r.get("language") or "-"
        lc = LANG_COLOR.get(lang, DIM)
        date = (r.get("pushed_at") or "")[:10]
        desc = wrap(r.get("description") or "(no description)", 46, 1)[0]
        name = r["name"] if len(r["name"]) <= 26 else r["name"][:25] + "…"
        rows += f'''<g class="row" style="animation-delay:{i * 0.18:.2f}s">
<rect x="20" y="{y}" width="{W - 40}" height="{RH - 8}" fill="{BG2}" stroke="{GREEN}" stroke-opacity=".22"/>
<rect x="20" y="{y}" width="5" height="{RH - 8}" fill="{GREEN}"/>
<text x="42" y="{y + 29}" font-family="{MONO}" font-size="13" fill="{GREEN}">{esc(date)}</text>
<text x="150" y="{y + 29}" font-family="{MONO}" font-size="15" font-weight="800" fill="#fff">{esc(name)}</text>
<circle cx="420" cy="{y + 24}" r="5" fill="{lc}"/>
<text x="434" y="{y + 29}" font-family="{MONO}" font-size="12" fill="{TEXT}">{esc(lang)}</text>
<text x="540" y="{y + 29}" font-family="{GOTH}" font-size="13.5" fill="{DIM}">{esc(desc)}</text>
</g>'''
    n = max(len(repos), 1)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Recently updated repositories">
<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath>
<linearGradient id="hl" x1="0" x2="1"><stop offset="0" stop-color="{GREEN}" stop-opacity=".0"/><stop offset=".5" stop-color="{GREEN}" stop-opacity=".16"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></linearGradient></defs>
<style>.row{{animation:row .5s ease-out both}}@keyframes row{{from{{opacity:0;transform:translateX(-14px)}}to{{opacity:1;transform:none}}}}
.hl{{animation:hl {n * 1.2:.1f}s steps({n},end) infinite}}@keyframes hl{{to{{transform:translateY({n * RH}px)}}}}
.bl{{animation:bl 1s steps(1) infinite}}@keyframes bl{{50%{{opacity:.2}}}}{REDUCED}</style>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="{BG}"/>
<circle class="bl" cx="32" cy="32" r="5" fill="{GREEN}"/>
<text x="48" y="37" font-family="{MONO}" font-size="13" letter-spacing="4" fill="{GREEN}">RECENT TRANSMISSIONS // LATEST PUSHES</text>
<text x="{W - 24}" y="37" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="3" fill="{DIM}">AUTO-UPDATED BY GITHUB ACTIONS</text>
{rows}
<rect class="hl" x="20" y="{TOP}" width="{W - 40}" height="{RH - 8}" fill="url(#hl)"/>
</g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="none" stroke="{GREEN}" stroke-opacity=".45" stroke-width="1.5"/>
</svg>'''
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print("wrote activity.svg rows:", len(repos))


if __name__ == "__main__":
    build(fetch())
