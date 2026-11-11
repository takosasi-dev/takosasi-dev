#!/usr/bin/env python3
"""Rebuild everything in the profile that depends on live GitHub data.

    assets/header.svg      the departure board: status from the real activity, notices and season from the date
    assets/guide.svg       lines (categories) with their repo counts, latest release in the ticker
    assets/card-*.svg      featured projects: the repos carrying the GitHub topic "featured"
    assets/arc-*.svg       the sign on top of each ARCHIVE group
    assets/stats.svg       repo / release / language counts
    assets/releases.svg    the six newest releases
    assets/contrib.svg     one year of contributions
    assets/fortune.svg     the fortune of the day in the waiting room
    README.md              the card links, the ARCHIVE list and today's pick, between their markers

Run by .github/workflows/activity.yml once a day. Standard library only.
    GITHUB_TOKEN=... python3 scripts/update_live.py   # live (GraphQL needs a token)
    python3 scripts/update_live.py data.json          # from a saved GraphQL response
"""
import base64
import bisect
import datetime
import glob
import importlib
import importlib.util
import json
import os
import random
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

USER = "takosasi-dev"
README = os.path.join(ROOT, "README.md")
# Optional modules in scripts/. Each may define static() (called by build_assets.py) and
# live(ctx) -> {MARKER: text}; the text replaces what is between <!-- MARKER:START --> and <!-- MARKER:END --> in README.
EXTENSIONS = ["ext_train", "ext_tako", "ext_data", "ext_games"]
NOTE = "GitHub の記録から毎日自動で更新"

# ponytail: one page of 100 repos, no cursor paging. Add paging when the account passes 100 public repos.
QUERY = """query($login: String!) {
  user(login: $login) {
    repositories(first: 100, privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name description pushedAt createdAt
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
            "created": (n.get("createdAt") or "")[:10],
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


def poster(repo, name, col, kind):
    """The picture on a card: assets/posters/<repo>.jpg (made with make_poster.py), or a destination roll sign."""
    path = os.path.join(ROOT, "assets", "posters", repo + ".jpg")
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
        img = f'<image x="8" y="8" width="396" height="178" preserveAspectRatio="xMidYMid slice" href="data:image/jpeg;base64,{data}"/>'
    else:
        # No screenshot yet: the navy roll sign of an old train, with the kind where the train type goes.
        size = min(50, 560 / max(len(name), 1))
        kw = max(len(kind) * 20, 40) + 28
        img = (f'<rect x="8" y="8" width="396" height="178" fill="#15223f"/>'
               f'<rect x="16" y="16" width="380" height="162" rx="4" fill="none" stroke="#fff" stroke-opacity=".28" stroke-width="1.5"/>'
               f'<rect x="{206 - kw / 2}" y="30" width="{kw}" height="34" rx="3" fill="{col}"/>'
               f'<text x="206" y="55" text-anchor="middle" font-family="{GOTH}" font-size="21" font-weight="700" fill="#fff" letter-spacing="3">{esc(kind)}</text>'
               f'<text x="206" y="{112 + size * .34:.0f}" text-anchor="middle" font-family="{GOTH}" font-size="{size:.0f}" font-weight="700" fill="#fff" letter-spacing="1">{esc(name)}</text>'
               f'<rect x="60" y="146" width="292" height="1.5" fill="#fff" opacity=".5"/>'
               f'<text x="206" y="166" text-anchor="middle" font-family="{MONO}" font-size="11.5" fill="#c7d0e0" letter-spacing="2">{USER.upper()} / {esc(repo.upper())}</text>')
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
    body = (f'<rect x=".5" y=".5" width="411" height="316" rx="8" fill="{BODY}" stroke="{EDGE}"/>' + poster(repo, name, col, kind or tag)
            + f'<g font-family="{GOTH}" font-size="10" fill="#aab0b8"><text x="14" y="200">種別</text><text x="70" y="200">名前</text>'
              f'<text x="400" y="200" text-anchor="end" font-family="{MONO}">{i:02d} // {esc(repo)}</text></g>'
            + a.svg() + b.svg())
    save(f"card-{repo}.svg", 412, 317, body, f"{name}: {' '.join(lines)}")


# --------------------------------------------------------------------------- header
def streaks(cal):
    """(days in a row up to now, longest run in the year, days since the last contribution)."""
    counts = [d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]]
    best = run = 0
    for c in counts:
        run = run + 1 if c else 0
        best = max(best, run)
    past = counts[:-1] if counts and not counts[-1] else counts  # today may still be empty
    cur = next((i for i, c in enumerate(reversed(past)) if not c), len(past))
    idle = next((i for i, c in enumerate(reversed(past)) if c), len(past))
    return cur, best, idle


OPENED = "2026-11-11"  # the day this profile went up
# MM-DD -> a line put in front of the scrolling text on that day.
SPECIAL = {
    "01-01": "謹賀新年。本年も当駅をよろしくお願いいたします。", "01-02": "謹賀新年。本年も当駅をよろしくお願いいたします。",
    "01-03": "謹賀新年。本年も当駅をよろしくお願いいたします。",
    "04-01": "本日に限り、すべての列車が定刻どおりに運転しています。",
    "07-07": "七夕です。短冊には「バグが出ませんように」と書きました。",
    "10-14": "本日は鉄道の日です。",
    "10-31": "ハロウィンです。お化けより本番障害のほうが怖い。",
    "12-24": "臨時列車 サンタクロース号が運転されます。", "12-25": "臨時列車 サンタクロース号が運転されます。",
    "12-31": "大みそかです。本年もご利用ありがとうございました。",
}
# month -> (what falls on the board, colours, seconds for one pass (0 = it stays and twinkles), the dots of one piece)
SNOW = ("雪", ["#e8f0ff"], 15, [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)])
SAKURA = ("桜", ["#ff9ec4"], 17, [(0, 0), (1, 0), (-1, 1), (0, 1), (1, 1), (0, 2)])
LEAF = ("紅葉", ["#ff7a3d", "#ffc04d"], 19, [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2), (0, 3)])
STAR = ("星", ["#fff3a0"], 0, [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)])
SEASON = {12: SNOW, 1: SNOW, 2: SNOW, 3: SAKURA, 4: SAKURA, 6: ("雨", ["#6aa8ff"], 3, [(0, 0), (0, 1), (0, 2), (0, 3)]),
          7: STAR, 8: STAR, 10: LEAF, 11: LEAF}


def notices(today):
    day = datetime.date.fromisoformat(today)
    out = []
    if today[5:] == OPENED[5:]:
        years = day.year - int(OPENED[:4])
        out.append(f"本日は当駅の開業記念日です。開業から {years} 年。" if years else "本日、当駅は開業しました。")
    if today[5:] in SPECIAL:
        out.append(SPECIAL[today[5:]])
    if day.timetuple().tm_yday == 256:
        out.append("本日は 256 日目、プログラマーの日です。")
    if day.weekday() == 4:
        out.append("本日は金曜日、週末ダイヤで運転しています。")
    return out


def header(repos, cal, today):
    """The departure board. The status line, the notices and what falls on the board follow the real data and the date."""
    cur, _, idle = streaks(cal)
    yesterday = (datetime.date.fromisoformat(today) - datetime.timedelta(days=1)).isoformat()
    fresh = [r for r in repos if r["tag_date"] >= yesterday]
    if fresh:
        n = max(fresh, key=lambda r: r["tag_date"])
        col, status = AMBER, f'臨時列車 {n["name"]} 発車'
    elif idle >= 3:
        col, status = RED, f"運転見合わせ 休養{idle}日目"
    elif cur >= 7:
        col, status = AMBER, f"増発中 連続{cur}日"
    else:
        col, status = GREEN, "全系統 正常稼働中"
    b = Board("h", LED_X, 61, LED_COLS, 86)
    b.put(F16, "TAKOSASI-DEV", 5, 4, AMBER, scale=2, bold=True)
    b.put(F16, "インフラ/ネットワーク", 207, 4, GREEN)
    b.put(F16, "/セキュリティ", 207, 21, GREEN)
    w = b.put(F16, "運行情報", 7, 44, RED, invert=True)
    pw =b.put(F16, f"のりば 1-{len(LINE)}", 397, 44, AMBER, right=True)
    b.put(F16, F16.fit(status, 397 - pw - 8 - (15 + w)), 15 + w, 44, col)
    extra = notices(today)
    b.ticker(F16, "".join(s + "　　" for s in extra)
             + "ゲーム、デスクトップツール、プラグインなど、思いついた物を作っています。　　"
               "GAMES, DESKTOP TOOLS, PLUGINS AND WHATEVER COMES TO MIND.　　　", 66, AMBER)
    _, cols, secs, piece = SEASON.get(int(today[5:7]), ("", [], 0, []))
    rnd = random.Random("season" + today)
    for i, c in enumerate(cols * 2):
        spots = [(rnd.randrange(2, LED_COLS - 3), rnd.randrange(2, 82)) for _ in range(18 // len(cols))]
        dots = [(x + dx, y + dy) for x, y in spots for dx, dy in piece]
        if secs:
            b.drift(dots, c, secs + i * 4, op=.8)  # two layers at different speeds
        else:  # stars do not fall: one half is steady, the other half blinks
            rows = [[0] * LED_COLS for _ in range(86)]
            for x, y in dots:
                rows[y][x] = 1
            b.raw(rows, 0, 0, c, blink=bool(i), op=.8)
    spots = "".join(
        f'<circle cx="{968 + i * 44}" cy="56" r="15" fill="{c}"/>'
        f'<text x="{968 + i * 44}" y="62" text-anchor="middle" font-size="17" font-weight="700" fill="#fff">{i + 1}</text>'
        for i, c in enumerate(LINE))
    body = (
        f'<g transform="scale(.705)"><rect x="180" width="14" height="30" fill="#33373e"/><rect x="1006" width="14" height="30" fill="#33373e"/>'
        f'<rect x="6" y="24" width="1188" height="328" rx="10" fill="{BODY}" stroke="{EDGE}"/>'
        f'<rect x="16" y="26" width="1168" height="2" fill="#6a717b" opacity=".45"/>'
        f'<g font-family="{GOTH}"><rect x="30" y="38" width="36" height="36" rx="5" fill="#1d63c4"/>'
        f'<path d="M40 49h16a3 3 0 0 1 3 3v11a3 3 0 0 1-3 3H40a3 3 0 0 1-3-3V52a3 3 0 0 1 3-3zm1 4v6h14v-6zm1 9.5a1.5 1.5 0 1 0 .01 0zm12 0a1.5 1.5 0 1 0 .01 0zM42 66l-3 4m15-4l3 4" fill="#fff" stroke="#fff" stroke-width="1.6" fill-rule="evenodd"/>'
        f'<text x="80" y="66" font-size="26" font-weight="700" fill="#f2f2ee" letter-spacing="4">発車案内</text>'
        f'<text x="214" y="65" font-size="15" fill="#aab0b8" letter-spacing="1">Departures</text>'
        f'<text x="886" y="62" font-size="15" fill="#aab0b8">のりば</text>{spots}</g></g>'
        + b.svg() + seam(b, 41) + seam(b, 63))
    save("header.svg", W, 252, body,
         f"TAKOSASI-DEV 発車案内。インフラ、ネットワーク、セキュリティ。運行情報: {status}。" + "".join(extra))


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
    save("stats.svg", W, h, casing(W, h, "運行状況", "Status", "公開リポジトリの集計") + b.svg() + seam(b, 38),
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
    save("releases.svg", W, h, casing(W, h, "新着リリース", "New releases") + heads + b.svg(),
         "新着リリース。" + "、".join(f'{md(r["tag_date"])} {r["name"]} {r["tag"]}' for r in rel))


def contrib(cal):
    counts = [d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]]
    cur, best, _ = streaks(cal)
    text =f"過去1年 {cal['totalContributions']:,}回　連続 {cur}日　最長 {best}日"
    t = Board("c", LED_X, 40, LED_COLS, 20)
    t.put(F16, F16.fit(text, 392), 5, 2, AMBER)
    weeks = cal["weeks"][-53:]
    h = Board("d", LED_X + (LED_COLS * 2 - 53 * 15) // 2, 92, 53, 7, 15)  # as wide as the text window above it
    lit = sorted(c for c in counts if c)
    for level, op in enumerate((.3, .55, .8, 1)):  # quartiles of the days that have anything
        rows = [[0] * 53 for _ in range(7)]
        for x, w in enumerate(weeks):
            for d in w["contributionDays"]:
                c = d["contributionCount"]
                if c and min(3, bisect.bisect_left(lit, c) * 4 // len(lit)) == level:
                    rows[datetime.date.fromisoformat(d["date"]).isoweekday() % 7][x] = 1
        h.raw(rows, 0, 0, GREEN, op=op)
    save("contrib.svg", W, 215, casing(W, 215, "稼働記録", "Contributions", "1 マスが 1 日。明るいほど活動が多い") + t.svg() + h.svg(), text)


def strip(title, n):
    """The sign on top of one ARCHIVE group: the line symbol with the repo count, like a station number."""
    slug, _, ja, sym, col, _ = CAT[title]
    plate(f"arc-{slug}.svg", col, sym, f"{n:02d}", ja, title)


# The daily fortune in the waiting room: (luck, how the trains run today, advice of at most 24 full-width characters).
FORTUNES = [
    ("大吉", "定刻運転", "今日書いたコードは一発で動くでしょう"),
    ("中吉", "平常運転", "こまめにコミットすると吉"),
    ("小吉", "徐行運転", "急がば回れ。先にテストを書くと吉"),
    ("吉", "各駅停車", "ひとつずつ片付けると吉"),
    ("末吉", "5分遅れ", "仕様書を読み直すと吉"),
    ("凶", "運転見合わせ", "今日は早く寝ると吉"),
]


def fortune(repos, today):
    """Drawn again every morning. The date (JST) is the seed, so a rerun on the same day gives the same draw."""
    rnd = random.Random(today)
    luck, run, advice = rnd.choice(FORTUNES)
    pick = rnd.choice(sorted(repos, key=lambda r: r["name"]))
    desc = DESC.get(pick["name"]) or pick["desc"]
    b = Board("o", LED_X, 40, LED_COLS, 100)
    w = b.put(F16, "本日の運行", 7, 4, GREEN, invert=True)
    b.put(F16, md(today), 15 + w, 4, AMBER)
    w = b.put(F16, luck, 6, 24, AMBER, scale=2)
    b.put(F16, run, 6 + w + 32, 24, GREEN, scale=2)
    b.put(F16, F16.fit(advice, 390), 6, 62, GREEN)
    b.ticker(F16, f'本日のおすすめ: {pick["name"]}　{desc}　　　', 82, AMBER)
    save("fortune.svg", W, 257, casing(W, 257, "本日の運行占い", "Today", "毎朝 6 時すぎに引き直します") + b.svg() + seam(b, 58),
         f"{md(today)} の運行占い: {luck}、{run}。{advice}。本日のおすすめは {pick['name']}")
    return (luck, run, advice), (f'本日のおすすめ: <a href="https://github.com/{USER}/{pick["name"]}">{esc(pick["name"])}</a>'
                                 + (f"（{esc(desc)}）" if desc else ""))


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
        # <picture> keeps GitHub from turning the image into a link, so a click on the sign opens the block.
        out.append(f'<details>\n<summary><picture><img src="assets/arc-{slug}.svg" height="40" align="middle" alt="{ja} / {title} ({len(rows)})"></picture></summary>\n<br>\n\n'
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
    # PROFILE_DATE=2026-12-31 lets you look at another day (season, notices, the daily draws).
    today = os.environ.get("PROFILE_DATE") or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    header(repos, cal, today)
    luck, pick = fortune(repos, today)
    parts = {"CARDS": cards_md(feat), "ARCHIVE": archive_md(groups), "FORTUNE": pick}
    # Everything an extension needs, so that it never has to import this file.
    ctx = {"repos": repos, "cal": cal, "cat_of": cat_of, "groups": groups, "today": today, "luck": luck,
           "CAT": CAT, "DESC": DESC, "USER": USER}
    for name in EXTENSIONS:
        if importlib.util.find_spec(name):
            parts.update(getattr(importlib.import_module(name), "live", lambda ctx: {})(ctx) or {})
    with open(README, encoding="utf-8", newline="") as f:
        text = f.read()
    for tag, body in parts.items():
        text = splice(text, tag, body)
    with open(README, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    check(repos)
