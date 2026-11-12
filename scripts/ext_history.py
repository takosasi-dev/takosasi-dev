#!/usr/bin/env python3
"""assets/history.svg: the "history of this station" sign. Every row is taken from the data: the day
the account was made, the creation dates of the repos that are public now, the day this profile went up.
Nothing is made up. update_live.py calls live(ctx) once a day. Standard library only.

    python3 scripts/ext_history.py    # self-check
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

MAX = 10             # rows on the sign
NTH = (10, 25, 50, 100)
BLUE = "#1d4f9e"


def events(ctx):
    """[(sort key, date as printed, text)] oldest first, MAX rows at most. The fixed rows come first;
    the featured repos fill what is left, in the order of their cards."""
    # Repos made on the same day are put in order by the time, if the data carries it ("created_at" or a full "created").
    repos = sorted((r for r in ctx["repos"] if r.get("created")), key=lambda r: (r.get("created_at") or r["created"], r["name"]))
    names = dict(ctx.get("feat") or [])
    dot = lambda d: d[:10].replace("-", ".")  # noqa: E731
    name = lambda r: names.get(r["name"], r["name"])  # noqa: E731
    out, used = [], set()
    if ctx.get("joined"):
        out.append((ctx["joined"], dot(ctx["joined"]), "開業。GitHub に登録"))
    if repos:
        out.append((repos[0]["created"][:10], dot(repos[0]["created"]), f"公開中でいちばん古い駅「{name(repos[0])}」を新設"))
        used.add(repos[0]["name"])
        for n in NTH:
            if len(repos) >= n and repos[n - 1]["name"] not in used:
                r = repos[n - 1]
                out.append((r["created"][:10], dot(r["created"]), f"{n} 本目の駅「{name(r)}」を新設"))
                used.add(r["name"])
        month, most = max(collections.Counter(r["created"][:7] for r in repos).items(), key=lambda kv: (kv[1], kv[0]))
        if most >= 3:
            out.append((month + "-99", dot(month), f"この月だけで {most} 駅を新設(月間の最多)"))  # sorts after the days of its month
    if ctx.get("opened"):
        out.append((ctx["opened"] + "~", dot(ctx["opened"]), "この駅舎(プロフィール)を公開"))
    out.append((ctx["today"] + "~~", dot(ctx["today"]), f'現在 {len(ctx["repos"])} 駅、リリース {sum(r["releases"] for r in ctx["repos"])} 本'))
    by = {r["name"]: r for r in repos}
    for repo, shown in ctx.get("feat") or []:
        if len(out) >= MAX:
            break
        if repo in by and repo not in used:
            out.append((by[repo]["created"][:10], dot(by[repo]["created"]), f"「{shown}」駅を新設"))
    return sorted(out)[:MAX]


def live(ctx):
    ev = events(ctx)
    step, top = 36, 92
    H = top + step * len(ev) - 2
    lx = 196  # the line the stations sit on
    out = (f'<g font-family="{GOTH}"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="7" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
           f'<text x="24" y="38" font-size="23" font-weight="700" fill="#111" letter-spacing="4">沿革</text>'
           f'<text x="86" y="37" font-size="12" fill="#666" font-family="{MONO}" letter-spacing="2">HISTORY</text>'
           f'<text x="{W - 24}" y="37" text-anchor="end" font-size="13" font-weight="700" fill="#555">いま公開しているリポジトリの記録から自動で作成</text>'
           f'<rect x="20" y="52" width="{W - 40}" height="2" fill="{BLUE}"/>'
           f'<path d="M{lx} {top - 22}V{top + step * (len(ev) - 1) - 6}" stroke="{BLUE}" stroke-width="7" stroke-linecap="round"/>')
    year = ""
    for i, (_, date, text) in enumerate(ev):
        y, last = top + i * step, i == len(ev) - 1
        if date[:4] != year:
            year = date[:4]
            out += f'<text x="28" y="{y}" font-size="21" font-weight="800" fill="{BLUE}" font-family="{MONO}">{year}</text>'
        day = date[5:] if len(date) > 7 else f"{int(date[5:])} 月"
        # A long repo name is squeezed instead of running off the sign (an ASCII letter is about half a kanji wide).
        wide = sum(20 if ord(c) > 0x2000 else 11.5 for c in text)
        squeeze = f' textLength="{W - lx - 46}" lengthAdjust="spacingAndGlyphs"' if wide > W - lx - 46 else ""
        out += (f'<text x="{lx - 22}" y="{y}" text-anchor="end" font-size="18" font-weight="700" fill="#333" font-family="{MONO}">{day}</text>'
                f'<circle cx="{lx}" cy="{y - 7}" r="{10 if last else 8}" fill="#fff" stroke="{"#d6402b" if last else "#222"}" stroke-width="{4.5 if last else 3.5}"/>'
                f'<text x="{lx + 24}" y="{y}" font-size="20" font-weight="700" fill="#111"{squeeze}>{esc(text)}</text>')
    save("history.svg", W, H, out + "</g>", "沿革。" + "。".join(f"{d} {t}" for _, d, t in ev))
    draw_m(ev)
    return {}


def draw_m(ev):
    """The same sign for a phone (history-m.svg): the line runs down the left edge, each row is the day and,
    under it, what happened, broken into as many lines as it needs."""
    lx, tx = 32, 58
    note = ["いま公開しているリポジトリの", "記録から自動で作成"]
    y = 50 + 24 * len(note) + 14
    rows, year = "", ""
    rule = f'<rect x="20" y="{y}" width="{WM - 40}" height="2" fill="{BLUE}"/>'
    y += 18
    first = None
    for i, (_, date, text) in enumerate(ev):
        last = i == len(ev) - 1
        if date[:4] != year:
            year = date[:4]
            rows += f'<text x="{tx}" y="{y + 22}" font-size="24" font-weight="800" fill="{BLUE}" font-family="{MONO}">{year}</text>'
            y += 38
        day = date[5:] if len(date) > 7 else f"{int(date[5:])} 月"
        first = first or y + 12
        rows += (f'<circle cx="{lx}" cy="{y + 12}" r="{10 if last else 8}" fill="#fff" stroke="{"#d6402b" if last else "#222"}" stroke-width="{4.5 if last else 3.5}"/>'
                 f'<text x="{tx}" y="{y + 19}" font-size="{SMALL}" font-weight="700" fill="#555" font-family="{MONO}">{day}</text>')
        end = y + 12
        for k, ln in enumerate(wrap_px(text, 20, WM - tx - 16)):
            rows += f'<text x="{tx}" y="{y + 45 + k * 26}" font-size="20" font-weight="700" fill="#111">{esc(ln)}</text>'
            bottom = y + 45 + k * 26
        y = bottom + 22
    H = y - 2
    out = (f'<g font-family="{GOTH}">' + sign_m(H, "沿革", "HISTORY")
           + "".join(f'<text x="20" y="{72 + k * 24}" font-size="{SMALL}" font-weight="700" fill="#555">{ln}</text>' for k, ln in enumerate(note))
           + rule + f'<path d="M{lx} {first}V{end}" stroke="{BLUE}" stroke-width="7" stroke-linecap="round"/>' + rows + "</g>")
    save("history-m.svg", WM, H, out, "沿革。" + "。".join(f"{d} {t}" for _, d, t in ev))


if __name__ == "__main__":  # self-check: python3 scripts/ext_history.py
    mk = lambda i: {"name": f"r{i:02d}", "created": f"2026-{1 + i // 20:02d}-{1 + i % 20:02d}", "releases": 2}  # noqa: E731
    ctx = {"repos": [mk(i) for i in range(30)], "feat": [("r00", "First"), ("r05", "Five"), ("r09", "Nine"), ("r12", "Twelve")],
           "joined": "2024-12-16", "opened": "2026-02-10", "today": "2026-02-10"}
    ev = events(ctx)
    texts = [t for _, _, t in ev]
    assert ev == sorted(ev) and len(ev) <= MAX, ev
    assert texts[0] == "開業。GitHub に登録" and texts[1] == "公開中でいちばん古い駅「First」を新設", texts  # display name of a featured repo
    assert "10 本目の駅「Nine」を新設" in texts and "25 本目の駅「r24」を新設" in texts and not any("50 本目" in t for t in texts)
    assert "この月だけで 20 駅を新設(月間の最多)" in texts and [d for _, d, t in ev if "月間" in t] == ["2026.01"]
    assert texts[-2:] == ["この駅舎(プロフィール)を公開", "現在 30 駅、リリース 60 本"], texts  # same day: the opening, then today
    assert "「Five」駅を新設" in texts and "「Twelve」駅を新設" in texts and sum("First" in t or "Nine" in t for t in texts) == 2  # one row per repo
    many = dict(ctx, feat=[(f"r{i:02d}", f"F{i}") for i in range(1, 9)], repos=[mk(i) for i in range(60)])
    assert len(events(many)) == MAX
    # no creation dates and no account date (an old saved response): the sign still has its last rows
    assert [t for _, _, t in events({"repos": [{"name": "a", "releases": 1}], "today": "2026-11-11"})] == ["現在 1 駅、リリース 1 本"]
    # made on the same day: the time decides which one is the oldest, when the data has it
    same = [{"name": "a", "created": "2026-01-01", "created_at": "2026-01-01T09:00:00Z", "releases": 0},
            {"name": "b", "created": "2026-01-01", "created_at": "2026-01-01T08:00:00Z", "releases": 0}]
    assert "「b」" in events({"repos": same, "today": "2026-01-02"})[0][2]
    assert "「a」" in events({"repos": [{k: v for k, v in r.items() if k != "created_at"} for r in same], "today": "2026-01-02"})[0][2]
    full = [dict(r, created=r["created_at"]) for r in same]  # "created" itself may carry the time
    assert events({"repos": full, "today": "2026-01-02"})[0][:2] == ("2026-01-01", "2026.01.01")
    print("history ok")
