#!/usr/bin/env python3
"""assets/annual.svg and annual-m.svg: the annual report of the station, on show in December only.
Everything on it is counted from the data: the repos made this year, the repos whose latest release is from
this year, and the contribution calendar from January 1 to today (so until the 31st it says "as of").
update_live.py calls live(ctx) once a day; outside December it puts nothing into README. Standard library only.

    python3 scripts/ext_annual.py    # self-check
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

GREEN_INK, RED_INK = "#00a650", "#e5404f"


def report(ctx):
    """The numbers of the year of ctx["today"], up to that day."""
    today, year = ctx["today"], ctx["today"][:4]
    days = [(d["date"], d["contributionCount"]) for w in ctx["cal"]["weeks"] for d in w["contributionDays"]
            if d["date"][:4] == year and d["date"] <= today]
    best = run = 0
    for _, c in days:
        run = run + 1 if c else 0
        best = max(best, run)
    top = max(days, key=lambda dc: (dc[1], dc[0]), default=("", 0))
    return {
        "year": year, "asof": today,
        "made": sum(r.get("created", "")[:4] == year for r in ctx["repos"]),
        "released": sum(r.get("tag_date", "")[:4] == year for r in ctx["repos"]),
        "total": sum(c for _, c in days), "active": sum(1 for _, c in days if c), "days": len(days), "streak": best,
        "top": top, "months": [sum(c for d, c in days if int(d[5:7]) == m) for m in range(1, 13)],
    }


def tiles(r):
    """[(number, unit, caption)]"""
    top = f'{int(r["top"][0][5:7])}/{int(r["top"][0][8:])}' if r["top"][1] else "-"
    return [(f'{r["made"]:,}', "駅", "新設した駅"), (f'{r["released"]:,}', "駅", "リリースを出した駅"), (f'{r["total"]:,}', "本", "総運行本数"),
            (f'{r["active"]:,}', "日", f'運行した日({r["days"]} 日中)'), (f'{r["streak"]:,}', "日", "最長の連続運行"),
            (top, "", f'最多運行日({r["top"][1]:,} 本)')]


def render(ctx):
    """[(file, width, height, body, label)]: the wide sign and the one for a phone."""
    r = report(ctx)
    ts, months, peak = tiles(r), r["months"], max(r["months"])
    now = int(r["asof"][5:7])
    asof = f'{now} 月 {int(r["asof"][8:])} 日 現在'
    title = f'{r["year"]} 年 年間運行報告'
    label = (f"{title}({asof})。" + "、".join(f"{cap} {num} {unit}".strip() for num, unit, cap in ts)
             + "。月ごとの運行本数: " + "、".join(f"{m} 月 {c:,} 本" for m, c in enumerate(months, 1) if m <= now))
    bar = lambda c, tall: max(2, round(tall * c / peak)) if c and peak else 0  # noqa: E731
    col = lambda c: RED_INK if c == peak and peak else GREEN_INK  # noqa: E731

    # ---- wide: six numbers in a row, the twelve months under them
    H, slot, base = 352, (W - 48) / 6, 306
    out = (f'<g font-family="{GOTH}"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="7" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
           f'<text x="24" y="38" font-size="23" font-weight="700" fill="#111" letter-spacing="3">{title}</text>'
           f'<text x="{40 + text_w(title, 23) + 3 * len(title):.0f}" y="37" font-size="12" fill="#666" font-family="{MONO}" letter-spacing="2">ANNUAL REPORT</text>'
           f'<text x="{W - 24}" y="37" text-anchor="end" font-size="13" font-weight="700" fill="#555">{asof}。GitHub の記録から自動で作成</text>'
           f'<rect x="20" y="52" width="{W - 40}" height="3" fill="{GREEN_INK}"/>')
    for i, (num, unit, cap) in enumerate(ts):
        cx = 24 + slot * (i + .5)
        out += (f'<text x="{cx:.0f}" y="112" text-anchor="middle" font-weight="800" fill="#111"><tspan font-size="36">{num}</tspan>'
                f'<tspan font-size="15" dx="3">{unit}</tspan></text>'
                f'<text x="{cx:.0f}" y="138" text-anchor="middle" font-size="12.5" font-weight="700" fill="#666">{cap}</text>')
        if i:
            out += f'<rect x="{24 + slot * i:.0f}" y="78" width="1" height="66" fill="#ccc"/>'
    slot = (W - 48) / 12
    out += f'<rect x="24" y="{base}" width="{W - 48}" height="1.5" fill="#999"/>'
    for m, c in enumerate(months, 1):
        cx, h = 24 + slot * (m - .5), bar(c, 112)
        out += f'<text x="{cx:.0f}" y="{base + 22}" text-anchor="middle" font-size="13" font-weight="700" fill="{"#555" if m <= now else "#aaa"}">{m} 月</text>'
        if m <= now:
            out += (f'<rect x="{cx - 20:.0f}" y="{base - h}" width="40" height="{h}" rx="2" fill="{col(c)}"/>'
                    f'<text x="{cx:.0f}" y="{base - h - 6}" text-anchor="middle" font-size="12.5" font-weight="700" fill="#333" font-family="{MONO}">{c:,}</text>')
    wide = ("annual.svg", W, H, out + "</g>", label)

    # ---- phone: the numbers two by two, then the months
    m_ = f'<text x="20" y="72" font-size="{SMALL}" font-weight="700" fill="#555">{asof}(自動で作成)</text><rect x="20" y="84" width="{WM - 40}" height="3" fill="{GREEN_INK}"/>'
    for i, (num, unit, cap) in enumerate(ts):
        cx, y = 20 + (WM - 40) / 2 * (i % 2 + .5), 138 + i // 2 * 96
        m_ += (f'<text x="{cx:.0f}" y="{y}" text-anchor="middle" font-weight="800" fill="#111"><tspan font-size="38">{num}</tspan>'
               f'<tspan font-size="{SMALL}" dx="3">{unit}</tspan></text>'
               f'<text x="{cx:.0f}" y="{y + 28}" text-anchor="middle" font-size="{SMALL}" font-weight="700" fill="#666">{cap}</text>')
    base, slot = 138 + 3 * 96 + 110, (WM - 40) / 12
    m_ += f'<rect x="20" y="{base}" width="{WM - 40}" height="1.5" fill="#999"/>'
    for m, c in enumerate(months, 1):
        cx, h = 20 + slot * (m - .5), bar(c, 110)
        m_ += f'<text x="{cx:.0f}" y="{base + 24}" text-anchor="middle" font-size="{SMALL}" font-weight="700" fill="{"#555" if m <= now else "#aaa"}">{m}</text>'
        if m <= now:
            m_ += f'<rect x="{cx - 11:.0f}" y="{base - h}" width="22" height="{h}" rx="2" fill="{col(c)}"/>'
    most = f"月ごとの運行本数。最多は {months.index(peak) + 1} 月の {peak:,} 本" if peak else "月ごとの運行本数"
    m_ += f'<text x="20" y="{base + 56}" font-size="{SMALL}" font-weight="700" fill="#555">{most}</text>'
    Hm = base + 76
    phone = ("annual-m.svg", WM, Hm, f'<g font-family="{GOTH}">' + sign_m(Hm, title, "ANNUAL", 24) + m_ + "</g>", label)
    return [wide, phone]


def live(ctx):
    if ctx["today"][5:7] != "12":
        return {"ANNUAL": ""}
    try:  # an extra for one month of the year must not stop the daily run
        signs = render(ctx)
        for sign in signs:
            save(*sign)
    except Exception as e:  # noqa: BLE001
        print(f"annual report: {type(e).__name__} {e}")
        return {"ANNUAL": ""}
    return {"ANNUAL": '<picture><source media="(max-width: 600px)" srcset="assets/annual-m.svg">'
                      f'<img src="assets/annual.svg" width="100%" alt="{esc(signs[0][4])}"></picture>'}


if __name__ == "__main__":  # self-check: python3 scripts/ext_annual.py
    import datetime
    from xml.dom.minidom import parseString

    d0 = datetime.date(2025, 12, 20)  # the calendar starts in the year before, as the real one does
    counts = [0 if i % 7 == 3 else 1 + i % 5 for i in range(361)]
    counts[100] = 40
    cal = {"weeks": [{"contributionDays": [{"date": (d0 + datetime.timedelta(days=i)).isoformat(), "contributionCount": c}
                                           for i, c in list(enumerate(counts))[k:k + 7]]} for k in range(0, 361, 7)]}
    ctx = {"today": "2026-12-15", "cal": cal, "repos": [{"created": "2026-03-01", "tag_date": "2026-04-01"}, {"created": "2025-12-25", "tag_date": ""},
                                                       {"created": "2026-11-01", "tag_date": "2025-12-30"}, {}]}
    r = report(ctx)
    year = [(d0 + datetime.timedelta(days=i), c) for i, c in enumerate(counts) if (d0 + datetime.timedelta(days=i)).year == 2026]
    assert (r["made"], r["released"], r["days"]) == (2, 1, 349), r  # Jan 1 to Dec 15
    assert r["total"] == sum(c for _, c in year) == sum(r["months"]) and r["active"] == sum(1 for _, c in year if c) and r["streak"] == 6
    assert r["top"] == ((d0 + datetime.timedelta(days=100)).isoformat(), 40) and tiles(r)[5][0] == "3/30", r["top"]
    for c in (ctx, dict(ctx, cal={"weeks": []}, repos=[])):  # also a year with nothing in it
        for name, w, h, body, text in render(c):
            parseString(f'<svg xmlns="http://www.w3.org/2000/svg">{body}</svg>')
            assert h > 300 and text.startswith("2026 年 年間運行報告(12 月 15 日 現在)。"), (name, h, text)
    assert tiles(report(dict(ctx, cal={"weeks": []})))[5][0] == "-"
    assert live(dict(ctx, today="2026-11-30")) == {"ANNUAL": ""} and live(dict(ctx, today="2027-01-01")) == {"ANNUAL": ""}
    print("annual ok")
