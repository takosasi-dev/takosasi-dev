#!/usr/bin/env python3
"""Rebuild everything in the profile that depends on live GitHub data.

    assets/guide.svg       lines (categories) with their repo counts, latest release in the ticker
    assets/card-*.svg      featured projects: the repos carrying the GitHub topic "featured"
    assets/arc-*.svg       the sign on top of each ARCHIVE group
    assets/stats.svg       repo / release / language counts
    assets/releases.svg    the six newest releases
    assets/contrib.svg     one year of contributions
    README.md              the card links and the ARCHIVE list, between their markers

Run by .github/workflows/activity.yml once a day. Standard library only.
    GITHUB_TOKEN=... python3 scripts/update_live.py   # live (GraphQL needs a token)
    python3 scripts/update_live.py data.json          # from a saved GraphQL response
"""
import base64
import bisect
import datetime
import glob
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

USER = "takosasi-dev"
README = os.path.join(ROOT, "README.md")
NOTE = "GitHub の記録から毎日自動で更新"

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
    contributionsCollection {
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
  }
}"""


def fetch():
    """(public repos, most recently pushed first; the contribution calendar)."""
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
    user = data["data"]["user"]
    repos = []
    for n in user["repositories"]["nodes"]:
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
    return repos, user["contributionsCollection"]["contributionCalendar"]


def md(date):
    return f"{date[5:7]}/{date[8:10]}"


# --------------------------------------------------------------------------- categories
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
# In display order. title: (file slug, tag on a board, name, line symbol, line colour, LED colour)
CAT = {
    "GAMES": ("games", "ゲーム", "ゲーム", "G", "#f39700", AMBER),
    "APPS": ("apps", "アプリ", "アプリ", "A", "#e5404f", GREEN),
    "DIAGNOSTICS": ("diag", "診断", "診断ツール", "D", "#00a7db", RED),
    "LINUX / SERVER": ("linux", "サーバ", "Linux・サーバ", "L", "#00a650", GREEN),
    "OBSIDIAN": ("obsidian", "Obsidian", "Obsidian", "O", "#9b7cb6", AMBER),
    "CHROME EXTENSIONS": ("chrome", "Chrome", "Chrome 拡張", "C", "#009bbf", GREEN),
    "MINECRAFT ADD-ONS": ("minecraft", "アドオン", "Minecraft", "M", "#bb641d", AMBER),
    "CLAUDE CODE MODS": ("claude", "CC mod", "Claude Code", "K", "#c99a00", RED),
}

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


# --------------------------------------------------------------------------- project cards
# The cards are the repos with the GitHub topic "featured" (six at most). This table only makes
# them prettier: repo -> (display name, tag, description broken by hand at "\n", about 21
# full-width characters a line). A featured repo that is not here uses its GitHub name and description.
PROJECTS = {
    "kanade-daw": ("KANADE DAW", "音楽", "AI 音楽生成・自動採譜を核にした統合 DAW。\nC++20 / JUCE 8、ローカル完結"),
    "koe-loom": ("KoeLoom", "音声", "Discord などで使える Windows 11 向け\nボイスチェンジャー。DSP のみ、JUCE / C++"),
    "rail-rampage": ("RailRampage", None, "トロッコ問題を題材にした横スクロールの\n1ボタン破壊ゲーム（Godot 4）"),
    "packet-bouncer": ("Packet Bouncer", None, "ブラウザで遊ぶパケット検問ゲーム\n（Godot 4・開発中）"),
    "padlab": ("PadLab", None, "Windows 向けゲームコントローラー診断ツール\n入力表示・ドリフト・チャタリング・精度"),
    "net-diag": ("net-diag", None, "自宅回線のボトルネックを推測ではなく\n実測で切り分けるネットワーク診断ツール"),
}


def featured(repos):
    order = list(PROJECTS)
    picked = [r for r in repos if "featured" in r["topics"]] or [r for r in repos if r["name"] in PROJECTS]
    picked.sort(key=lambda r: order.index(r["name"]) if r["name"] in order else len(order))  # stable: the rest stay newest first
    return picked[:6]


def poster(repo, name, col):
    """The picture on a card: assets/posters/<repo>.jpg (made with make_poster.py), or a plain name plate."""
    path = os.path.join(ROOT, "assets", "posters", repo + ".jpg")
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
        img = f'<image x="8" y="8" width="396" height="178" preserveAspectRatio="xMidYMid slice" href="data:image/jpeg;base64,{data}"/>'
    else:
        img = (f'<rect x="8" y="8" width="396" height="178" fill="#181b22"/><path d="M8 152L404 104V186H8Z" fill="{col}"/>'
               f'<path d="M8 146L404 98" stroke="{col}" stroke-width="2" opacity=".5"/>'
               f'<text x="28" y="74" font-family="{MONO}" font-size="34" font-weight="800" fill="#f2f2ee">{esc(name)}</text>'
               f'<text x="30" y="98" font-family="{MONO}" font-size="11.5" fill="#aab0b8" letter-spacing="1">{USER} / {esc(repo)}</text>')
    return (f'<clipPath id="p"><rect x="8" y="8" width="396" height="178" rx="3"/></clipPath><g clip-path="url(#p)">{img}</g>'
            f'<rect x="8" y="8" width="396" height="178" rx="3" fill="none" stroke="#000" opacity=".5"/>')


def card(i, r, cat):
    # Drawn at its natural size (no width in README): two fit side by side on a desktop
    # profile (846px) and they drop to one column on a phone.
    repo, lang = r["name"], "" if r["lang"] == "-" else r["lang"]
    name, kind, desc = PROJECTS.get(repo, (repo, None, None))
    _, tag, _, _, col, led = CAT[cat]
    lines = desc.split("\n") if desc else F12.wrap(DESC.get(repo) or r["desc"], 246)
    a = Board("a", 8, 208, 198, 20)
    w = a.put(F16, kind or tag, 3, 2, led, invert=True)
    a.put(F16, F16.fit(name, 186 - w), 9 + w, 2, AMBER)
    b = Board("b", 8, 250, 264, 39, 1.5)
    for k, ln in enumerate(lines[:2]):
        b.put(F12, F12.fit(ln, 258), 3, 1 + k * 13, GREEN)
    if r["tag"]:
        info = f'{r["tag"]}　{md(r["tag_date"])} 発　{lang}'
        b.put(F12, "公開中", 261, 27, GREEN, right=True)
    else:
        info = f"リリース準備中　{lang}"
        b.put(F12, "開発中", 261, 27, RED, blink=True, right=True)
    b.put(F12, F12.fit(info.strip(), 214), 3, 27, AMBER)
    body = (f'<rect x=".5" y=".5" width="411" height="316" rx="8" fill="{BODY}" stroke="{EDGE}"/>' + poster(repo, name, col)
            + f'<g font-family="{GOTH}" font-size="10" fill="#aab0b8"><text x="14" y="200">種別</text><text x="70" y="200">名前</text>'
              f'<text x="400" y="200" text-anchor="end" font-family="{MONO}">{i:02d} // {esc(repo)}</text></g>'
            + a.svg() + b.svg())
    save(f"card-{repo}.svg", 412, 317, body, f"{name}: {' '.join(lines)}")


# --------------------------------------------------------------------------- boards
def guide(repos, groups):
    b = Board("g", LED_X, 40, LED_COLS, 98)
    for i, title in enumerate(CAT):
        x, y = 5 + (i % 2) * 201, 3 + (i // 2) * 18
        b.put(F16, CAT[title][2], x, y, AMBER)
        b.put(F16, f"{len(groups[title])}本", x + 190, y, GREEN, right=True)
    news = [r for r in repos if r["tag_date"]]
    tick = ""
    if news:
        n = max(news, key=lambda r: r["tag_date"])
        tick = f'最新リリース: {n["name"]} {n["tag"]}（{md(n["tag_date"])}）　　'
    tick += "最近の更新: " + "、".join(r["name"] for r in repos[:5]) + "　　　"
    b.ticker(F16, tick, 80, AMBER)
    counts = "、".join(f"{CAT[t][2]} {len(groups[t])}" for t in CAT)
    save("guide.svg", W, 256, casing(W, 256, "系統のご案内", "Lines", NOTE) + b.svg() + seam(b, 76),
         f"公開リポジトリ {len(repos)} 本。{counts}。{tick.strip()}")


def stats(repos):
    langs = {}
    for r in repos:
        if r["lang"] != "-":
            langs[r["lang"]] = langs.get(r["lang"], 0) + 1
    order = sorted(langs.items(), key=lambda kv: (-kv[1], kv[0]))
    if len(order) > 9:
        order = order[:8] + [("ほか", sum(v for _, v in order[8:]))]
    total = sum(v for _, v in order) or 1
    counters = [(len(repos), "リポジトリ"), (sum(r["releases"] for r in repos), "リリース"), (len(langs), "言語")]
    rows = -(-len(order) // 3)
    b = Board("s", LED_X, 40, LED_COLS, 60 + rows * 18)
    for i, (v, label) in enumerate(counters):
        w = b.put(F16, str(v), 6 + i * 134, 4, AMBER, scale=2)
        b.put(F16, label, 10 + i * 134 + w, 20, GREEN)
    x = 6
    for i, (lang, v) in enumerate(order):
        col = LANG_COLOR.get(lang, "#aab0b8")
        w = 390 - (x - 6) if i == len(order) - 1 else round(390 * v / total)
        b.bar(x, 42, max(w - 1, 1), 10, col)
        x += w
        b.put(F16, F16.fit(f"{lang} {v}", 126), 6 + (i % 3) * 132, 58 + (i // 3) * 18, col)
    h = 40 + b.h + 17
    save("stats.svg", W, h, casing(W, h, "運行状況", "Status", NOTE) + b.svg() + seam(b, 38),
         f"公開リポジトリ {counters[0][0]}、リリース {counters[1][0]}、言語 {counters[2][0]} 種。"
         + "、".join(f"{lang} {v}" for lang, v in order))


def releases(repos, cat_of):
    rel = sorted((r for r in repos if r["tag_date"]), key=lambda r: r["tag_date"], reverse=True)[:6]
    b = Board("r", LED_X, 58, LED_COLS, 4 + 20 * len(rel))
    for i, r in enumerate(rel):
        y = 4 + i * 20
        b.put(F16, md(r["tag_date"]), 5, y, GREEN)
        w = b.put(F16, CAT[cat_of[r["name"]]][1], 54, y, CAT[cat_of[r["name"]]][5], invert=True)
        tw = b.put(F16, F16.fit(r["tag"], 80), 397, y, GREEN, right=True)
        b.put(F16, F16.fit(r["name"], 397 - tw - 8 - (60 + w)), 60 + w, y, AMBER)
    h = 58 + b.h + 17
    heads = (f'<g font-family="{GOTH}" font-size="10.5" fill="#aab0b8"><text x="31" y="50">日付</text><text x="129" y="50">種別</text>'
             f'<text x="275" y="50">名前</text><text x="815" y="50" text-anchor="end">版</text></g>')
    save("releases.svg", W, h, casing(W, h, "新着リリース", "New releases", NOTE) + heads + b.svg(),
         "新着リリース。" + "、".join(f'{md(r["tag_date"])} {r["name"]} {r["tag"]}' for r in rel))


def contrib(cal):
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    counts = [d["contributionCount"] for d in days]
    best = run = cur = 0
    for c in counts:
        run = run + 1 if c else 0
        best = max(best, run)
    for c in reversed(counts[:-1] if counts and not counts[-1] else counts):  # today may still be empty
        if not c:
            break
        cur += 1
    text = f"過去1年 {cal['totalContributions']:,}回　連続 {cur}日　最長 {best}日"
    t = Board("c", LED_X, 40, LED_COLS, 20)
    t.put(F16, F16.fit(text, 392), 5, 2, AMBER)
    weeks = cal["weeks"][-53:]
    h = Board("d", (W - 53 * 14) // 2, 92, 53, 7, 14)
    lit = sorted(c for c in counts if c)
    for level, op in enumerate((.3, .55, .8, 1)):  # quartiles of the days that have anything
        rows = [[0] * 53 for _ in range(7)]
        for x, w in enumerate(weeks):
            for d in w["contributionDays"]:
                c = d["contributionCount"]
                if c and min(3, bisect.bisect_left(lit, c) * 4 // len(lit)) == level:
                    rows[datetime.date.fromisoformat(d["date"]).isoweekday() % 7][x] = 1
        h.raw(rows, 0, 0, GREEN, op=op)
    save("contrib.svg", W, 208, casing(W, 208, "稼働記録", "Contributions", NOTE) + t.svg() + h.svg(), text)


def strip(title, n):
    """The sign on top of one ARCHIVE group: the line symbol with the repo count, like a station number."""
    slug, _, ja, sym, col, _ = CAT[title]
    body = (f'<g font-family="{GOTH}"><rect x="1" y="1" width="418" height="44" rx="6" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="1.5"/>'
            f'<circle cx="25" cy="23" r="16" fill="#fff" stroke="{col}" stroke-width="5"/>'
            f'<text x="25" y="21" text-anchor="middle" font-size="12" font-weight="800" fill="#111">{sym}</text>'
            f'<text x="25" y="33" text-anchor="middle" font-size="11" font-weight="800" fill="#111">{n:02d}</text>'
            f'<text x="54" y="30" font-size="19" font-weight="700" fill="#111">{ja}</text>'
            f'<text x="406" y="29" text-anchor="end" font-size="11" fill="#666" font-family="{MONO}" letter-spacing="1.5">{title}</text></g>')
    save(f"arc-{slug}.svg", 420, 46, body, f"{ja} {n} 本")


# --------------------------------------------------------------------------- README.md
def splice(text, tag, body):
    a, b = f"<!-- {tag}:START -->", f"<!-- {tag}:END -->"
    return text[:text.index(a) + len(a)] + "\n" + body + "\n" + text[text.index(b):]


def cards_md(feat):
    return "\n".join(f'<a href="https://github.com/{USER}/{r["name"]}"><img src="assets/card-{r["name"]}.svg" '
                     f'alt="{esc(PROJECTS.get(r["name"], (r["name"],))[0])}"></a>' for r in feat)


def archive_md(groups):
    out = [""]
    for title, rows in groups.items():
        if not rows:
            continue
        slug, _, ja, *_ = CAT[title]
        out.append(f'<details>\n<summary><img src="assets/arc-{slug}.svg" height="40" align="middle" alt="{ja} / {title} ({len(rows)})"></summary>\n<br>\n\n'
                   "| Repo | 内容 | Lang | Release |\n|---|---|---|---|")
        for r in rows:
            desc = (DESC.get(r["name"]) or r["desc"] or "-").replace("|", "\\|")
            out.append(f"| [{r['name']}](https://github.com/{USER}/{r['name']}) | {desc} | {r['lang']} | {r['tag'] or '-'} |")
        out.append("\n</details>\n")
    return "\n".join(out)


def check(repos):
    """Stop the run (and so the commit) if README would point at something that is not there."""
    with open(README, encoding="utf-8") as f:
        text = f.read()
    files = set(re.findall(r'(?:src|srcset)="(assets/[^"]+)"', text))
    missing = sorted(p for p in files if not os.path.exists(os.path.join(ROOT, p)))
    unlisted = sorted(r["name"] for r in repos if f"(https://github.com/{USER}/{r['name']})" not in text)
    if missing or unlisted:
        sys.exit(f"check failed: missing files {missing}, repos not listed {unlisted}")
    print("check ok:", len(files), "asset files,", len(repos), "repos listed")


if __name__ == "__main__":
    repos, cal = fetch()
    cat_of = {r["name"]: next(title for title, test in CATS if test(r)) for r in repos}
    groups = {title: sorted((r for r in repos if cat_of[r["name"]] == title), key=lambda r: r["name"].strip("-").lower())
              for title in CAT}
    feat = featured(repos)
    for old in glob.glob(os.path.join(ROOT, "assets", "card-*.svg")):  # cards of repos that are no longer featured
        os.remove(old)
    for i, r in enumerate(feat, 1):
        card(i, r, cat_of[r["name"]])
    for title in CAT:
        strip(title, len(groups[title]))
    guide(repos, groups)
    stats(repos)
    releases(repos, cat_of)
    contrib(cal)
    with open(README, encoding="utf-8", newline="") as f:
        text = f.read()
    text = splice(splice(text, "CARDS", cards_md(feat)), "ARCHIVE", archive_md(groups))
    with open(README, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    check(repos)
