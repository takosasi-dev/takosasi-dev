#!/usr/bin/env python3
"""The message board of the station ("伝言板"): a visitor leaves one of eight fixed lines. Standard library only.

A visitor opens an issue titled "board: 1" ... "board: 8" (the signs in README do that).
.github/workflows/board.yml then runs `python3 scripts/ext_board.py post`, which keeps the line in
data/board.json, redraws assets/board.svg and prints the fixed sentence the workflow answers with.

    python3 scripts/ext_board.py                                    # self-check
    TITLE="board: 3" LOGIN=someone python3 scripts/ext_board.py post

The issue title and the login come from strangers. Only post() looks at them, it accepts nothing but
the exact patterns below, and the issue body is never read. What lands on the board is the line the
number stands for, never a word the visitor typed; the only thing of theirs that is drawn is the login
after it passed the check. The answer is one of the fixed sentences here.
"""
import contextlib
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403
from ext_ticket import ink  # noqa: E402  text as square dots from the Shinonome glyphs

STATE = os.path.join(ROOT, "data", "board.json")
TITLE_RE = re.compile(r"board: ?[1-8]")       # used with fullmatch: nothing before, nothing after
LOGIN_RE = re.compile(r"[A-Za-z0-9-]{1,39}")  # a GitHub login. "name[bot]" does not pass, on purpose
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
KEEP = 8                                      # lines on the board; one per person
PHRASES = ["見に来ました", "おつかれさまです", "また来ます", "列車を動かしました", "隠し駅を見つけました",
           "応援しています", "ゲームを全部解きました", "Hello from overseas"]

MSG_BAD = "この題名では伝言板に書けません。README の伝言の札から、題名を変えずに出してください。"
MSG_LOGIN = "このアカウント名では伝言板に書けません。"

WOOD, WOOD_EDGE, SLATE = "#8a5a34", "#5e3b1f", "#2c5a43"
CHALK, YELLOW, BLUE = "#f3f2e8", "#ffe27a", "#a9dcf5"
ROW, TOP = 40, 96                 # height of one line, top of the first line
X_DATE, X_TEXT, X_NAME, NAME_W = 30, 132, 506, 320
# The octopus somebody draws in chalk once the board is full: head, eyes, mouth, four legs. 44 wide, in the top right corner.
DOODLE_W = 54
DOODLE = (f'<g transform="translate({W - 72} 13) rotate(-7 22 22)" fill="none" stroke="{CHALK}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" opacity=".85">'
          '<path d="M9 23c-6-12 2-21 13-21s19 9 13 21q-13 5-26 0M16.5 11v3M27.5 11v3M22 17.5a2.3 2.3 0 1 0 .01 0'
          'M11 25c-1 7-3 11-9 9M18 27c0 7-1 11-6 13M26 27c0 7 1 11 6 13M33 25c1 7 3 11 9 9"/></g>')


def blank():
    return {"posts": []}


def clean(raw):
    """A state with nothing in it that was not checked. The file is only written by this script, but it is drawn, so trust nothing in it."""
    posts, seen = [], set()
    listed = raw.get("posts") if isinstance(raw, dict) else None
    for p in (listed if isinstance(listed, list) else []):
        if (isinstance(p, dict) and isinstance(p.get("login"), str) and LOGIN_RE.fullmatch(p["login"])
                and type(p.get("n")) is int and 1 <= p["n"] <= len(PHRASES)
                and isinstance(p.get("date"), str) and DATE_RE.fullmatch(p["date"]) and p["login"].lower() not in seen):
            seen.add(p["login"].lower())
            posts.append({"login": p["login"], "n": p["n"], "date": p["date"]})
    return {"posts": posts[:KEEP]}


def load():
    if not os.path.exists(STATE):
        return blank()
    with open(STATE, encoding="utf-8") as f:
        return clean(json.load(f))


def post(state, title, login, today):
    """(new state, the sentence to answer with). Anything that is not exactly right leaves the state as it is."""
    if not isinstance(title, str) or not TITLE_RE.fullmatch(title):
        return state, MSG_BAD
    if not isinstance(login, str) or not LOGIN_RE.fullmatch(login):
        return state, MSG_LOGIN
    n = int(title[-1])
    rest = [p for p in state["posts"] if p["login"].lower() != login.lower()]  # logins are case-insensitive: one line a person
    again = "前の伝言と入れ替えました。" if len(rest) < len(state["posts"]) else ""
    new = {"posts": ([{"login": login, "n": n, "date": today}] + rest)[:KEEP]}
    return new, (f"伝言板に「{PHRASES[n - 1]}」と書きました。{again}"
                 "ご利用ありがとうございました。絵が変わるまで数分かかることがあります。")


# --------------------------------------------------------------------------- the picture
def name_scale(login):
    """px per dot for the name: 2 when it fits its column, down to 1 for the longest login (39 letters = 312 dots)."""
    return max(1, int(min(2, NAME_W / F16.width(login)) * 2) / 2)


def draw(state):
    """(SVG body, label, height) of the board: green slate in a wooden frame, the lines in chalk, newest on top."""
    posts = state["posts"]
    rows = max(len(posts), 4)                     # no long empty board while few have written
    bottom = TOP + rows * ROW + 6                 # the lower edge of the slate
    h = bottom + 30
    out = (f'<rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="6" fill="{WOOD}" stroke="{WOOD_EDGE}" stroke-width="2"/>'
           f'<rect x="10" y="10" width="{W - 20}" height="{bottom - 4}" rx="2" fill="{SLATE}" stroke="{WOOD_EDGE}" stroke-width="1.5"/>'
           f'<defs><filter id="bf" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="12"/></filter>'
           f'<clipPath id="bc"><rect x="11" y="11" width="{W - 22}" height="{bottom - 6}"/></clipPath></defs>'
           # where the eraser went over old lines
           f'<g filter="url(#bf)" fill="#fff" opacity=".06" clip-path="url(#bc)"><ellipse cx="250" cy="{TOP + 50}" rx="190" ry="26"/>'
           f'<ellipse cx="620" cy="{bottom - 46}" rx="170" ry="22"/><ellipse cx="700" cy="40" rx="120" ry="16"/></g>'
           # the chalk ledge: three chalks and the eraser
           f'<rect x="10" y="{bottom + 8}" width="{W - 20}" height="12" rx="2" fill="#a26d43" stroke="{WOOD_EDGE}"/>'
           f'<rect x="640" y="{bottom + 3}" width="26" height="6" rx="2" fill="{CHALK}"/><rect x="674" y="{bottom + 3}" width="18" height="6" rx="2" fill="{YELLOW}"/>'
           f'<rect x="700" y="{bottom + 3}" width="22" height="6" rx="2" fill="{BLUE}"/>'
           f'<rect x="748" y="{bottom - 2}" width="52" height="11" rx="2" fill="#3a3f47"/><rect x="748" y="{bottom - 5}" width="52" height="5" rx="2" fill="#d9c9a3"/>')
    rule = "".join(f"M22 {TOP + i * ROW}H{W - 22}" for i in range(rows))
    out += (f'<path d="{rule}M{X_TEXT - 12} 62V{bottom - 8}M{X_NAME - 12} 62V{bottom - 8}" stroke="{CHALK}" stroke-width="1.5" opacity=".3"/>'
            f'<path d="M22 60H{W - 22}" stroke="{CHALK}" stroke-width="2" opacity=".55"/>')
    full = len(posts) == KEEP
    if full:  # every line is taken: someone has doodled an octopus in the top right corner (the note moves over for it)
        out += DOODLE
    text = [ink(F16, "伝言板", 26, 20, 2, CHALK, bold=True)[0], ink(F12, "MESSAGE BOARD", 136, 36, 1, CHALK)[0],
            ink(F12, "下の札から 1 行書けます。新しい伝言が上", W - 26 - (DOODLE_W if full else 0), 34, 1, CHALK, right=True)[0],
            ink(F12, "月日", X_DATE, 70, 1.5, CHALK)[0], ink(F12, "伝言", X_TEXT, 70, 1.5, CHALK)[0], ink(F12, "お名前", X_NAME, 70, 1.5, CHALK)[0]]
    for i, p in enumerate(posts):
        y = TOP + i * ROW + 4
        u = name_scale(p["login"])
        text += [ink(F16, f"{p['date'][5:7]}/{p['date'][8:10]}", X_DATE, y, 2, BLUE)[0],
                 ink(F16, PHRASES[p["n"] - 1], X_TEXT, y, 2, CHALK)[0],
                 ink(F16, p["login"], X_NAME, y + (32 - 16 * u) / 2, u, YELLOW)[0]]
    if not posts:
        text.append(ink(F16, "最初の伝言をお待ちしています", X_TEXT, TOP + 8, 1.5, CHALK)[0])
    out += f'<g fill="none" stroke-width="1" shape-rendering="crispEdges" opacity=".93">{"".join(text)}</g>'
    if posts:
        # The newest line is written in from the left when the page opens: a slate-coloured cover slides off it.
        # Without animation the cover is simply not there (opacity 0), so the line is never hidden.
        out += (f'<style>@keyframes bw{{from{{opacity:1;transform:translateX(0)}}to{{opacity:1;transform:translateX({W - 24}px)}}}}'
                f'.bw{{animation:bw 1.4s steps(28) .5s backwards}}@media (prefers-reduced-motion:reduce){{.bw{{animation:none}}}}</style>'
                f'<g clip-path="url(#bc)"><rect class="bw" opacity="0" x="12" y="{TOP + 2}" width="{W - 24}" height="{ROW - 4}" fill="{SLATE}"/></g>')
    label = "駅の伝言板。" + ("、".join(f"{p['date'][5:7]}/{p['date'][8:10]} {esc(p['login'])}「{PHRASES[p['n'] - 1]}」" for p in posts)
                          if posts else "まだ伝言はありません。最初の伝言をお待ちしています。")
    return out, label + ("。隅に、チョークで描いたたこの落書きがある" if full else ""), h


def write(state):
    body, label, h = draw(state)
    save("board.svg", W, h, body, label)


def static():
    """The eight signs that open the issue (small slates), and the sign on top of the block."""
    for n, phrase in enumerate(PHRASES, 1):
        body = (f'<rect x="1" y="1" width="218" height="46" rx="5" fill="{SLATE}" stroke="{WOOD}" stroke-width="2.5"/>'
                f'<circle cx="23" cy="24" r="14" fill="{CHALK}"/>'
                f'<text x="23" y="30" text-anchor="middle" font-family="{MONO}" font-size="17" font-weight="800" fill="{SLATE}">{n}</text>'
                f'<text x="44" y="29.5" font-family="{GOTH}" font-size="15.5" font-weight="700" fill="{CHALK}">{esc(phrase)}</text>')
        save(f"board-go-{n}.svg", 220, 48, body, f"伝言板に「{phrase}」と書く")
    plate("board-plate.svg", "#2f7a57", "伝", "言", "伝言板", "MESSAGE BOARD")


def live(ctx):
    write(load())
    return {}


def selfcheck():
    s, day = blank(), "2026-11-11"
    for bad in ["", "board:", "board: 0", "board: 9", "board:  1", "Board: 1", " board: 1", "board: 1 ", "board: 1\n",
                "board: 12", "board: 1; rm -rf /", "board: $(id)", "x board: 1", "board: 見に来ました", "board: <svg>", "train: 1", None, 1]:
        assert post(s, bad, "alice", day) == (s, MSG_BAD), bad
    for bad in ["", "a b", "evil[bot]", "<svg>", "a&b", "a\"b", "../x", "a" * 40, "名前", "$(id)", "a\n", None, 7]:
        assert post(s, "board: 1", bad, day) == (s, MSG_LOGIN), bad
    s1, msg = post(s, "board: 3", "Alice", day)
    assert s1 == {"posts": [{"login": "Alice", "n": 3, "date": day}]} and s == blank()            # input untouched
    assert PHRASES[2] in msg and "alice" not in msg.lower() and "入れ替え" not in msg               # nothing of the visitor's is echoed
    s2, msg = post(s1, "board:5", "alice", "2026-11-12")                                          # the same person, any letter case: replaced
    assert s2 == {"posts": [{"login": "alice", "n": 5, "date": "2026-11-12"}]} and "入れ替え" in msg
    for i in range(12):
        s2, _ = post(s2, f"board: {i % 8 + 1}", f"user{i}", day)
    assert len(s2["posts"]) == KEEP and s2["posts"][0]["login"] == "user11" and all(p["login"] != "alice" for p in s2["posts"])
    # a broken or hostile state file: only the well-formed entries survive, one per person, eight at most
    ok = {"login": "bob-2", "n": 8, "date": day}
    dirty = {"posts": [ok, {"login": "BOB-2", "n": 1, "date": day}, {"login": "<svg onload=x>", "n": 1, "date": day}, {"login": "x", "n": 9, "date": day},
                       {"login": "x", "n": "1", "date": day}, {"login": "x", "n": True, "date": day}, {"login": "x", "n": 1, "date": "</svg>"},
                       {"login": "x", "n": 1}, {"login": None, "n": 1, "date": day}, "text", None, 3, {"login": "x\n", "n": 1, "date": day}]}
    assert clean(dirty) == {"posts": [ok]}
    for junk in ({}, [], None, "x", 5, {"posts": None}, {"posts": {"a": 1}}, {"posts": "abc"}, {"posts": 5}):
        assert clean(junk) == blank(), junk
    assert len(clean({"posts": [{"login": f"u{i}", "n": 1, "date": day} for i in range(20)]})["posts"]) == KEEP
    # the picture: empty, one line, a full board; the longest name stays in its column; every character has a glyph
    for st in (blank(), s1, s2, {"posts": [{"login": "W" * 39, "n": 7, "date": day}]}):
        body, label, h = draw(st)
        assert body.count("<svg") == 0 and "nan" not in body and h == TOP + max(len(st["posts"]), 4) * ROW + 36
        assert all(p["login"] in label for p in st["posts"]) and (st["posts"] or "お待ち" in body or "お待ち" in label)
        assert (DOODLE in body) == ("落書き" in label) == (len(st["posts"]) == KEEP)  # the doodle: on a full board only
    assert DOODLE not in draw({"posts": s2["posts"][:KEEP - 1]})[0]
    for login in ("a", "W" * 39, "your-name"):
        assert F16.width(login) * name_scale(login) <= NAME_W and name_scale(login) >= 1, login
    assert max(F16.width(p) for p in PHRASES) * 2 <= X_NAME - 12 - X_TEXT - 6
    for font, chars in ((F16, "".join(PHRASES) + "伝言板最初の伝言をお待ちしています0123456789/-"), (F12, "月日伝言お名前下の札から行書けます。新しいが上")):
        assert all(font.glyph(ch) != font.glyph("?") for ch in chars), chars
    print("board ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["post"]:
        today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()  # the date in Japan
        old = load()
        new, answer = post(old, os.environ.get("TITLE", ""), os.environ.get("LOGIN", ""), today)
        if new is not old:
            os.makedirs(os.path.dirname(STATE), exist_ok=True)
            with open(STATE, "w", encoding="utf-8", newline="\n") as f:
                json.dump(new, f, ensure_ascii=False, indent=1)
                f.write("\n")
            with contextlib.redirect_stdout(sys.stderr):  # keep stdout for the answer alone
                write(new)
        sys.stdout.buffer.write(answer.encode("utf-8") + b"\n")  # UTF-8 whatever the console is set to
    else:
        selfcheck()
