#!/usr/bin/env python3
"""Panels that follow the account's activity. update_live.py calls live(ctx) once a day.

    assets/stamps.svg      station stamp sheet: the achievements reached so far, and the ones still ahead
    assets/lost.svg        lost and found: the repos that have gone the longest without a push
    assets/lost-delay.svg  a delay certificate for the featured repo whose release is the most overdue
    assets/map-all.svg     every public repo as a station on the line of its category
    assets/rail.svg        a train of the six newest releases crossing the page (a ghost train one day a month)

Standard library only. `python3 scripts/ext_data.py` runs the self-check of the rules below.
"""
import calendar
import datetime
import itertools
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

INK = "#d6402b"  # vermilion stamp ink
# Speckled holes, so a stamp looks pressed by hand instead of printed.
INK_FILTER = ('<filter id="ink" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="7"/>'
              '<feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 -9 5.7"/>'
              '<feComposite in="SourceGraphic" operator="in"/></filter>')


def date(s):
    return datetime.date.fromisoformat(s[:10])


def md(d):
    return f"{d[5:7]}/{d[8:10]}"


# --------------------------------------------------------------------------- 1. stamp sheet
def facts(ctx):
    counts = [d["contributionCount"] for w in ctx["cal"]["weeks"] for d in w["contributionDays"]]
    best = run = 0
    for c in counts:
        run = run + 1 if c else 0
        best = max(best, run)
    repos = ctx["repos"]
    return {"repos": len(repos), "releases": sum(r["releases"] for r in repos),
            "langs": len({r["lang"] for r in repos} - {"-"}), "streak": best,
            "year": ctx["cal"]["totalContributions"], "lines": sum(1 for g in ctx["groups"].values() if g)}


def stamp_list(lines):
    """(fact, how much it takes, the three lines on the stamp, the caption under it)"""
    return [
        ("repos", 25, ("公開", "25", "系統"), "公開リポジトリ 25 本"),
        ("repos", 50, ("公開", "50", "系統"), "公開リポジトリ 50 本"),
        ("repos", 100, ("公開", "100", "系統"), "公開リポジトリ 100 本"),
        ("releases", 50, ("リリース", "50", "本"), "リリース 50 本"),
        ("releases", 100, ("リリース", "100", "本"), "リリース 100 本"),
        ("releases", 200, ("リリース", "200", "本"), "リリース 200 本"),
        ("langs", 8, ("言語", "8", "種"), "8 つの言語で作る"),
        ("lines", lines, ("全線", "開通", f"{lines} 路線"), f"{lines} 分類すべてに 1 本以上"),
        ("streak", 7, ("連続", "7", "日"), "7 日つづけて活動"),
        ("streak", 30, ("連続", "30", "日"), "30 日つづけて活動"),
        ("year", 500, ("年間", "500", "回"), "1 年の活動 500 回"),
        ("year", 1000, ("年間", "1000", "回"), "1 年の活動 1000 回"),
    ]


def stamps(ctx):
    have, todo = facts(ctx), stamp_list(len(ctx["CAT"]))
    done = sum(have[k] >= need for k, need, _, _ in todo)
    rows = -(-len(todo) // 4)
    H = 64 + 196 * rows + 6
    tilt = [-9, 6, -4, 8, -6, 3, 9, -7, 5, -3, 7, -8]
    out = (f'<defs>{INK_FILTER}</defs><g font-family="{GOTH}" text-anchor="middle">'
           f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="7" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
           f'<text x="24" y="38" text-anchor="start" font-size="23" font-weight="700" fill="#111" letter-spacing="4">駅スタンプ帳</text>'
           f'<text x="188" y="37" text-anchor="start" font-size="12" fill="#666" font-family="{MONO}" letter-spacing="2">STAMP RALLY</text>'
           f'<text x="{W - 24}" y="40" text-anchor="end" font-size="15" font-weight="700" fill="#555">あつめた数 '
           f'<tspan font-size="27" fill="{INK}">{done}</tspan> / {len(todo)}</text>')
    for i, (key, need, (top, big, bottom), caption) in enumerate(todo):
        cx, cy, ok = 123 + 200 * (i % 4), 136 + 196 * (i // 4), have[key] >= need
        col = INK if ok else "#b9bcc0"
        ring = (f'<circle r="62" stroke-width="4.5"/><circle r="53" stroke-width="1.5"/>' if ok
                else '<circle r="62" stroke-width="2" stroke-dasharray="5 6"/>')
        out += (seal(cx, cy, tilt[i % len(tilt)] if ok else 0, ok, col, ring, top, big, bottom)
                + f'<text x="{cx}" y="{cy + 88}" font-size="16.5" font-weight="700" fill="#222">{caption}</text>'
                + (f'<text x="{cx}" y="{cy + 109}" font-size="14.5" font-weight="700" fill="{INK}">達成</text>' if ok
                   else f'<text x="{cx}" y="{cy + 109}" font-size="14.5" fill="#777">いま {have[key]} / {need}</text>'))
    label = f"駅スタンプ帳: {done} / {len(todo)} 個。" + "、".join(f"{c}{'(達成)' if have[k] >= n else ''}" for k, n, _, c in todo)
    save("stamps.svg", W, H, out + "</g>", label)

    # the same sheet for a phone: two stamps to a row, each a little larger, so the small print inside stays readable
    cw, pitch, big_r = (WM - 40) / 2, 216, 1.13
    H = 92 + pitch * -(-len(todo) // 2) + 2
    out = (f'<defs>{INK_FILTER}</defs><g font-family="{GOTH}">' + sign_m(H, "駅スタンプ帳", "STAMP RALLY")
           + f'<text x="20" y="76" font-size="{SMALL}" font-weight="700" fill="#555">あつめた数 '
             f'<tspan font-size="28" fill="{INK}">{done}</tspan> / {len(todo)}</text><g text-anchor="middle">')
    for i, (key, need, (top, big, bottom), caption) in enumerate(todo):
        cx, cy, ok = 20 + cw / 2 + cw * (i % 2), 92 + 78 + pitch * (i // 2), have[key] >= need
        col = INK if ok else "#b9bcc0"
        ring = (f'<circle r="62" stroke-width="4.5"/><circle r="53" stroke-width="1.5"/>' if ok
                else '<circle r="62" stroke-width="2" stroke-dasharray="5 6"/>')
        squeeze = f' textLength="{cw - 8:.0f}" lengthAdjust="spacingAndGlyphs"' if text_w(caption, SMALL) > cw - 8 else ""
        out += (seal(cx, cy, tilt[i % len(tilt)] if ok else 0, ok, col, ring, top, big, bottom, f" scale({big_r})")
                + f'<text x="{cx}" y="{cy + 98}" font-size="{SMALL}" font-weight="700" fill="#222"{squeeze}>{caption}</text>'
                + (f'<text x="{cx}" y="{cy + 122}" font-size="{SMALL}" font-weight="700" fill="{INK}">達成</text>' if ok
                   else f'<text x="{cx}" y="{cy + 122}" font-size="{SMALL}" fill="#777">いま {have[key]} / {need}</text>'))
    save("stamps-m.svg", WM, H, out + "</g></g>", label)


def seal(cx, cy, turn, ok, col, ring, top, big, bottom, scale=""):
    """One stamp at (cx, cy): three lines of lettering in its ring. A stamp that was reached is pressed in ink, askew."""
    return (f'<g transform="translate({cx} {cy}) rotate({turn}){scale}"{" filter=" + chr(34) + "url(#ink)" + chr(34) if ok else ""}>'
            f'<g fill="none" stroke="{col}">{ring}</g><g fill="{col}" font-weight="800">'
            f'<text y="-24" font-size="16">{top}</text><text y="{14 if big.isdigit() else 10}" font-size="{40 if big.isdigit() else 30}">{big}</text>'
            f'<text y="36" font-size="15">{bottom}</text>'
            + ('<circle cx="-44" r="2.5"/><circle cx="44" r="2.5"/>' if len(big) < 4 else "") + '</g></g>')


# --------------------------------------------------------------------------- 2. lost and found
def overdue(repos, today, limit=60):
    """The featured repo whose release is the most overdue: (repo, days since its last release).
    Days is None for a featured repo that has never had a release; that one is picked only when
    nothing else is `limit` days late. (None, None) when there is no delay at all."""
    feat = [r for r in repos if "featured" in r["topics"]]
    late = [((today - date(r["tag_date"])).days, r["name"], r) for r in feat if r["tag_date"]]
    late = [x for x in late if x[0] >= limit]
    if late:
        days, _, r = max(late)
        return r, days
    never = [r for r in feat if not r["tag_date"]]
    return (never[0], None) if never else (None, None)


REASONS = ["作者が別の列車の整備に出ているため", "新しい路線の建設を先に進めているため", "点検(動作確認)に時間をかけているため"]


def lost(ctx):
    today = date(ctx["today"])
    old = sorted((r for r in ctx["repos"] if r["pushed"]), key=lambda r: (r["pushed"], r["name"]))[:3]
    n = len(old)
    b = Board("l", LED_X, 58, LED_COLS, 28 + 20 * n)
    for i, r in enumerate(old):
        y = 4 + i * 20
        b.put(F16, str(i + 1), 6, y, AMBER)
        w = b.put(F16, f"{(today - date(r['pushed'])).days}日間", 397, y, GREEN, right=True)
        b.put(F16, F16.fit(r["name"], 397 - w - 8 - 24), 24, y, AMBER)
    if old:
        tick = (f'{old[0]["name"]} が {(today - date(old[0]["pushed"])).days} 日間、ホームに置かれています。'
                "お心当たりの方は駅長室までお越しください。　　　")
    else:
        tick = "本日、お忘れ物はありません。　　　"
    b.ticker(F16, tick, 8 + 20 * n, AMBER)
    h = 58 + b.h + 17
    heads = (f'<g font-family="{GOTH}" font-size="10.5" fill="#aab0b8"><text x="31" y="50">順</text><text x="69" y="50">お忘れ物</text>'
             f'<text x="815" y="50" text-anchor="end">置かれている日数</text></g>')
    save("lost.svg", W, h, casing(W, h, "お忘れ物センター", "Lost and found", "最後の push からの日数。毎朝更新") + heads + b.svg()
         + (seam(b, 4 + 20 * n) if old else ""), "お忘れ物センター。" + tick.strip())

    # the delay certificate, a paper slip
    r, days = overdue(ctx["repos"], today)
    H, blue = 232, "#1d4f9e"
    out = (f'<defs>{INK_FILTER}</defs><g font-family="{GOTH}"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="5" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
           f'<rect x="10" y="10" width="{W - 20}" height="{H - 20}" fill="none" stroke="{blue}" stroke-width="2"/>'
           f'<rect x="15" y="15" width="{W - 30}" height="{H - 30}" fill="none" stroke="{blue}" stroke-width=".8"/>'
           f'<text x="40" y="62" font-size="33" font-weight="800" fill="{blue}" letter-spacing="10">遅延証明書</text>'
           f'<text x="318" y="60" font-size="12" fill="{blue}" font-family="{MONO}" letter-spacing="2">DELAY CERTIFICATE</text>'
           f'<text x="{W - 40}" y="60" text-anchor="end" font-size="15" fill="#333" font-family="{MONO}">{ctx["today"].replace("-", ".")}</text>')
    if r:
        late = (f'最後のリリース {esc(r["tag"])}({md(r["tag_date"])})から {days} 日' if days is not None else "最初のリリースを準備中")
        why = random.Random(r["name"] + ctx["today"][:7]).choice(REASONS)
        out += (f'<text x="40" y="96" font-size="16.5" fill="#222">下記の列車は、リリースが遅れていることを証明します。</text>'
                + "".join(f'<text x="40" y="{132 + k * 30}" font-size="16" font-weight="700" fill="{blue}">{a}</text>'
                          f'<text x="104" y="{132 + k * 30}" font-size="19" font-weight="700" fill="#111">{v}</text>'
                          for k, (a, v) in enumerate([("列車", esc(r["name"])), ("遅れ", late), ("理由", why)])))
        label = f"遅延証明書: {r['name']}、{late}。理由: {why}"
        facts_m = [("列車", esc(r["name"])), ("遅れ", late), ("理由", why)]
    else:
        facts_m = None
        out += (f'<text x="40" y="128" font-size="26" font-weight="800" fill="#111">本日、遅延はありません。</text>'
                f'<text x="40" y="164" font-size="17" fill="#222">全列車、定刻どおり運転しています。</text>')
        label = "遅延証明書: 本日、遅延はありません"
    out += (f'<g transform="translate({W - 92} {H - 78}) rotate(-7)" filter="url(#ink)"><rect x="-34" y="-34" width="68" height="68" rx="5" fill="none" stroke="{INK}" stroke-width="4"/>'
            f'<text y="-4" text-anchor="middle" font-size="22" font-weight="800" fill="{INK}">駅長</text>'
            f'<text y="20" text-anchor="middle" font-size="13" font-weight="800" fill="{INK}">之印</text></g>'
            f'<text x="{W - 140}" y="{H - 34}" text-anchor="end" font-size="14" fill="#333">takosasi-dev 駅</text></g>')
    save("lost-delay.svg", W, H, out, label)
    delay_m(ctx["today"], facts_m, label)


def delay_m(today, rows, label, blue="#1d4f9e"):
    """The delay certificate for a phone (lost-delay-m.svg): the same slip, narrow, every sentence broken to fit.
    rows: [(heading, text already escaped)], or None on a day without a delay."""
    out, y = "", 132
    if rows:
        for ln in wrap_px("下記の列車は、リリースが遅れていることを証明します。", 19, WM - 64):
            out += f'<text x="32" y="{y}" font-size="19" fill="#222">{ln}</text>'
            y += 27
        y += 12
        for a, v in rows:  # the heading over its text: beside it, a reason would not fit on one line
            out += f'<text x="32" y="{y}" font-size="{SMALL}" font-weight="700" fill="{blue}">{a}</text>'
            for ln in wrap_px(v, 20, WM - 64):
                y += 27
                out += f'<text x="32" y="{y}" font-size="20" font-weight="700" fill="#111">{ln}</text>'
            y += 36
        y -= 18
    else:
        out += (f'<text x="32" y="{y + 6}" font-size="26" font-weight="800" fill="#111">本日、遅延はありません。</text>'
                f'<text x="32" y="{y + 42}" font-size="19" fill="#222">全列車、定刻どおり運転しています。</text>')
        y += 64
    H = y + 112  # room for the seal under the last line
    out = (f'<defs>{INK_FILTER}</defs><g font-family="{GOTH}"><rect x="1" y="1" width="{WM - 2}" height="{H - 2}" rx="5" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
           f'<rect x="10" y="10" width="{WM - 20}" height="{H - 20}" fill="none" stroke="{blue}" stroke-width="2"/>'
           f'<rect x="15" y="15" width="{WM - 30}" height="{H - 30}" fill="none" stroke="{blue}" stroke-width=".8"/>'
           f'<text x="32" y="64" font-size="31" font-weight="800" fill="{blue}" letter-spacing="9">遅延証明書</text>'
           f'<text x="32" y="94" font-size="{SMALL}" fill="{blue}" font-family="{MONO}">DELAY CERTIFICATE</text>'
           f'<text x="{WM - 32}" y="94" text-anchor="end" font-size="{SMALL}" fill="#333" font-family="{MONO}">{today.replace("-", ".")}</text>'
           + out
           + f'<g transform="translate({WM - 76} {H - 70}) rotate(-7) scale(1.2)" filter="url(#ink)"><rect x="-34" y="-34" width="68" height="68" rx="5" fill="none" stroke="{INK}" stroke-width="4"/>'
             f'<text y="-4" text-anchor="middle" font-size="22" font-weight="800" fill="{INK}">駅長</text>'
             f'<text y="20" text-anchor="middle" font-size="13" font-weight="800" fill="{INK}">之印</text></g>'
             f'<text x="{WM - 134}" y="{H - 34}" text-anchor="end" font-size="{SMALL}" fill="#333">takosasi-dev 駅</text></g>')
    save("lost-delay-m.svg", WM, H, out, label)


# --------------------------------------------------------------------------- 3. the map of every repo
COLS, FOLD, CHARS = 3, 18, 19  # columns on the sheet; stations before a line folds into a new block; letters on one name line


def name_lines(name, chars=CHARS, most=2):
    """A station name on one line, or broken at hyphens into `most` lines at most (the last is cut if still too long)."""
    out = []
    while len(name) > chars and len(out) < most - 1:
        cut = name.rfind("-", 1, chars) + 1 or chars
        out.append(name[:cut])
        name = name[cut:]
    return out + [name if len(name) <= chars else name[:chars - 2] + ".."]


def map_all(ctx):
    CAT, today = ctx["CAT"], date(ctx["today"])
    # ponytail: the API data here has no creation date, so "old to new" falls back to the latest release, then
    # the last push. Add createdAt to QUERY in update_live.py (as r["created"]) and the order becomes the real one.
    born = lambda r: r.get("created") or r["tag_date"] or r["pushed"] or ""  # noqa: E731
    newest = max(ctx["repos"], key=lambda r: (born(r), r["name"]), default={}).get("name")
    blocks = []  # (title, index of the part, stations, is the last part, stations on the whole line)
    for title, rows in ctx["groups"].items():
        st = sorted(rows, key=lambda r: (born(r), r["name"]))
        parts = [st[i:i + FOLD] for i in range(0, len(st), FOLD)]
        blocks += [(title, k, p, k == len(parts) - 1, len(st)) for k, p in enumerate(parts)]

    known = any(r.get("created") for r in ctx["repos"])

    def opened(r, last):
        """The "newly opened" tag: the newest station of all, and, once real creation dates are in the data,
        the end of any line that opened within 30 days."""
        return last and (r["name"] == newest or bool(known and r.get("created") and (today - date(r["created"])).days <= 30))

    def height(b):
        _, _, st, last, _ = b
        return 46 + sum(12 + 22 * len(name_lines(r["name"])) + (22 if opened(r, last and r is st[-1]) else 0) for r in st) + 34

    # Keep the blocks in order and cut them into columns where the tallest column comes out shortest.
    hs = [height(b) for b in blocks]
    cuts = min(itertools.combinations(range(1, len(blocks)), min(COLS, len(blocks)) - 1),
               key=lambda c: max(sum(hs[a:b]) for a, b in zip((0,) + c, c + (len(blocks),)))) if blocks else ()
    cw = (W - 36) / COLS
    col, y, top, out, bottom = 0, 64, 64, "", 64
    for bi, b in enumerate(blocks):
        title, part, st, last, total = b
        if bi in cuts:
            col, y = col + 1, top
        _, _, ja, sym, lc, _ = CAT[title]
        x0 = 18 + col * cw + 6
        sx, yy = x0 + 17, y + 46
        ys = []
        for r in st:
            ys.append(yy + 10)
            yy += 12 + 22 * len(name_lines(r["name"])) + (22 if opened(r, last and r is st[-1]) else 0)
        end = ys[-1]
        out += (f'<path d="M{sx} {y + 16}V{end}" stroke="{lc}" stroke-width="8"/>'
                + (f'<path d="M{sx} {end}v26" stroke="{lc}" stroke-width="8" stroke-dasharray="3 5"/>' if last
                   else f'<path d="M{sx} {end}V{yy + 8}" stroke="{lc}" stroke-width="8"/>'
                        f'<text x="{sx + 18}" y="{yy + 12}" font-size="12.5" fill="#666">つづく</text>')
                + f'<rect x="{x0}" y="{y}" width="{cw - 14:.0f}" height="32" rx="16" fill="{lc}"/>'
                  f'<circle cx="{sx}" cy="{y + 16}" r="11.5" fill="#fff"/>'
                  f'<text x="{sx}" y="{y + 21}" text-anchor="middle" font-size="13.5" font-weight="800" fill="#111">{sym}</text>'
                  f'<text x="{x0 + 36}" y="{y + 22}" font-size="16.5" font-weight="700" fill="#fff">{ja}{"(つづき)" if part else ""}</text>'
                  f'<text x="{x0 + cw - 28:.0f}" y="{y + 21}" text-anchor="end" font-size="13.5" font-weight="700" fill="#fff">{total} 駅</text>')
        for r, sy in zip(st, ys):
            new = opened(r, last and r is st[-1])
            out += (f'<circle cx="{sx}" cy="{sy}" r="{9 if new else 7}" fill="#fff" stroke="{INK if new else "#222"}" stroke-width="{4.5 if new else 3}"/>'
                    + "".join(f'<text x="{sx + 18}" y="{sy + 6 + k * 22}" font-family="{MONO}" font-size="18" font-weight="700" fill="#111">{esc(ln)}</text>'
                              for k, ln in enumerate(name_lines(r["name"]))))
            if new:
                ty = sy + 22 * len(name_lines(r["name"])) - 6
                out += (f'<rect x="{sx + 18}" y="{ty}" width="72" height="19" rx="9.5" fill="{INK}"/>'
                        f'<text x="{sx + 54}" y="{ty + 14}" text-anchor="middle" font-size="12.5" font-weight="700" fill="#fff">延伸開業</text>')
        y += height(b)
        bottom = max(bottom, y)
    H = bottom + 6
    lines = sum(1 for g in ctx["groups"].values() if g)
    head = (f'<g font-family="{GOTH}"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="7" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
            f'<text x="24" y="38" font-size="23" font-weight="700" fill="#111" letter-spacing="4">全線路線図</text>'
            f'<text x="162" y="37" font-size="12" fill="#666" font-family="{MONO}" letter-spacing="2">ALL LINES</text>'
            f'<text x="{W - 24}" y="37" text-anchor="end" font-size="14" font-weight="700" fill="#555">{len(ctx["repos"])} 駅 / {lines} 路線。下へ行くほど新しい駅</text>')
    label = (f"全線路線図: {len(ctx['repos'])} 駅 / {lines} 路線。"
             + "。".join(f"{CAT[t][2]}: {'、'.join(r['name'] for r in sorted(g, key=lambda r: (born(r), r['name'])))}" for t, g in ctx["groups"].items() if g))
    save("map-all.svg", W, H, head + out + "</g>", label)
    map_all_m(ctx, born, opened, label)


def map_all_m(ctx, born, opened, label):
    """The same map for a phone: two columns, a line is never folded, a long name breaks at its hyphens
    (three lines at most) instead of being cut. More repos only make the sheet taller."""
    # ponytail: a line is never folded here, so one line far longer than the rest leaves the other column short.
    # Fold it the way map_all() does with FOLD if a category ever passes about 25 repos.
    CAT = ctx["CAT"]
    lines = [(t, sorted(g, key=lambda r: (born(r), r["name"]))) for t, g in ctx["groups"].items() if g]
    rows = lambda r: name_lines(r["name"], 14, 3)  # noqa: E731
    step = lambda r, last: 10 + 23 * len(rows(r)) + (28 if opened(r, last) else 0)  # noqa: E731
    hs = [50 + sum(step(r, r is st[-1]) for r in st) + 36 for _, st in lines]
    cut = min(range(1, len(lines)), key=lambda c: max(sum(hs[:c]), sum(hs[c:])), default=len(lines))
    cw, top = (WM - 20) / 2, 92
    out, y, bottom = "", top, top
    for i, ((title, st), h) in enumerate(zip(lines, hs)):
        if i == cut:
            y = top
        _, _, ja, sym, lc, _ = CAT[title]
        x0 = 14 + (i >= cut) * cw
        sx, pw, count = x0 + 18, cw - 10, f"{len(st)}駅"
        room = pw - 38 - text_w(count, SMALL) - 18
        squeeze = f' textLength="{room:.0f}" lengthAdjust="spacingAndGlyphs"' if text_w(ja, SMALL) > room else ""
        ys, yy = [], y + 50
        for r in st:
            ys.append(yy + 10)
            yy += step(r, r is st[-1])
        out += (f'<path d="M{sx} {y + 18}V{ys[-1]}" stroke="{lc}" stroke-width="8"/>'
                f'<path d="M{sx} {ys[-1]}V{yy + 14}" stroke="{lc}" stroke-width="8" stroke-dasharray="3 5"/>'
                f'<rect x="{x0}" y="{y}" width="{pw:.0f}" height="36" rx="18" fill="{lc}"/>'
                f'<circle cx="{sx}" cy="{y + 18}" r="13" fill="#fff"/>'
                f'<text x="{sx}" y="{y + 24}" text-anchor="middle" font-size="16.5" font-weight="800" fill="#111">{sym}</text>'
                f'<text x="{x0 + 38}" y="{y + 25}" font-size="{SMALL}" font-weight="700" fill="#fff"{squeeze}>{ja}</text>'
                f'<text x="{x0 + pw - 12:.0f}" y="{y + 25}" text-anchor="end" font-size="{SMALL}" font-weight="700" fill="#fff">{count}</text>')
        for r, sy in zip(st, ys):
            new, ls = opened(r, r is st[-1]), rows(r)
            out += (f'<circle cx="{sx}" cy="{sy}" r="{9 if new else 7}" fill="#fff" stroke="{INK if new else "#222"}" stroke-width="{4.5 if new else 3}"/>'
                    + "".join(f'<text x="{sx + 18}" y="{sy + 6 + k * 23}" font-family="{MONO}" font-size="{SMALL}" font-weight="700" fill="#111">{esc(ln)}</text>'
                              for k, ln in enumerate(ls)))
            if new:
                ty = sy + 23 * len(ls) - 7
                out += (f'<rect x="{sx + 18}" y="{ty}" width="92" height="26" rx="13" fill="{INK}"/>'
                        f'<text x="{sx + 64}" y="{ty + 19.5}" text-anchor="middle" font-size="{SMALL}" font-weight="700" fill="#fff">延伸開業</text>')
        y += h
        bottom = max(bottom, y)
    H = bottom + 2
    head = (f'<g font-family="{GOTH}">' + sign_m(H, "全線路線図", "ALL LINES")
            + f'<text x="20" y="72" font-size="{SMALL}" font-weight="700" fill="#555">{len(ctx["repos"])} 駅 / {len(lines)} 路線。下へ行くほど新しい駅</text>')
    save("map-all-m.svg", WM, H, head + out + "</g>", label)


# --------------------------------------------------------------------------- 4. the train across the page
def ghost_day(year, month):
    """The one day of the month on which the ghost train runs. Seeded by the month, so it moves every month."""
    return random.Random(f"kisaragi:{year}-{month:02d}").randint(1, calendar.monthrange(year, month)[1])


def rail(ctx):
    today = date(ctx["today"])
    ghost = today.day == ghost_day(today.year, today.month)
    cars = sorted((r for r in ctx["repos"] if r["tag_date"]), key=lambda r: (r["tag_date"], r["name"]), reverse=True)[:6]
    n = 6 if ghost else len(cars)
    cw, gap, hw, H = 116, 4, 86, 76
    L = hw + n * (cw + gap)
    x0 = (W - L) // 2  # where the train stands when motion is turned off
    hx = x0 + L - hw   # the head is at the right end; the train runs to the right
    body, lamp, glass = ("#45415a", "#c9ffd6", "#191922") if ghost else ("#eceff2", "#ffd84a", "#27303b")
    out = ""
    for i in range(n):
        x = hx - (i + 1) * (cw + gap)
        if ghost:
            sign = (f'<rect x="{x + 22}" y="23" width="72" height="20" fill="#0c0c10"/><text x="{x + 58}" y="38" text-anchor="middle" font-family="{GOTH}" '
                    f'font-size="13.5" font-weight="700" fill="#c9ffd6">きさらぎ</text>') if i == 0 else "".join(
                    f'<rect class="fl" style="animation-delay:-{(i * 7 + k * 3) % 11 / 2}s" x="{x + 14 + k * 24}" y="24" width="16" height="13" fill="#c9ffd6" opacity=".35"/>' for k in range(4))
            out += f'<rect x="{x}" y="16" width="{cw}" height="36" rx="5" fill="{body}" stroke="#77718f"/>{sign}'
        else:
            col = ctx["CAT"][ctx["cat_of"][cars[i]["name"]]][4]
            name = cars[i]["name"] if len(cars[i]["name"]) <= 13 else cars[i]["name"][:11] + ".."
            out += (f'<rect x="{x}" y="16" width="{cw}" height="36" rx="5" fill="{col}" stroke="#000" stroke-opacity=".35"/>'
                    f'<rect x="{x}" y="45" width="{cw}" height="2" fill="#fff" opacity=".55"/>'
                    f'<text x="{x + cw / 2}" y="37" text-anchor="middle" font-family="{MONO}" font-size="13" font-weight="800" fill="#fff">{esc(name)}</text>')
        out += (f'<rect x="{x + cw}" y="38" width="{gap}" height="4" fill="#555b64"/>'
                + "".join(f'<circle cx="{x + dx}" cy="55" r="4.5" fill="#2b2f36" stroke="#8a9099"/>' for dx in (20, 36, cw - 36, cw - 20)))
    out += (f'<path d="M{hx} 16h{hw - 34}q26 3 34 24v12h-{hw}z" fill="{body}" stroke="{"#77718f" if ghost else "#8a9099"}"/>'
            f'<path d="M{hx + hw - 40} 21h8q14 3 20 15h-28z" fill="{glass}"/>'
            f'<rect x="{hx + 8}" y="22" width="34" height="18" rx="3" fill="{glass}"/>'
            f'<text x="{hx + 25}" y="36" text-anchor="middle" font-family="{GOTH}" font-size="12.5" font-weight="700" fill="{lamp if ghost else "#fff"}">{"回送" if ghost else "新着"}</text>'
            f'<rect x="{hx}" y="45" width="{hw}" height="2" fill="{"#77718f" if ghost else LINE[2]}"/>'
            f'<circle cx="{hx + hw - 5}" cy="46" r="3.5" fill="{lamp}"/>'
            + (f'<circle class="fl" cx="{hx + hw - 5}" cy="46" r="9" fill="{lamp}" opacity=".3"/>' if ghost else "")
            + "".join(f'<circle cx="{hx + dx}" cy="55" r="4.5" fill="#2b2f36" stroke="#8a9099"/>' for dx in (16, 32, hw - 26)))
    period, share = (26, 50) if ghost else (20, 45)
    css = (f"@keyframes tr{{0%{{transform:translateX(-{x0 + L + 20}px)}}{share}%,100%{{transform:translateX({W - x0 + 20}px)}}}}"
           f".tr{{animation:tr {period}s linear infinite}}@keyframes fl{{50%{{opacity:.08}}}}.fl{{animation:fl 1.3s steps(2) infinite}}"
           "@media (prefers-reduced-motion:reduce){.tr,.fl{animation:none}}")
    track = (f'<path d="M0 60H{W}" stroke="#8a9099" stroke-width="2.5"/><path d="M2 65H{W}" stroke="#6a717b" stroke-width="5" stroke-dasharray="4 12"/>')
    save("rail.svg", W, H, f"<style>{css}</style>{track}<g class=\"tr\">{out}</g>",
         "回送列車が通過します" if ghost else "新着リリースの列車: " + "、".join(r["name"] for r in cars))


def live(ctx):
    stamps(ctx)
    lost(ctx)
    map_all(ctx)
    rail(ctx)
    return {}


if __name__ == "__main__":  # self-check of the rules: python3 scripts/ext_data.py
    cal = {"totalContributions": 600, "weeks": [{"contributionDays": [{"contributionCount": c} for c in (1, 1, 0, 1, 1, 1, 0)]}]}
    mk = lambda name, pushed, tag_date="", topics=(): {"name": name, "pushed": pushed, "tag": "v1" if tag_date else "", "tag_date": tag_date,  # noqa: E731
                                                       "topics": set(topics), "releases": 1 if tag_date else 0, "lang": "Python"}
    repos = [mk("a", "2026-01-01", "2026-08-01", ["featured"]), mk("b", "2026-02-01", "2026-10-20", ["featured"]), mk("c", "2026-03-01", "", ["featured"])]
    f = facts({"cal": cal, "repos": repos, "groups": {"X": repos, "Y": []}})
    assert f == {"repos": 3, "releases": 2, "langs": 1, "streak": 3, "year": 600, "lines": 1}, f
    got = [f[k] >= need for k, need, _, _ in stamp_list(8)]
    assert got.count(True) == 1 and got[10], got  # only "500 a year" is reached with these numbers
    day = datetime.date(2026, 11, 11)
    assert overdue(repos, day) == (repos[0], 102)                      # the longest since its release wins
    assert overdue(repos[1:], day) == (repos[2], None)                 # 22 days is not late; the one without a release is named
    assert overdue(repos[1:2], day) == (None, None) and overdue([mk("d", "2026-01-01", "2026-01-01")], day) == (None, None)
    days = [ghost_day(2026, m) for m in range(1, 13)]
    assert all(1 <= d <= calendar.monthrange(2026, m)[1] for m, d in enumerate(days, 1)) and len(set(days)) > 6, days
    assert ghost_day(2026, 11) == ghost_day(2026, 11)
    assert name_lines("padlab") == ["padlab"] and name_lines("minecraft-building-blocks-plus") == ["minecraft-building-", "blocks-plus"]
    assert name_lines("a" * 45) == ["a" * 19, "a" * 17 + ".."]
    # the phone sheet: narrower lines, three of them, so no real name is cut
    assert name_lines("minecraft-building-blocks-plus", 14, 3) == ["minecraft-", "building-", "blocks-plus"]
    assert name_lines("-ai-work-board-", 14, 3) == ["-ai-work-", "board-"] and name_lines("a" * 45, 14, 3)[2] == "a" * 12 + ".."
    print("ext_data ok, ghost days 2026:", days)
