#!/usr/bin/env python3
"""The loop line that visitors move together ("みんなで動かす列車"). Standard library only.

A visitor opens an issue titled "train: 1", "train: 2" or "train: 3" (the signs in README do
that). .github/workflows/train.yml then runs `python3 scripts/ext_train.py move`, which moves
the train, redraws assets/train.svg and prints the fixed sentence the workflow answers with.

    python3 scripts/ext_train.py                                    # self-check
    TITLE="train: 2" LOGIN=someone python3 scripts/ext_train.py move

The issue title and the login come from strangers. Only step() looks at them, it accepts
nothing but the exact patterns below, and the issue body is never read. The answer is one of
the fixed sentences here; nothing a visitor typed is echoed back.
"""
import contextlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

STATE = os.path.join(ROOT, "data", "train.json")
TITLE_RE = re.compile(r"train: ?[123]")       # used with fullmatch: nothing before, nothing after
LOGIN_RE = re.compile(r"[A-Za-z0-9-]{1,39}")  # a GitHub login. "name[bot]" does not pass, on purpose
KEEP = 5                                      # drivers shown on the board

TRACK = "#00a650"
# The loop, clockwise from the left end. (name, x, y, label dx, label dy, label anchor)
STOPS = [("たこさし", 130, 180, -34, 8, "end")]
STOPS += [(n, 195 + i * 114, 115, 0, -34, "middle") for i, n in enumerate(["ひらめき", "仕様書", "実装", "ビルド", "バグの森"])]
STOPS += [("デバッグ", 716, 180, 34, 8, "start")]
STOPS += [(n, 651 - i * 114, 245, 0, 50, "middle") for i, n in enumerate(["テスト", "レビュー", "リリース", "祝杯", "仮眠"])]
N = len(STOPS)

MSG_BAD = "この題名では運転できません。README の「1 駅」「2 駅」「3 駅」の札から、題名を変えずに出してください。"
MSG_LOGIN = "このアカウント名では運転できません。"
MSG_TWICE = "続けて 2 回は運転できません。ほかの方が運転したあとで、またどうぞ。"


def blank():
    return {"pos": 0, "laps": 0, "moves": 0, "recent": []}


def load():
    """The state file, cleaned. It is only written by this script, but it is drawn, so trust nothing in it."""
    if not os.path.exists(STATE):
        return blank()
    with open(STATE, encoding="utf-8") as f:
        raw = json.load(f)
    recent = [{"login": r["login"], "steps": int(r["steps"]), "to": int(r["to"])} for r in raw.get("recent", [])
              if LOGIN_RE.fullmatch(str(r.get("login"))) and int(r.get("steps", 0)) in (1, 2, 3) and 0 <= int(r.get("to", -1)) < N]
    return {"pos": int(raw["pos"]) % N, "laps": max(int(raw["laps"]), 0), "moves": max(int(raw["moves"]), 0), "recent": recent[:KEEP]}


def step(state, title, login):
    """(new state, the sentence to answer with). Anything that is not exactly right leaves the state as it is."""
    if not isinstance(title, str) or not TITLE_RE.fullmatch(title):
        return state, MSG_BAD
    if not isinstance(login, str) or not LOGIN_RE.fullmatch(login):
        return state, MSG_LOGIN
    if state["recent"] and state["recent"][0]["login"].lower() == login.lower():  # logins are case-insensitive
        return state, MSG_TWICE
    n = int(title[-1])
    pos = state["pos"] + n
    new = {"pos": pos % N, "laps": state["laps"] + pos // N, "moves": state["moves"] + 1,
           "recent": ([{"login": login, "steps": n, "to": pos % N}] + state["recent"])[:KEEP]}
    lap = "環状線をひと回りしました。" if pos >= N else ""
    return new, (f"列車を {n} 駅進めました。{lap}ただいま「{STOPS[new['pos']][0]}」駅、{new['laps'] + 1} 周目です。"
                 "ご乗車ありがとうございました。絵が変わるまで数分かかることがあります。")


def draw(state):
    name, tx, ty = STOPS[state["pos"]][:3]
    lap = state["laps"] + 1
    out = (f'<style>@keyframes tp{{50%{{opacity:.1}}}}.tp{{animation:tp 1.6s steps(1) infinite}}'
           f'@media (prefers-reduced-motion:reduce){{.tp{{animation:none}}}}</style>'
           f'<g font-family="{GOTH}"><rect x="1" y="1" width="{W - 2}" height="308" rx="7" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
           f'<text x="24" y="38" font-size="23" font-weight="700" fill="#111" letter-spacing="3">たこさし環状線</text>'
           f'<text x="{W - 24}" y="37" text-anchor="end" font-size="12" fill="#666" font-family="{MONO}" letter-spacing="2">LOOP LINE</text>'
           f'<rect x="130" y="115" width="586" height="130" rx="65" fill="none" stroke="{TRACK}" stroke-width="10"/>'
           f'<path d="M246 108l12 7l-12 7zM480 108l12 7l-12 7zM600 252l-12-7l12-7zM366 252l-12-7l12-7z" fill="#fff"/>'
           f'<text x="423" y="160" text-anchor="middle" font-size="14" font-weight="700" fill="#666">ただいまの停車駅</text>'
           f'<text x="423" y="198" text-anchor="middle" font-size="32" font-weight="700" fill="#111" letter-spacing="2">{name}</text>'
           f'<text x="423" y="224" text-anchor="middle" font-size="15" font-weight="700" fill="#555">{lap} 周目 ・ のべ {state["moves"]} 回運転</text>')
    for i, (n, x, y, dx, dy, anchor) in enumerate(STOPS):
        here = i == state["pos"]
        out += (f'<circle cx="{x}" cy="{y}" r="10" fill="#fff" stroke="#222" stroke-width="4"/>'
                f'<text x="{x + dx}" y="{y + dy}" text-anchor="{anchor}" font-size="21" font-weight="700" fill="{"#d2283a" if here else "#111"}">{n}</text>')
    out += (f'<g transform="translate({tx} {ty})"><circle class="tp" r="27" fill="none" stroke="#e5404f" stroke-width="4"/>'
            f'<rect x="-21" y="-14" width="42" height="28" rx="7" fill="#e5404f" stroke="#111" stroke-width="3"/>'
            f'<rect x="-14" y="-8" width="11" height="9" rx="1.5" fill="#fff"/><rect x="3" y="-8" width="11" height="9" rx="1.5" fill="#fff"/>'
            f'<circle cx="-11" cy="7" r="2.2" fill="#ffd500"/><circle cx="11" cy="7" r="2.2" fill="#ffd500"/></g></g>')

    y0 = 318
    b = Board("t", LED_X, y0 + 40, LED_COLS, 140)
    w = b.put(F16, "現在", 7, 4, GREEN, invert=True)
    b.put(F16, f"{name}駅", 15 + w, 4, AMBER)
    b.put(F16, f"{lap}周目", 397, 4, AMBER, right=True)
    b.put(F16, f"のべ運転 {state['moves']}回", 6, 24, GREEN)
    b.put(F16, f"全{N}駅", 397, 24, GREEN, right=True)
    for i, r in enumerate(state["recent"][:KEEP]):
        y = 48 + i * 18
        tw = b.put(F16, f"{r['steps']}駅 → {STOPS[r['to']][0]}", 397, y, GREEN, right=True)
        b.put(F16, F16.fit(r["login"], 397 - tw - 16), 6, y, AMBER)
    if not state["recent"]:
        b.put(F16, "まだ運転士がいません。", 6, 48, GREEN)
        b.put(F16, "最初の1人をお待ちしています。", 6, 66, GREEN)
    h = y0 + 40 + b.h + 17
    save("train.svg", W, h, out + casing(W, h, "運転記録", "Drivers", "下の札から Issue を出すと列車が進みます", y=y0) + b.svg() + seam(b, 43),
         f"たこさし環状線。列車は {name} 駅、{lap} 周目、のべ {state['moves']} 回運転。"
         + (f"直近の運転士: {'、'.join(esc(r['login']) for r in state['recent'])}" if state["recent"] else ""))


def static():
    """The three signs that open the issue, and the sign on top of the block."""
    for n in (1, 2, 3):
        body = (f'<rect x="1" y="1" width="268" height="62" rx="7" fill="#1d4f9e" stroke="#0d2a57" stroke-width="2"/>'
                f'<circle cx="32" cy="32" r="21" fill="#fff"/>'
                f'<text x="32" y="41" text-anchor="middle" font-family="{MONO}" font-size="26" font-weight="800" fill="#1d4f9e">{n}</text>'
                f'<text x="64" y="26" font-family="{GOTH}" font-size="12" font-weight="700" fill="#fff" opacity=".85" letter-spacing="1">列車を進める</text>'
                f'<text x="64" y="50" font-family="{GOTH}" font-size="21" font-weight="700" fill="#fff">{n} 駅すすむ</text>'
                f'<path d="M226 32h26m-10-10l10 10l-10 10" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
        save(f"train-go-{n}.svg", 270, 64, body, f"列車を {n} 駅進める")
    plate("train-plate.svg", TRACK, "参", "加", "みんなで動かす列車", "LOOP LINE")


def live(ctx):
    draw(load())
    return {}


def selfcheck():
    s = blank()
    for bad in ["", "train:", "train: 4", "train: 0", "train:  1", "Train: 1", " train: 1", "train: 1 ", "train: 1\n",
                "train: 12", "train: 1; rm -rf /", "train: $(id)", "x train: 1", None, 1]:
        assert step(s, bad, "alice") == (s, MSG_BAD), bad
    for bad in ["", "a b", "evil[bot]", "<svg>", "a" * 40, "名前", "$(id)", "a\n", None]:
        assert step(s, "train: 1", bad) == (s, MSG_LOGIN), bad
    s1, msg = step(s, "train: 3", "alice")
    assert (s1["pos"], s1["laps"], s1["moves"]) == (3, 0, 1) and "alice" not in msg and s == blank()  # input untouched
    assert step(s1, "train:2", "Alice") == (s1, MSG_TWICE)        # same person twice in a row, any letter case
    s2, _ = step(s1, "train:2", "bob-2")
    assert s2["pos"] == 5 and s2["recent"][0] == {"login": "bob-2", "steps": 2, "to": 5}
    t = {"pos": N - 1, "laps": 4, "moves": 9, "recent": []}
    t2, msg = step(t, "train: 2", "carol")
    assert (t2["pos"], t2["laps"]) == (1, 5) and "ひと回り" in msg  # wraps around and counts the lap
    for i in range(12):
        s2, _ = step(s2, "train: 1", f"user{i}")
    assert len(s2["recent"]) == KEEP and s2["recent"][0]["login"] == "user11" and s2["moves"] == 14
    print("train ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["move"]:
        old = load()
        new, answer = step(old, os.environ.get("TITLE", ""), os.environ.get("LOGIN", ""))
        if new is not old:
            os.makedirs(os.path.dirname(STATE), exist_ok=True)
            with open(STATE, "w", encoding="utf-8", newline="\n") as f:
                json.dump(new, f, ensure_ascii=False, indent=1)
                f.write("\n")
            with contextlib.redirect_stdout(sys.stderr):  # keep stdout for the answer alone
                draw(new)
        sys.stdout.buffer.write(answer.encode("utf-8") + b"\n")  # UTF-8 whatever the console is set to
    else:
        selfcheck()
