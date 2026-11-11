#!/usr/bin/env python3
"""The station timetable made of real commit times ("時刻表"). Standard library only.

ctx["commits"] holds when the public commits of the last four weeks were written (Japan time).
Each one is a departure: the row is the hour, the number is the minute, and like a real timetable
there is one column for weekdays and one for Saturdays and Sundays (holidays are not looked up).
The day starts at 5:00, so a commit at 1:00 on Saturday still belongs to Friday.

    python3 scripts/ext_timetable.py     # self-check
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

START = 5            # the hour a day begins at
PER, LINES = 10, 2   # minutes on one line of a cell, lines in a cell at most
LH, PITCH = 29, 37   # line height, distance between two minutes
COLS = ((24, "平日", "#1d4f9e"), (449, "土・休日", "#c8342b"))  # (left edge, heading, colour); each is 373 wide
HOUR_X, HOUR_W, COL_W = 397, 52, 373
ORDER = [(START + i) % 24 for i in range(24)]
NONE = "この期間の運転はありません"


def table(commits):
    """({(hour, 0 weekday / 1 weekend): sorted minutes}, the hours to print, in the order of a day).
    The hours run from the first one that has a commit to the last one that has; nothing in between is skipped."""
    cells = {}
    for c in commits:
        try:
            t = datetime.datetime.fromisoformat(c)
        except (TypeError, ValueError):
            continue
        weekend = (t - datetime.timedelta(hours=START)).weekday() >= 5
        cells.setdefault((t.hour, int(weekend)), []).append(t.minute)
    for ms in cells.values():
        ms.sort()
    used = [i for i, h in enumerate(ORDER) if (h, 0) in cells or (h, 1) in cells]
    return cells, (ORDER[used[0]:used[-1] + 1] if used else [])


def shown(ms, per=PER):
    """(the minutes printed, how many are left out). A cell that is too full ends with "ほか n 本" in its last two places."""
    # ponytail: the left-out ones are the latest of the hour, so the last train's mark is not drawn in a cell this full.
    keep = ms if len(ms) <= per * LINES else ms[:per * LINES - 2]
    return keep, len(ms) - len(keep)


def layout(total):
    """(x of the hour column, [(column 0 weekday / 1 weekend, left edge, width, minutes on a line)]).
    Two columns with the hours between them; when only one of them has any train, that one alone, full width,
    with the hours on the left (half a board saying "no trains" is a waste of the board)."""
    if bool(total[0]) != bool(total[1]):
        x = 24 + HOUR_W
        return 24, [(0 if total[0] else 1, x, 822 - x, (822 - x - 6) // PITCH)]
    return HOUR_X, [(c, COLS[c][0], COL_W, PER) for c in (0, 1)]


def ends(cells, hours, col):
    """((hour, minute) of the first train, (hour, minute) of the last train) of one column, or (None, None)."""
    hs = [h for h in hours if (h, col) in cells]
    return ((hs[0], cells[hs[0], col][0]), (hs[-1], cells[hs[-1], col][-1])) if hs else (None, None)


def draw(commits, today):
    cells, hours = table(commits)
    total = [sum(len(ms) for (_, c), ms in cells.items() if c == col) for col in (0, 1)]
    n = sum(total)
    rows = hours or ORDER[:6]  # nothing at all: a short empty table
    per_hour = {h: len(cells.get((h, 0), [])) + len(cells.get((h, 1), [])) for h in rows}
    peak = max(rows, key=lambda h: per_hour[h]) if n else None  # the earliest one on a tie
    day = datetime.date.fromisoformat(today)
    since = day - datetime.timedelta(days=27)
    period = f"{since.month}/{since.day} 〜 {day.month}/{day.day}"

    y0 = 102
    out, y = "", y0
    hour_x, cols = layout(total)
    for i, h in enumerate(rows):
        lines = max(1, *(-(-min(len(cells.get((h, c), [])), per * LINES) // per) for c, _, _, per in cols))
        hgt = lines * LH + 4
        if i % 2:
            out += f'<rect x="24" y="{y}" width="798" height="{hgt}" fill="#e9eae3"/>'
        out += (f'<rect x="{hour_x}" y="{y}" width="{HOUR_W}" height="{hgt}" fill="{"#ffd500" if h == peak else "#d9dcd3"}"/>'
                f'<text x="{hour_x + HOUR_W / 2}" y="{y + hgt / 2 + 7}" font-size="20" font-weight="800" fill="#111">{h}</text>')
        for col, x, _, per in cols:
            ms, more = shown(cells.get((h, col), []), per)
            first, last = ends(cells, hours, col)
            for k, m in enumerate(ms):
                cx, by = x + 20 + (k % per) * PITCH, y + 24 + (k // per) * LH
                mark = "#111" if (h, m) == first and k == 0 else "#d2283a" if (h, m) == last and k == len(ms) - 1 and not more else ""
                if mark:
                    out += f'<rect x="{cx - 16}" y="{by - 21}" width="32" height="26" rx="4" fill="{mark}"/>'
                white = ' fill="#fff"' if mark else ""
                out += f'<text x="{cx}" y="{by}"{white}>{m:02d}</text>'
            if more:
                out += (f'<text x="{x + 20 + (per - 1.5) * PITCH}" y="{y + 22 + (LINES - 1) * LH}" font-size="13" fill="#555">ほか {more} 本</text>')
        y += hgt
        out += f'<rect x="24" y="{y - .5}" width="798" height="1" fill="#c3c6bd"/>'
    for col, x, w, _ in cols:
        if not total[col]:
            out += f'<text x="{x + w / 2}" y="{(y0 + y) / 2 + 5}" font-size="15" font-weight="400" fill="#888">{NONE}</text>'
    H = y + 46
    heads = "".join(f'<rect x="{x}" y="74" width="{w}" height="28" fill="{COLS[col][2]}"/>'
                    f'<text x="{x + w / 2}" y="94" font-size="16" fill="#fff" letter-spacing="4">{COLS[col][1]}</text>' for col, x, w, _ in cols)
    if len(cols) == 1:  # say on the board why the other column is not there
        other = COLS[1 - cols[0][0]][1]
        heads += f'<text x="810" y="93" text-anchor="end" font-size="12" font-weight="400" fill="#fff" opacity=".9">{other}の運転はありません</text>'
    legend = (f'<g font-size="12.5" font-weight="400" fill="#444" text-anchor="start">'
              f'<rect x="24" y="{y + 14}" width="26" height="18" rx="4" fill="#111"/><text x="56" y="{y + 28}">始発</text>'
              f'<rect x="96" y="{y + 14}" width="26" height="18" rx="4" fill="#d2283a"/><text x="128" y="{y + 28}">終電</text>'
              f'<rect x="168" y="{y + 14}" width="26" height="18" fill="#ffd500"/><text x="200" y="{y + 28}">いちばん混む時間帯</text>'
              f'<text x="822" y="{y + 28}" text-anchor="end">数字は、コミットした「分」。1 つが 1 本(日本時間)</text></g>')
    body = (f'<g font-family="{GOTH}"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="7" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
            f'<text x="24" y="38" font-size="23" font-weight="700" fill="#111" letter-spacing="4">時刻表</text>'
            f'<text x="112" y="37" font-size="12" fill="#666" font-family="{MONO}" letter-spacing="2">COMMIT TIMETABLE</text>'
            f'<text x="{W - 24}" y="37" text-anchor="end" font-size="13" font-weight="700" fill="#333">過去 4 週間の公開コミット {n} 本</text>'
            f'<text x="24" y="62" font-size="13" fill="#555">たこさし駅　コミット線　発車時刻</text>'
            f'<text x="{W - 24}" y="62" text-anchor="end" font-size="12" fill="#666" font-family="{MONO}">{period}</text>'
            f'<g text-anchor="middle" font-weight="700" fill="#111" style="font-variant-numeric:tabular-nums">{heads}'
            f'<rect x="{hour_x}" y="74" width="{HOUR_W}" height="28" fill="#222"/>'
            f'<text x="{hour_x + HOUR_W / 2}" y="94" font-size="15" fill="#fff">時</text>'
            f'<g font-size="22">{out}</g></g>'
            f'<rect x="24" y="74" width="798" height="{y - 74}" fill="none" stroke="#8a9099" stroke-width="1.5"/>{legend}</g>')
    label = f"時刻表。過去 4 週間({period})の公開コミット {n} 本を、コミットした時刻で並べた駅の時刻表。平日 {total[0]} 本、土・休日 {total[1]} 本。"
    if n:
        both = [e for c in (0, 1) if total[c] for e in ends(cells, hours, c)]
        f, l = (pick(both, key=lambda e: (ORDER.index(e[0]), e[1])) for pick in (min, max))
        label += f"いちばん混むのは {peak} 時台の {per_hour[peak]} 本。始発 {f[0]}:{f[1]:02d}、終電 {l[0]}:{l[1]:02d}。"
    else:
        label += NONE + "。"
    save("timetable.svg", W, H, body, label)
    return label


def live(ctx):
    draw(ctx.get("commits") or [], ctx["today"])
    return {}


def selfcheck():
    # 2026-11-13 is a Friday, 11-14 a Saturday, 11-16 a Monday.
    cells, hours = table(["2026-11-13T09:05", "2026-11-13T09:01", "2026-11-14T01:30",   # Sat 1:30 is still Friday's last train
                          "2026-11-14T12:00", "2026-11-16T02:10", "junk", None])         # Mon 2:10 belongs to Sunday
    assert cells == {(9, 0): [1, 5], (1, 0): [30], (12, 1): [0], (2, 1): [10]}, cells
    assert hours == [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0, 1, 2], hours  # no gap, 0-2 after 23
    assert ends(cells, hours, 0) == ((9, 1), (1, 30)) and ends(cells, hours, 1) == ((12, 0), (2, 10))
    assert table([]) == ({}, []) and ends({}, [], 0) == (None, None)
    full = PER * LINES  # a full cell is printed whole; one more and the last two places go to "ほか n 本"
    assert shown(list(range(full))) == (list(range(full)), 0) and shown(list(range(40))) == (list(range(full - 2)), 42 - full)
    # both columns when both have trains or neither has; one full-width column when only one has
    assert [c for c, *_ in layout([3, 2])[1]] == [0, 1] == [c for c, *_ in layout([0, 0])[1]]
    for total, col in (([3, 0], 0), ([0, 2], 1)):
        hx, [(c, x, w, per)] = layout(total)
        assert c == col and hx + HOUR_W == x and x + w == 822 and x + 20 + (per - 1) * PITCH + 16 <= 822 and per > PER
    print("timetable ok")


if __name__ == "__main__":
    selfcheck()
