#!/usr/bin/env python3
"""The commuter pass ("定期券"): the current run of days with a contribution, printed like a season ticket.

It is valid from the day the run began until its last day. A day without a contribution ends the run,
and the pass is then stamped 期限切れ with the number of days off. Same paper and same dot printing as
the ticket of ext_ticket.py, so the two can sit side by side. Standard library only.

    python3 scripts/ext_commuter.py      # self-check
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403
from ext_ticket import INK, STAMP, TH, TW, ink  # noqa: E402

BAND, PAPER, WAVE, RIM = "#1d4f9e", "#dfe9f3", "#bcd0e6", "#8aa3bf"
NOTES = "経由:毎日のコミット　1日休むと失効"


def dates(cal, cur, idle):
    """(first day of the current run, its last day, the last day with a contribution), each "YYYY-MM-DD" or None.
    cur and idle are ctx["streak"]; like there, an empty today does not count as a day off yet."""
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    past = days[:-1] if days and not days[-1]["contributionCount"] else days
    if cur:
        return past[-cur]["date"], past[-1]["date"], past[-1]["date"]
    return None, None, past[-1 - idle]["date"] if idle < len(past) else None


def dot(date):
    return date.replace("-", ".")


def draw(cur, best, idle, start, end, last, user):
    """(SVG body, label). cur: days in a row now (0 = the pass has run out), best: longest run of the year,
    idle: days since the last contribution."""
    live_ = cur > 0
    band = BAND if live_ else "#6b7078"
    nw = len(str(cur)) * 8 * 4 + 4
    if live_:
        right = [ink(F16, dot(start) + " から", 318, 126, 1.5), ink(F16, dot(end) + " まで", 318, 160, 1.5, bold=True)]
        y2, m2, d2 = end.split("-")
        mark = (f'<g transform="rotate(-9 520 82)" opacity=".82"><circle cx="520" cy="82" r="30" fill="none" stroke="{STAMP}" stroke-width="3"/>'
                f'<path d="M493 73h54M493 93h54" stroke="{STAMP}" stroke-width="2"/>'
                + ink(F12, "継続中", 502, 58, 1, STAMP)[0] + ink(F12, f"{y2[2:]}.{m2}.{d2}", 496, 77, 1, STAMP)[0]
                + ink(F12, "有効", 508, 96, 1, STAMP)[0] + "</g>")
        label = f"有効期間 {start} から {end}"
    else:
        right = [ink(F16, "最終乗車 " + (dot(last) if last else "記録なし"), 318, 126, 1.5),
                 ink(F16, f"{idle} 日間 お休み中", 318, 160, 1.5, bold=True)]  # not "日目": 目 next to 日 reads as 日日 at this size
        # Pressed where the round stamp of a valid pass goes, so nothing printed is covered.
        mark = (f'<g transform="rotate(-6 510 81)" opacity=".85"><rect x="442" y="58" width="136" height="46" rx="5" fill="none" stroke="{STAMP}" stroke-width="4"/>'
                + ink(F16, "期限切れ", 446, 65, 2, STAMP, bold=True)[0] + "</g>")
        label = f"期限切れ。休み {idle} 日目" + (f"、最後の活動は {last}" if last else "")
    out = "".join(p for p, _ in [
        ink(F16, "定期券", 24, 9, 2, "#fff", bold=True),
        ink(F16, "通勤", 136, 17, 1, "#fff"),
        ink(F16, "たこさし駅発行", 576, 17, 1, "#fff", right=True),
        ink(F16, "たこさし", 24, 58, 3, bold=True),
        ink(F16, "⇔", 228, 58, 3, bold=True),
        ink(F16, "GitHub", 292, 58, 3, bold=True),
        ink(F16, "連続", 24, 150, 2, bold=True),
        ink(F16, str(cur), 100, 122, 4, bold=True),
        ink(F16, "日", 104 + nw, 150, 2, bold=True),
        *right,
        ink(F12, f"{NOTES}　1年の最長 {best}日", 24, 214, 1.5),
        ink(F16, f"{user} 様", 24, 252, 1.5),
        ink(F16, "たこさし駅 自動発券機", 576, 256, 1, right=True),
    ])
    body = (f'<defs><pattern id="cw" width="24" height="12" patternUnits="userSpaceOnUse"><path d="M0 6q6-7 12 0t12 0" fill="none" stroke="{WAVE}" stroke-width="1.3"/></pattern>'
            f'<clipPath id="cc"><rect x="1" y="1" width="{TW - 2}" height="{TH - 2}" rx="14"/></clipPath></defs>'
            f'<g clip-path="url(#cc)"><rect width="{TW}" height="{TH}" fill="{PAPER}"/><rect width="{TW}" height="{TH}" fill="url(#cw)"/>'
            f'<rect width="{TW}" height="48" fill="{band}"/>'
            f'<rect x="24" y="112" width="552" height="1.5" fill="{INK}" opacity=".55"/>'
            f'<path d="M24 204H576" stroke="{INK}" stroke-width="1.5" stroke-dasharray="3 3" opacity=".7"/>'
            f'<rect x="300" y="122" width="1.5" height="68" fill="{INK}" opacity=".35"/>'
            f'<g fill="none" stroke-width="1" shape-rendering="crispEdges">{out}{mark}</g></g>'
            f'<rect x="1" y="1" width="{TW - 2}" height="{TH - 2}" rx="14" fill="none" stroke="{RIM}" stroke-width="1.5"/>')
    return body, f"定期券。たこさし ⇔ GitHub、連続 {cur} 日。{label}。1 年の最長 {best} 日"


def live(ctx):
    cur, best, idle = ctx["streak"]
    save("commuter.svg", TW, TH, *draw(cur, best, idle, *dates(ctx["cal"], cur, idle), ctx["USER"]))
    return {}


def selfcheck():
    cal = lambda counts: {"weeks": [{"contributionDays": [  # noqa: E731
        {"date": f"2026-11-{i + 1:02d}", "contributionCount": c} for i, c in enumerate(counts)]}]}
    assert dates(cal([0, 1, 2, 3]), 3, 0) == ("2026-11-02", "2026-11-04", "2026-11-04")
    assert dates(cal([0, 1, 2, 0]), 2, 0) == ("2026-11-02", "2026-11-03", "2026-11-03")  # today is still empty: the run holds
    assert dates(cal([1, 0, 0, 0]), 0, 2) == (None, None, "2026-11-01")                  # two days off, then today
    assert dates(cal([0, 0, 0]), 0, 2) == (None, None, None)                             # nothing in the whole year
    for cur in (1, 28, 300, 366):  # the number and the 日 behind it stay left of the dates
        assert 104 + len(str(cur)) * 32 + 4 + 32 <= 296, cur
        body, label = draw(cur, 366, 0, "2026-01-01", "2026-11-11", "2026-11-11", "takosasi-dev")
        assert f"連続 {cur} 日" in label and "期限切れ" not in label
    assert "期限切れ" in draw(0, 12, 5, None, None, "2026-11-06", "takosasi-dev")[1]
    draw(0, 0, 3, None, None, None, "takosasi-dev")  # a year with nothing in it still prints
    for font, text in ((F16, "定期券通勤たこさし駅発行⇔連続日からまで最終乗車休み目記録な期限切れ様自動発券機間お中"), (F12, NOTES + "年の最長継続中有効")):
        assert all(font.glyph(ch) != font.glyph("?") for ch in text), text  # every printed character has a glyph
    print("commuter ok")


if __name__ == "__main__":
    selfcheck()
