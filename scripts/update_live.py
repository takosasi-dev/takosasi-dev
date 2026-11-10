#!/usr/bin/env python3
"""Rebuild everything in the profile that depends on live GitHub data.

    assets/activity.svg, assets/stats.svg   (+ m-*.svg, the phone variants)
    assets/card-*.svg                       featured projects: language, latest release
    README.md                               the ARCHIVE list between the ARCHIVE markers

Run by .github/workflows/activity.yml once a day. Standard library only.
    GITHUB_TOKEN=... python3 scripts/update_live.py   # live (GraphQL needs a token)
    python3 scripts/update_live.py data.json          # from a saved GraphQL response
"""
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

USER = "takosasi-dev"
ROOT = os.path.join(os.path.dirname(__file__), "..")
README = os.path.join(ROOT, "README.md")
START, END = "<!-- ARCHIVE:START -->", "<!-- ARCHIVE:END -->"

# ponytail: one page of 100 repos, no cursor paging. Add paging when the account passes 100 public repos.
QUERY = """query($login: String!) {
  user(login: $login) {
    repositories(first: 100, privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name description pushedAt
        primaryLanguage { name }
        repositoryTopics(first: 20) { nodes { topic { name } } }
        releases(first: 1, orderBy: {field: CREATED_AT, direction: DESC}) {
          totalCount
          nodes { tagName publishedAt }
        }
      }
    }
  }
}"""


def fetch():
    """Public repos, most recently pushed first."""
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            data = json.load(f)
    else:
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
            headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "User-Agent": USER})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    if data.get("errors"):
        sys.exit(f"GraphQL error: {data['errors']}")
    repos = []
    for n in data["data"]["user"]["repositories"]["nodes"]:
        if n["name"] == USER:
            continue
        last = (n["releases"]["nodes"] or [{}])[0]
        repos.append({
            "name": n["name"],
            "desc": (n["description"] or "").strip(),
            "pushed": (n["pushedAt"] or "")[:10],
            "lang": (n["primaryLanguage"] or {}).get("name") or "-",
            "topics": {t["topic"]["name"] for t in n["repositoryTopics"]["nodes"]},
            "releases": n["releases"]["totalCount"],
            "tag": last.get("tagName") or "",
            "tag_date": (last.get("publishedAt") or "")[:10],
        })
    return repos


def save(name, svg):
    with open(os.path.join(ROOT, "assets", name), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print("wrote", name, len(svg))


# --------------------------------------------------------------------------- activity panel
def activity(repos, mobile=False):
    repos = repos[:6]
    W, RH, TOP = (600, 86, 60) if mobile else (1200, 54, 64)
    H = TOP + RH * len(repos) + 18
    rows = ""
    for i, r in enumerate(repos):
        y = TOP + i * RH
        lc = LANG_COLOR.get(r["lang"], DIM)
        name = r["name"] if len(r["name"]) <= 26 else r["name"][:25] + "…"
        desc = DESC.get(r["name"]) or r["desc"] or "(no description)"
        if mobile:
            cells = f'''<text x="42" y="{y + 31}" font-family="{MONO}" font-size="19" font-weight="800" fill="#fff">{esc(name)}</text>
<text x="{W - 38}" y="{y + 31}" text-anchor="end" font-family="{MONO}" font-size="13" fill="{GREEN}">{esc(r["pushed"])}</text>
<circle cx="47" cy="{y + 54}" r="5" fill="{lc}"/>
<text x="60" y="{y + 59}" font-family="{MONO}" font-size="13" fill="{TEXT}">{esc(r["lang"])}</text>
<text x="160" y="{y + 59}" font-family="{GOTH}" font-size="14" fill="{DIM}">{esc(wrap(desc, 27, 1)[0])}</text>'''
        else:
            cells = f'''<text x="42" y="{y + 29}" font-family="{MONO}" font-size="13" fill="{GREEN}">{esc(r["pushed"])}</text>
<text x="150" y="{y + 29}" font-family="{MONO}" font-size="15" font-weight="800" fill="#fff">{esc(name)}</text>
<circle cx="420" cy="{y + 24}" r="5" fill="{lc}"/>
<text x="434" y="{y + 29}" font-family="{MONO}" font-size="12" fill="{TEXT}">{esc(r["lang"])}</text>
<text x="540" y="{y + 29}" font-family="{GOTH}" font-size="13.5" fill="{DIM}">{esc(wrap(desc, 46, 1)[0])}</text>'''
        rows += f'''<g class="row" style="animation-delay:{i * 0.18:.2f}s">
<rect x="20" y="{y}" width="{W - 40}" height="{RH - 8}" fill="{BG2}" stroke="{GREEN}" stroke-opacity=".22"/>
<rect x="20" y="{y}" width="5" height="{RH - 8}" fill="{GREEN}"/>
{cells}
</g>'''
    n = max(len(repos), 1)
    if mobile:
        title = f'<text x="48" y="37" font-family="{MONO}" font-size="15" letter-spacing="4" fill="{GREEN}">RECENT TRANSMISSIONS</text>'
    else:
        title = (f'<text x="48" y="37" font-family="{MONO}" font-size="13" letter-spacing="4" fill="{GREEN}">RECENT TRANSMISSIONS // LATEST PUSHES</text>'
                 f'<text x="{W - 24}" y="37" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="3" fill="{DIM}">AUTO-UPDATED BY GITHUB ACTIONS</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Recently updated repositories">
<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath>
<linearGradient id="hl" x1="0" x2="1"><stop offset="0" stop-color="{GREEN}" stop-opacity=".0"/><stop offset=".5" stop-color="{GREEN}" stop-opacity=".16"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></linearGradient></defs>
<style>.row{{animation:row .5s ease-out both}}@keyframes row{{from{{opacity:0;transform:translateX(-14px)}}to{{opacity:1;transform:none}}}}
.hl{{animation:hl {n * 1.2:.1f}s steps({n},end) infinite}}@keyframes hl{{to{{transform:translateY({n * RH}px)}}}}
.bl{{animation:bl 1s steps(1) infinite}}@keyframes bl{{50%{{opacity:.2}}}}{REDUCED}</style>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="{BG}"/>
<circle class="bl" cx="32" cy="32" r="5" fill="{GREEN}"/>
{title}
{rows}
<rect class="hl" x="20" y="{TOP}" width="{W - 40}" height="{RH - 8}" fill="url(#hl)"/>
</g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="none" stroke="{GREEN}" stroke-opacity=".45" stroke-width="1.5"/>
</svg>'''
    save("m-activity.svg" if mobile else "activity.svg", svg)


# --------------------------------------------------------------------------- stats panel
def stats(repos, mobile=False):
    langs = {}
    for r in repos:
        if r["lang"] != "-":
            langs[r["lang"]] = langs.get(r["lang"], 0) + 1
    order = sorted(langs.items(), key=lambda kv: (-kv[1], kv[0]))
    if len(order) > 8:
        order = order[:7] + [("other", sum(v for _, v in order[7:]))]
    total = sum(v for _, v in order) or 1
    newest = max((r for r in repos if r["tag_date"]), key=lambda r: r["tag_date"], default=None)
    counters = [(len(repos), "PUBLIC REPOS"), (sum(r["releases"] for r in repos), "RELEASES"), (len(langs), "LANGUAGES")]
    if mobile:
        W, H, cx0, cdx, nf, ny, lf = 600, 334, 30, 190, 54, 106, 12.5
        ry, rf, bx, bw, by, cols, ldx, gf = 166, 14, 30, 540, 210, 3, 185, 14
    else:
        W, H, cx0, cdx, nf, ny, lf = 1200, 214, 40, 200, 64, 122, 12
        ry, rf, bx, bw, by, cols, ldx, gf = 186, 13, 660, 500, 92, 4, 125, 13
    nums = "".join(
        f'<text x="{cx0 + i * cdx}" y="{ny}" font-family="{MONO}" font-size="{nf}" font-weight="800" fill="#fff">{v}</text>'
        f'<text x="{cx0 + i * cdx + 2}" y="{ny + 24}" font-family="{MONO}" font-size="{lf}" letter-spacing="3" fill="{AMBER}">{label}</text>'
        for i, (v, label) in enumerate(counters))
    latest = ""
    if newest:
        latest = (f'<text x="{cx0 + 2}" y="{ry}" font-family="{MONO}" font-size="{rf}" fill="{DIM}" xml:space="preserve">LATEST RELEASE  '
                  f'<tspan fill="#fff" font-weight="800">{esc(newest["name"])} {esc(newest["tag"])}</tspan>  {esc(newest["tag_date"])}</text>')
    segs, legend, x = "", "", float(bx)
    for i, (lang, v) in enumerate(order):
        col = LANG_COLOR.get(lang, DIM)
        w = bw * v / total
        segs += f'<rect x="{x:.1f}" y="{by}" width="{max(w - 2, 1):.1f}" height="18" fill="{col}"/>'
        x += w
        lx, ly = bx + (i % cols) * ldx, by + 48 + (i // cols) * 26
        legend += (f'<circle cx="{lx + 5}" cy="{ly - 5}" r="5" fill="{col}"/>'
                   f'<text x="{lx + 17}" y="{ly}" font-family="{MONO}" font-size="{gf}" fill="{TEXT}">{esc(lang)} <tspan fill="#fff" font-weight="800">{v}</tspan></text>')
    if mobile:
        title = f'<text x="48" y="37" font-family="{MONO}" font-size="15" letter-spacing="4" fill="{AMBER}">FLEET STATUS</text>'
    else:
        title = (f'<text x="48" y="37" font-family="{MONO}" font-size="13" letter-spacing="4" fill="{AMBER}">FLEET STATUS // PUBLIC REPOSITORIES</text>'
                 f'<text x="{W - 24}" y="37" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="3" fill="{DIM}">AUTO-UPDATED BY GITHUB ACTIONS</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{counters[0][0]} public repositories, {counters[1][0]} releases, {counters[2][0]} languages">
<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath>{hex_pattern("hex", 22, AMBER, 0.06)}</defs>
<style>.g{{transform-origin:{bx}px 0;animation:g 1.8s cubic-bezier(.2,.8,.2,1) both}}@keyframes g{{from{{transform:scaleX(0)}}}}
.bl{{animation:bl 1s steps(1) infinite}}@keyframes bl{{50%{{opacity:.2}}}}{REDUCED}</style>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="{BG}"/><rect width="{W}" height="{H}" fill="url(#hex)"/>
<circle class="bl" cx="32" cy="32" r="5" fill="{AMBER}"/>
{title}
{nums}
{latest}
<text x="{bx}" y="{by - 14}" font-family="{MONO}" font-size="{lf}" letter-spacing="3" fill="{AMBER}">LANGUAGES // BY REPOSITORY</text>
<rect x="{bx}" y="{by}" width="{bw}" height="18" fill="{AMBER}" fill-opacity=".12"/>
<g class="g">{segs}</g>
{legend}
</g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="none" stroke="{AMBER}" stroke-opacity=".45" stroke-width="1.5"/>
</svg>'''
    save("m-stats.svg" if mobile else "stats.svg", svg)


# --------------------------------------------------------------------------- project cards
# (repo, display name, hand-written description, color). Language and release come from the API.
# The description is two lines at most, broken by hand at "\n" (about 28 full-width characters a line).
PROJECTS = [
    ("kanade-daw", "KANADE DAW", "AI 音楽生成・自動採譜を核にした統合 DAW。\nC++20 / JUCE 8、ローカル完結", CYAN),
    ("koe-loom", "KoeLoom", "Discord などで使える Windows 11 向け\nボイスチェンジャー。DSP のみ、JUCE / C++", MAG),
    ("rail-rampage", "RailRampage", "トロッコ問題を題材にした横スクロールの\n1ボタン破壊ゲーム（Godot 4）", ORANGE),
    ("packet-bouncer", "Packet Bouncer", "ブラウザで遊ぶパケット検問ゲーム（Godot 4・開発中）", GREEN),
    ("padlab", "PadLab", "Windows 向けゲームコントローラー診断ツール。\n入力の可視化・ドリフト・チャタリング・精度テスト", AMBER),
    ("net-diag", "net-diag", "自宅回線のボトルネックを推測ではなく\n実測で切り分けるネットワーク診断ツール", RED),
]


def card(i, repo, name, desc, col, info):
    # Drawn at its natural size (no width in README): two fit side by side on a desktop
    # profile (846px) and they drop to one column on a phone, so the text stays readable.
    W, H = 412, 150
    per = 2 * (W + H) - 60
    lang, tag, date = info.get("lang", "-"), info.get("tag", ""), info.get("tag_date", "")
    dl = "".join(f'<text x="24" y="{84 + k * 18}" font-family="{GOTH}" font-size="12.5" fill="{TEXT}">{esc(l)}</text>'
                 for k, l in enumerate(desc.split("\n")))
    desc = desc.replace("\n", " ")
    lc = LANG_COLOR.get(lang, col)
    rel = ""
    if tag:
        px = 40 + len(lang) * 7 + 12
        pw = len(tag) * 6.5 + 14
        rel = (f'<rect x="{px}" y="119" width="{pw:.0f}" height="18" fill="none" stroke="{col}" stroke-opacity=".7"/>'
               f'<text x="{px + pw / 2:.0f}" y="132" text-anchor="middle" font-family="{MONO}" font-size="10.5" fill="{col}">{esc(tag)}</text>'
               f'<text x="{px + pw + 8:.0f}" y="132" font-family="{MONO}" font-size="10.5" fill="{DIM}">{esc(date)}</text>')
    bars = "".join(f'<rect class="eq" style="animation-delay:{-k * 0.17:.2f}s" x="{W - 76 + k * 8}" y="120" width="4.5" height="16" fill="{col}"/>' for k in range(7))
    shape = f"M16 1.5H{W-1.5}V{H-16}L{W-16} {H-1.5}H1.5V16Z"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(name)}: {esc(desc)}">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{col}" stop-opacity=".16"/><stop offset=".55" stop-color="{BG}" stop-opacity="0"/></linearGradient>
{hex_pattern("hex", 14, col, 0.07)}</defs>
<style>.t{{stroke-dasharray:110 {per - 110};animation:t 5s linear infinite}}@keyframes t{{to{{stroke-dashoffset:-{per}}}}}
.eq{{transform-box:fill-box;transform-origin:bottom;animation:eq 1.1s ease-in-out infinite alternate}}@keyframes eq{{from{{transform:scaleY(.2)}}to{{transform:scaleY(1)}}}}
.bl{{animation:bl 1.4s steps(1) infinite}}@keyframes bl{{50%{{opacity:.2}}}}{REDUCED}</style>
<path d="{shape}" fill="{BG}"/><path d="{shape}" fill="url(#hex)"/><path d="{shape}" fill="url(#g)"/>
<path d="{shape}" fill="none" stroke="{col}" stroke-opacity=".4" stroke-width="1.5"/>
<path class="t" d="{shape}" fill="none" stroke="{col}" stroke-width="2.5" stroke-linecap="round"/>
<text x="24" y="28" font-family="{MONO}" font-size="10.5" letter-spacing="2.5" fill="{col}">PRJ-{i:02d} // {esc(repo)}</text>
<circle class="bl" cx="{W-26}" cy="24" r="3.5" fill="{col}"/>
<text x="24" y="60" font-family="{MONO}" font-size="23" font-weight="800" fill="#fff">{esc(name)}</text>
{dl}
<circle cx="29" cy="128" r="4.5" fill="{lc}"/><text x="40" y="132" font-family="{MONO}" font-size="11.5" fill="{TEXT}">{esc(lang)}</text>
{rel}
{bars}
</svg>'''
    save(f"card-{repo}.svg", svg)


# --------------------------------------------------------------------------- archive list in README.md
# Each repo goes to the first category whose test matches (by GitHub topics), so a new
# repo shows up without touching this file. Nothing matches -> APPS.
T = lambda *names: lambda r: bool(r["topics"] & set(names))  # noqa: E731
CATS = [
    ("MINECRAFT ADD-ONS", T("minecraft-addon", "minecraft-bedrock")),
    ("CLAUDE CODE MODS", T("claude-code-plugin")),
    ("CHROME EXTENSIONS", T("chrome-extension")),
    ("OBSIDIAN", T("obsidian", "obsidian-plugin", "obsidian-md")),
    ("GAMES", lambda r: bool(r["topics"] & {"game", "game-tool", "roguelike", "godot"}) or r["lang"] == "GDScript"),
    ("DIAGNOSTICS", T("diagnostics", "controller-tester")),
    ("LINUX / SERVER", T("linux", "tmux")),
    ("APPS", lambda r: True),
]
ORDER = ["GAMES", "APPS", "DIAGNOSTICS", "LINUX / SERVER", "OBSIDIAN", "CHROME EXTENSIONS", "MINECRAFT ADD-ONS", "CLAUDE CODE MODS"]

# Japanese one-liners for repos whose GitHub description is English or empty.
DESC = {
    "-ai-work-board-": "各 AI との作業の進み具合を1枚の画面で見て書けるボード",
    "blocker-board": "仕様ノートの未記入プレースホルダと、止めているフェーズを一覧にする",
    "broken-name-watch": "見えない文字や Windows で使えない文字を含む名前を警告する",
    "diag-cron": "診断ツールを定期実行して結果を測定条件つきで残し、差分を取る",
    "diag-sheet": "診断ツールの結果 JSON を共通のシート形式に変換する",
    "discord-vc-check": "Discord の通話音声の不調を、マイク・スピーカー・回線・PC 負荷の区間ごとに切り分ける(非公式)",
    "handoff-board": "引き継ぎノートを古い順にサイドバーへ並べる",
    "log-stamp": "日ごとの開発ログに時刻つきの記録を足す",
    "note-shuttle": "選んだノートを秘密情報をマスクして1つにまとめ、コピーする",
    "pdf-pair": "元の Markdown より古い PDF を見つける",
    "placeholder-form": "仕様ノートの未記入プレースホルダをフォームで埋める(確認・バックアップ・取り消しつき)",
    "report-age": "調査ノートがいつ書かれたか、どれだけ古いか、調べ直しが要るかを表示する",
    "spec-lint": "開いている仕様ノートを、ルールノートの決まりと照らして点検する",
    "status-badge": "開いているノートの実装状況を、見出し部のバッジで表示する",
    "sync-guard": "同期や外部編集でノートが急に減ったときに警告する",
    "vault-doctor": "リンク切れ・孤立ノート・命名や配置ルール違反を見つける",
}


def archive(repos):
    groups = {title: [] for title in ORDER}
    for r in repos:
        groups[next(title for title, test in CATS if test(r))].append(r)
    out = []
    for i, title in enumerate(ORDER, 1):
        rows = sorted(groups[title], key=lambda r: r["name"].strip("-").lower())
        if not rows:
            continue
        out.append(f"<details>\n<summary><b>ARCHIVE {i:02d} // {title}</b> ({len(rows)})</summary>\n<br>\n\n"
                   "| Repo | 内容 | Lang | Release |\n|---|---|---|---|")
        for r in rows:
            desc = (DESC.get(r["name"]) or r["desc"] or "-").replace("|", "\\|")
            out.append(f"| [{r['name']}](https://github.com/{USER}/{r['name']}) | {desc} | {r['lang']} | {r['tag'] or '-'} |")
        out.append("\n</details>\n")
    with open(README, encoding="utf-8", newline="") as f:
        md = f.read()
    a, b = md.index(START) + len(START), md.index(END)
    md = md[:a] + "\n\n" + "\n".join(out) + "\n" + md[b:]
    with open(README, "w", encoding="utf-8", newline="") as f:
        f.write(md)
    print("wrote README archive:", len(repos), "repos")


def check(repos):
    """Stop the run (and so the commit) if README would point at something that is not there."""
    with open(README, encoding="utf-8") as f:
        md = f.read()
    files = set(re.findall(r'(?:src|srcset)="(?:https://raw\.githubusercontent\.com/[^/]+/[^/]+/main/)?(assets/[^"]+)"', md))
    missing = sorted(p for p in files if not os.path.exists(os.path.join(ROOT, p)))
    unlisted = sorted(r["name"] for r in repos if f"(https://github.com/{USER}/{r['name']})" not in md)
    if missing or unlisted:
        sys.exit(f"check failed: missing files {missing}, repos not listed {unlisted}")
    print("check ok:", len(files), "asset files,", len(repos), "repos listed")


if __name__ == "__main__":
    repos = fetch()
    by_name = {r["name"]: r for r in repos}
    activity(repos)
    activity(repos, mobile=True)
    stats(repos)
    stats(repos, mobile=True)
    for i, (repo, name, desc, col) in enumerate(PROJECTS, 1):
        card(i, repo, name, desc, col, by_name.get(repo, {}))
    archive(repos)
    check(repos)
