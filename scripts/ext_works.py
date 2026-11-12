#!/usr/bin/env python3
"""assets/works.svg and works-m.svg: the works notice, what is being built right now. A repo pushed in the
last DAYS days is a section under construction: one that was also made in that time is a new line ("新設"),
an older one an improvement ("改良"). Taken from the data, nothing is written by hand.
update_live.py calls live(ctx) once a day. Standard library only.

    python3 scripts/ext_works.py    # self-check
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

DAYS, MAX = 14, 5
YELLOW, RED_INK, BLUE = "#f5c400", "#e5404f", "#1d4f9e"
SORRY = "ご迷惑をおかけしますが、ご理解とご協力をお願いいたします。"
QUIET = "現在、工事中の区間はありません。全線、平常どおり運転しています。"


def sites(ctx):
    """([(days ago, repo, name as shown, category, new?)] newest first, MAX at most; how many more there are)."""
    day = datetime.date.fromisoformat
    today, names, out = day(ctx["today"]), dict(ctx.get("feat") or []), []
    for r in ctx["repos"]:
        if not r.get("pushed") or r.get("archived"):
            continue
        ago = (today - day(r["pushed"])).days
        if 0 <= ago <= DAYS:
            new = bool(r.get("created")) and (today - day(r["created"])).days <= DAYS
            out.append((ago, r["name"], names.get(r["name"], r["name"]), ctx["cat_of"][r["name"]], new))
    out.sort()
    return out[:MAX], max(0, len(out) - MAX)


def when(ago):
    return "きょう" if ago == 0 else "きのう" if ago == 1 else f"{ago} 日前"


def stripe(x, y, w):
    """The yellow and black band of a construction site. The black must stay black at night: class fx."""
    return (f'<defs><pattern id="wk" width="24" height="10" patternUnits="userSpaceOnUse" patternTransform="skewX(-40)">'
            f'<rect width="24" height="10" fill="{YELLOW}"/><rect class="fx" width="12" height="10" fill="#111"/></pattern></defs>'
            f'<rect x="{x}" y="{y}" width="{w}" height="10" rx="2" fill="url(#wk)"/>')


def worker(x, y):
    """The worker who bows on every such notice, feet at (x, y), bowing to the left."""
    return (f'<g stroke-linecap="round" fill="none"><path d="M{x + 30} {y - 4}V{y - 24}" stroke="{BLUE}" stroke-width="9"/>'
            f'<path d="M{x + 30} {y - 25}L{x + 15} {y - 37}" stroke="{BLUE}" stroke-width="11"/>'
            f'<path d="M{x + 18} {y - 33}V{y - 19}" stroke="{BLUE}" stroke-width="5.5"/></g>'
            f'<rect x="{x + 22}" y="{y - 5}" width="15" height="5" rx="2" fill="#333"/>'
            f'<g transform="rotate(-48 {x + 8} {y - 42})"><circle cx="{x + 8}" cy="{y - 42}" r="7.5" fill="#f0c8a0"/>'
            f'<path d="M{x - 1.5} {y - 43}a9.5 9.5 0 0 1 19 0z" fill="{YELLOW}"/>'
            f'<rect x="{x - 3.5}" y="{y - 44}" width="23" height="2.6" rx="1.3" fill="{YELLOW}"/></g>')


def pill(x, y, w, h, size, new):
    """新設 is a filled red tag; 改良 an outlined one, so that it turns with the ink at night."""
    box = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="{RED_INK}"/>' if new else
           f'<rect x="{x + .75}" y="{y + .75}" width="{w - 1.5}" height="{h - 1.5}" rx="{h / 2 - .75}" fill="none" stroke="#111" stroke-width="1.5"/>')
    return box + (f'<text x="{x + w / 2}" y="{y + h / 2 + size * .36:.1f}" text-anchor="middle" font-size="{size}" font-weight="700" '
                  f'fill="{"#fff" if new else "#111"}">{"新設" if new else "改良"}</text>')


def render(ctx):
    """[(file, width, height, body, label)]: the wide sign and the one for a phone."""
    rows, more = sites(ctx)
    cat = lambda t: ctx["CAT"][t]  # noqa: E731
    md = lambda ago: (datetime.date.fromisoformat(ctx["today"]) - datetime.timedelta(days=ago)).strftime("%m/%d")  # noqa: E731
    foot = (f"ほか {more} 区間でも工事を行っています。" if more else "") + SORRY
    label = "工事のお知らせ。" + (f"最近 {DAYS} 日に作業した区間: " + "、".join(
        f'{shown}({cat(c)[2]}・{"新設" if new else "改良"}・{when(ago)})' for ago, _, shown, c, new in rows)
        + (f"。ほか {more} 区間" if more else "") if rows else QUIET)

    # ---- wide
    step, top = 40, 100
    H = top + step * max(len(rows), 1) + 46
    out = (f'<g font-family="{GOTH}"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="7" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
           f'<text x="24" y="38" font-size="23" font-weight="700" fill="#111" letter-spacing="4">工事のお知らせ</text>'
           f'<text x="222" y="37" font-size="12" fill="#666" font-family="{MONO}" letter-spacing="2">WORKS NOTICE</text>'
           f'<text x="{W - 24}" y="37" text-anchor="end" font-size="13" font-weight="700" fill="#555">最近 {DAYS} 日に push したリポジトリから自動で作成</text>'
           + stripe(20, 50, W - 40))
    if not rows:
        out += f'<text x="24" y="{top}" font-size="18" font-weight="700" fill="#111">{QUIET}</text>'
    for i, (ago, _, shown, c, new) in enumerate(rows):
        y = top + i * step
        squeeze = ' textLength="370" lengthAdjust="spacingAndGlyphs"' if text_w(shown, 20) > 370 else ""
        out += (pill(24, y - 20, 58, 26, 14, new)
                + f'<text x="98" y="{y}" font-size="20" font-weight="700" fill="#111"{squeeze}>{esc(shown)}</text>'
                f'<circle cx="496" cy="{y - 7}" r="7" fill="{cat(c)[4]}"/>'
                f'<text x="511" y="{y - 1}" font-size="15" font-weight="700" fill="#333">{esc(cat(c)[2])}</text>'
                f'<text x="{W - 24}" y="{y}" text-anchor="end" font-size="16" font-weight="700" fill="#333">{md(ago)}　{when(ago)}</text>'
                f'<rect x="24" y="{y + 13}" width="{W - 48}" height="1" fill="#ccc"/>')
    fy = top + step * max(len(rows), 1) + 6
    out += f'<text x="24" y="{fy}" font-size="13" font-weight="700" fill="#555">{foot}</text>' + worker(W - 70, H - 12) + "</g>"
    wide = ("works.svg", W, H, out, label)

    # ---- phone
    m, y = stripe(20, 56, WM - 40), 106
    if not rows:
        for ln in wrap_px(QUIET, 20, WM - 40):
            m += f'<text x="20" y="{y}" font-size="20" font-weight="700" fill="#111">{ln}</text>'
            y += 28
    for ago, _, shown, c, new in rows:
        m += pill(20, y - 23, 62, 30, 16, new)
        for ln in wrap_px(shown, 22, WM - 96 - 16):
            m += f'<text x="96" y="{y}" font-size="22" font-weight="700" fill="#111">{esc(ln)}</text>'
            y += 28
        m += (f'<circle cx="104" cy="{y - 7}" r="7" fill="{cat(c)[4]}"/>'
              f'<text x="118" y="{y}" font-size="{SMALL}" font-weight="700" fill="#555">{esc(cat(c)[2])}</text>'
              f'<text x="{WM - 20}" y="{y}" text-anchor="end" font-size="{SMALL}" font-weight="700" fill="#555">{md(ago)} {when(ago)}</text>'
              f'<rect x="20" y="{y + 14}" width="{WM - 40}" height="1" fill="#ccc"/>')
        y += 50
    y -= 8
    for ln in wrap_px(foot, SMALL, WM - 40):
        m += f'<text x="20" y="{y}" font-size="{SMALL}" font-weight="700" fill="#555">{ln}</text>'
        y += 25
    Hm = y + 44
    m = f'<g font-family="{GOTH}">' + sign_m(Hm, "工事のお知らせ", "WORKS") + m + worker(WM - 66, Hm - 12) + "</g>"
    return [wide, ("works-m.svg", WM, Hm, m, label)]


def live(ctx):
    for sign in render(ctx):
        save(*sign)
    return {}


if __name__ == "__main__":  # self-check: python3 scripts/ext_works.py
    from xml.dom.minidom import parseString

    mk = lambda name, pushed, created="2026-01-01", **kw: {"name": name, "pushed": pushed, "created": created, **kw}  # noqa: E731
    ctx = {"today": "2026-11-12", "feat": [("b", "Bee <B>")], "CAT": {"APPS": ("apps", "アプリ", "アプリ", "A", "#e5404f", None)},
           "repos": [mk("a", "2026-11-12", "2026-11-10"), mk("b", "2026-11-11"), mk("old", "2026-10-28"), mk("gone", "2026-11-12", archived=True),
                     mk("far", "2026-10-29"), mk("tomorrow", "2026-11-13"), mk("none", "")]}
    ctx["cat_of"] = {r["name"]: "APPS" for r in ctx["repos"]}
    rows, more = sites(ctx)
    assert [(ago, n, new) for ago, n, _, _, new in rows] == [(0, "a", True), (1, "b", False), (14, "far", False)], rows  # 15 days ago is out
    assert rows[1][2] == "Bee <B>" and more == 0 and [when(a) for a in (0, 1, 2)] == ["きょう", "きのう", "2 日前"]
    many = dict(ctx, repos=[mk(f"r{i}", "2026-11-12") for i in range(8)])
    many["cat_of"] = {r["name"]: "APPS" for r in many["repos"]}
    assert (len(sites(many)[0]), sites(many)[1]) == (MAX, 3)
    for c in (ctx, many, dict(ctx, repos=[])):  # also the notice with nothing on it
        for name, w, h, body, text in render(c):
            parseString(f'<svg xmlns="http://www.w3.org/2000/svg">{body}</svg>')
            assert h > 100 and text.startswith("工事のお知らせ。"), (name, h)
    assert QUIET in render(dict(ctx, repos=[]))[0][4] and "ほか 3 区間" in render(many)[0][4]
    print("works ok")
