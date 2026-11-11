#!/usr/bin/env python3
"""assets/service.svg: the service status board. One row per line (= category), the way a railway
lists its lines; the status of a line comes from the automatic tests (CI) of its repos.
update_live.py calls live(ctx) once a day. Standard library only.

    python3 scripts/ext_status.py    # self-check
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

# what the board says for a line, worst first: (key, word, colour)
DELAY, ADJUST, OK, NONE = ("delay", "遅延", RED), ("adjust", "調整中", AMBER), ("ok", "平常運転", GREEN), ("none", "情報なし", AMBER)


def line_state(repos):
    """One line from its repos. A failing test anywhere delays the line; a running one is "being adjusted";
    all green is normal service; a line whose repos have no CI has nothing to report. Archived repos do not count."""
    ci = {r.get("ci") or "" for r in repos if not r.get("archived")}
    if ci & {"FAILURE", "ERROR"}:
        return DELAY
    if ci & {"PENDING", "EXPECTED"}:
        return ADJUST
    return OK if "SUCCESS" in ci else NONE


def live(ctx):
    CAT, groups = ctx["CAT"], ctx["groups"]
    states = {t: line_state(groups.get(t, [])) for t in CAT}
    live_repos = [r for r in ctx["repos"] if not r.get("archived")]
    late = sorted(r["name"] for r in live_repos if r.get("ci") in ("FAILURE", "ERROR"))
    busy = sorted(r["name"] for r in live_repos if r.get("ci") in ("PENDING", "EXPECTED"))
    with_ci = sum(1 for r in live_repos if r.get("ci"))

    b = Board("v", LED_X, 40, LED_COLS, 128)
    if late:
        tag, col, head = "遅延", RED, f"{sum(s is DELAY for s in states.values())}路線で遅れが出ています"
    elif busy:
        tag, col, head = "調整中", AMBER, "一部の列車を点検しています"
    elif with_ci:
        tag, col, head = "平常", GREEN, "全線 平常どおり運転しています"
    else:
        tag, col, head = "休止", AMBER, "運行情報はありません"
    w = b.put(F16, tag, 7, 4, col, invert=True, blink=bool(late))
    cw = b.put(F16, f"CI {with_ci}本", 397, 4, GREEN, right=True)
    b.put(F16, F16.fit(head, 397 - cw - 8 - (15 + w)), 15 + w, 4, col)
    for i, title in enumerate(CAT):
        _, _, ja, sym, line_col, _ = CAT[title]
        x, y = 5 + (i % 2) * 201, 28 + (i // 2) * 20  # 20 rows apart: the symbol tags are 18 tall and must not touch
        key, word, scol = states[title]
        sw = b.put(F16, sym, x + 2, y, line_col, invert=True)
        rows = F16.rows(word)
        b.raw(rows, x + 190 - len(rows[0]), y, scol, blink=key == "delay", op=.38 if key == "none" else 1)
        b.put(F16, F16.fit(ja, 190 - len(rows[0]) - 2 - (sw + 4)), x + sw + 4, y, AMBER)
    tick = ""
    if late:
        tick += f'遅延: {"、".join(late)}(自動テストが失敗しています)。　　'
    if busy:
        tick += f'調整中: {"、".join(busy)}(自動テストを実行中です)。　　'
    if not late and not busy:
        tick += "現在、遅れの情報はありません。　　"
    tick += f"自動テストつきの列車は {with_ci} 本です。　　　"
    b.ticker(F16, tick, 108, AMBER)
    h = 40 + b.h + 17
    save("service.svg", W, h,
         casing(W, h, "列車運行情報", "Service status", "各リポジトリの自動テスト(CI)の結果") + b.svg() + seam(b, 23) + seam(b, 105),
         f"列車運行情報。{head}。" + "、".join(f"{CAT[t][2]}: {states[t][1]}" for t in CAT) + "。" + tick.strip())
    return {}


if __name__ == "__main__":  # self-check: python3 scripts/ext_status.py
    r = lambda ci, archived=False: {"ci": ci, "archived": archived}  # noqa: E731
    assert line_state([]) is NONE and line_state([r(""), r("")]) is NONE and line_state([{}]) is NONE
    assert line_state([r("SUCCESS"), r("")]) is OK
    assert line_state([r("SUCCESS"), r("PENDING")]) is ADJUST and line_state([r("EXPECTED")]) is ADJUST
    assert line_state([r("SUCCESS"), r("PENDING"), r("FAILURE")]) is DELAY and line_state([r("ERROR")]) is DELAY
    assert line_state([r("FAILURE", archived=True), r("SUCCESS")]) is OK  # a closed line does not delay anyone
    assert line_state([r("SOMETHING_NEW")]) is NONE                      # a state this file does not know is not reported as fine
    print("status ok")
