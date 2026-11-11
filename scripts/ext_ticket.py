#!/usr/bin/env python3
"""The ticket office ("きっぷうりば"): a visitor gets a ticket from たこさし to their own GitHub name.

A visitor opens an issue titled "ticket" (the sign in README does that). .github/workflows/ticket.yml
then runs `python3 scripts/ext_ticket.py issue`, which writes tickets/<login in lower case>.svg, keeps
the serial numbers in data/tickets.json and prints the comment the workflow answers with.

    python3 scripts/ext_ticket.py                                 # self-check
    TITLE=ticket LOGIN=someone python3 scripts/ext_ticket.py issue

The issue title and the login come from strangers. Only issue() looks at them, it accepts nothing but
the exact patterns below, and the issue body is never read. The login ends up in a file name, in the
picture and in the answer, so it must be the plain form of a GitHub login and nothing else. The answer
is made of fixed sentences plus that checked login. Standard library only.
"""
import datetime
import itertools
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

USER = "takosasi-dev"
STATE = os.path.join(ROOT, "data", "tickets.json")
DIR = os.path.join(ROOT, "tickets")
RAW = f"https://raw.githubusercontent.com/{USER}/{USER}/main/tickets/"
TITLE_RE = re.compile(r"ticket")              # used with fullmatch: nothing before, nothing after
LOGIN_RE = re.compile(r"[A-Za-z0-9-]{1,39}")  # a GitHub login. "name[bot]" does not pass, on purpose
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
# Names Windows cannot check out as a file ("con.svg"). A ticket with such a name would break every clone on Windows.
RESERVED = {"con", "prn", "aux", "nul"} | {f"{p}{i}" for p in ("com", "lpt") for i in range(1, 10)}

MSG_BAD = "この題名ではきっぷを発行できません。README の「きっぷを発行する」の札から、題名を変えずに出してください。"
MSG_LOGIN = "このアカウント名ではきっぷを発行できません。"

TW, TH = 600, 300
INK, STAMP = "#22201c", "#d6402b"
# The paper: rounded corners and the notch a ticket punch leaves on the lower edge.
PAPER = "M12 1H588a11 11 0 0 1 11 11V288a11 11 0 0 1-11 11H539v-11a9 9 0 0 0-18 0v11H12a11 11 0 0 1-11-11V12A11 11 0 0 1 12 1z"
NOTES = "経由:GitHub　発行日から無期限有効　下車前途無効"
SAMPLE = {"login": "your-name", "no": 0, "date": "2026-11-11"}
# The paper: (ground, the wave pattern, the edge). Lucky numbers are printed on gold; nothing on the page says so.
GREEN_PAPER = ("#e6f1de", "#bfdab2", "#8fa886")
GOLD_PAPER = ("url(#gd)", "#cfa646", "#9c7a25")
MSG_GOLD = "金のきっぷが出ました。"


def blank():
    return {"count": 0, "issued": {}}


def load():
    """The state file, cleaned. It is only written by this script, but it is drawn, so trust nothing in it."""
    if not os.path.exists(STATE):
        return blank()
    with open(STATE, encoding="utf-8") as f:
        raw = json.load(f)
    issued = {}
    for v in raw.get("issued", {}).values():
        if (isinstance(v, dict) and LOGIN_RE.fullmatch(str(v.get("login"))) and DATE_RE.fullmatch(str(v.get("date")))
                and isinstance(v.get("no"), int) and v["no"] >= 1):
            issued[v["login"].lower()] = {"login": v["login"], "no": v["no"], "date": v["date"]}
    return {"count": max([int(raw.get("count", 0))] + [v["no"] for v in issued.values()]), "issued": issued}


def lucky(no):
    """The numbers that get a gold ticket: 1, 7, 10, every hundred, and 11 or more with all digits the same."""
    return no in (1, 7, 10) or (no > 0 and no % 100 == 0) or (no >= 11 and len(set(str(no))) == 1)


def issue(state, title, login, today):
    """(new state, the comment to answer with, the ticket or None). Anything that is not exactly right leaves the state as it is."""
    if not isinstance(title, str) or not TITLE_RE.fullmatch(title):
        return state, MSG_BAD, None
    if not isinstance(login, str) or not LOGIN_RE.fullmatch(login) or login.lower() in RESERVED:
        return state, MSG_LOGIN, None
    key = login.lower()  # logins are case-insensitive: one person, one number, one file
    old = state["issued"].get(key)
    t = {"login": login, "no": old["no"] if old else state["count"] + 1, "date": old["date"] if old else today}
    new = {"count": max(state["count"], t["no"]), "issued": {**state["issued"], key: t}}
    url = RAW + key + ".svg"
    head = "きっぷは発行済みです。同じ番号で作り直しました。" if old else "きっぷを発行しました。"
    return new, (f"{head}通し番号は No.{t['no']:05d} です。{MSG_GOLD if lucky(t['no']) else ''}\n\n"
                 f"![たこさし駅の乗車券]({url})\n\n"
                 "自分の README に貼るときは、次の 1 行をどうぞ。\n\n"
                 f"```md\n[![たこさし駅の乗車券]({url})](https://github.com/{USER})\n```\n\n"
                 "絵が出るまで数分かかることがあります。ご乗車ありがとうございました。"), t


# --------------------------------------------------------------------------- the picture
def ink(font, s, x, y, u, col=INK, bold=False, right=False):
    """Text printed in square dots, u px a dot, from the Shinonome glyphs: it looks the same on every machine.
    (the path, the width in px). With right=True, x is the right edge."""
    d = ""
    rows = font.rows(s, bold=bold)
    for r, row in enumerate(rows):
        c = 0
        for lit, run in itertools.groupby(row):
            n = len(list(run))
            if lit:
                d += f"M{c} {r}.5h{n}"
            c += n
    w = len(rows[0]) * u
    return f'<path transform="translate({x - w if right else x:.1f} {y:.1f}) scale({u:.3f})" stroke="{col}" d="{d}"/>', w


def name_scale(name):
    """px per dot for the name: as large as the line (552px) allows, in half steps so the dots stay even.
    1 letter gives 3.5, the longest login (39 letters and the @) gives 1.5."""
    return int(min(3.5, 552 / F16.width(name)) * 2) / 2


def draw(t, sample=False):
    """(SVG body, label) of one ticket. t: {"login", "no", "date"}; all three were checked before they get here."""
    name = "@" + t["login"]
    y, m, d = t["date"].split("-")
    serial = f"No.{t['no']:05d}"
    u = name_scale(name)
    out = "".join(p for p, _ in [
        ink(F16, "記念乗車券", 24, 20, 2, bold=True),
        ink(F16, "たこさし駅発行", 576, 20, 1, right=True),
        ink(F16, serial, 576, 40, 1, right=True),
        ink(F16, "たこさし", 24, 72, 3, bold=True),
        ink(F16, "→", 236, 72, 3, bold=True),
        ink(F16, name, 24, 136 + (56 - 16 * u) / 2, u),
        ink(F12, NOTES, 24, 218, 1.5),
        ink(F16, "￥0", 576, 211, 2, bold=True, right=True),
        ink(F16, f"{y}.{m}.{d}", 24, 252, 1.5),
        ink(F16, "たこさし駅 自動発券機", 164, 256, 1),
        ink(F16, f"{t['no']:05d}-01", 505, 256, 1, right=True),
    ])
    # The round date stamp of the gate, pressed a little crooked.
    stamp = (f'<g transform="rotate(-9 510 96)" opacity=".82"><circle cx="510" cy="96" r="34" fill="none" stroke="{STAMP}" stroke-width="3"/>'
             f'<path d="M479 85h62M479 107h62" stroke="{STAMP}" stroke-width="2"/>'
             + ink(F12, "たこさし", 486, 69, 1, STAMP)[0] + ink(F12, f"{y[2:]}.{m}.{d}", 486, 90, 1, STAMP)[0] + ink(F12, "改札", 498, 110, 1, STAMP)[0] + "</g>")
    over = ink(F16, "見本", 372, 134, 4, STAMP, bold=True)[0].replace("<path ", '<path opacity=".6" ') if sample else ""
    gold = lucky(t["no"]) and not sample
    ground, wave, edge = GOLD_PAPER if gold else GREEN_PAPER
    # Gold: a foil gradient, and a band of light that crosses the paper now and then (it waits off the paper, so no motion = no band).
    foil = ('<linearGradient id="gd" x2="1" y2="1"><stop offset="0" stop-color="#f6e5a6"/><stop offset=".42" stop-color="#e3c164"/>'
            '<stop offset=".58" stop-color="#f9edbe"/><stop offset="1" stop-color="#d9b250"/></linearGradient>'
            '<style>@keyframes gs{0%,72%{transform:translateX(0)}100%{transform:translateX(900px)}}.gs{animation:gs 7s ease-in-out infinite}'
            '@media (prefers-reduced-motion:reduce){.gs{animation:none}}</style>') if gold else ""
    shine = '<g transform="skewX(-20)"><rect class="gs" x="-150" y="-10" width="90" height="320" fill="#fff" opacity=".4"/></g>' if gold else ""
    body = (f'<defs><pattern id="jm" width="24" height="12" patternUnits="userSpaceOnUse"><path d="M0 6q6-7 12 0t12 0" fill="none" stroke="{wave}" stroke-width="1.3"/></pattern>'
            f'<clipPath id="pp"><path d="{PAPER}"/></clipPath>{foil}</defs>'
            f'<path d="{PAPER}" fill="{ground}"/><path d="{PAPER}" fill="url(#jm)"/>'
            f'<g clip-path="url(#pp)">{shine}<rect y="62" width="{TW}" height="1.5" fill="{INK}" opacity=".55"/>'
            f'<path d="M24 206H576" stroke="{INK}" stroke-width="1.5" stroke-dasharray="3 3" opacity=".7"/>'
            f'<g fill="none" stroke-width="1" shape-rendering="crispEdges">{out}{stamp}{over}</g></g>'
            f'<path d="{PAPER}" fill="none" stroke="{edge}" stroke-width="1.5"/>')
    return body, (f"{'金の' if gold else ''}乗車券{'の見本' if sample else ''}。たこさし → {name}、通し番号 {serial}、発行日 {t['date']}、改札印つき")


def write(t):
    body, label = draw(t)
    path = os.path.join(DIR, t["login"].lower() + ".svg")
    assert os.path.dirname(os.path.abspath(path)) == os.path.abspath(DIR), path  # the name cannot leave tickets/
    os.makedirs(DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TW} {TH}" width="{TW}" height="{TH}" '
                f'role="img" aria-label="{esc(label)}">{body}</svg>\n')


def static():
    """The sample ticket, the sign that opens the issue, and the sign on top of the block.
    The tickets already handed out are printed again too, so they follow a change of the drawing
    (the daily run does not commit tickets/: run build_assets.py by hand and commit them)."""
    save("ticket-sample.svg", TW, TH, *draw(SAMPLE, sample=True))
    for t in load()["issued"].values():
        write(t)
    body = (f'<rect x="1" y="1" width="298" height="62" rx="7" fill="#1d4f9e" stroke="#0d2a57" stroke-width="2"/>'
            f'<circle cx="32" cy="32" r="21" fill="#fff"/>'
            f'<path d="M18 24h28v5a3 3 0 0 0 0 6v5H18v-5a3 3 0 0 0 0-6z" fill="#1d4f9e"/>'
            f'<path d="M37 25.5v13" stroke="#fff" stroke-width="1.6" stroke-dasharray="2.2 2"/>'
            f'<text x="64" y="26" font-family="{GOTH}" font-size="12" font-weight="700" fill="#fff" opacity=".85" letter-spacing="1">きっぷうりば</text>'
            f'<text x="64" y="50" font-family="{GOTH}" font-size="21" font-weight="700" fill="#fff">きっぷを発行する</text>'
            f'<path d="M256 32h26m-10-10l10 10l-10 10" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
    save("ticket-go.svg", 300, 64, body, "きっぷを発行する")
    plate("ticket-plate.svg", LINE[1], "発", "券", "きっぷうりば", "TICKETS")


def selfcheck():
    s, day = blank(), "2026-11-11"
    for bad in ["", "ticket ", " ticket", "Ticket", "ticket\n", "tickets", "ticket: 1", "ticket; rm -rf /", "$(id)", None, 1]:
        assert issue(s, bad, "alice", day) == (s, MSG_BAD, None), bad
    for bad in ["", "a b", "dependabot[bot]", "../x", "..", "a/b", "a\\b", "x.svg", "<svg>", "a" * 40, "名前", "$(id)", "a\n", "CON", "nul", "Lpt1", None]:
        assert issue(s, "ticket", bad, day) == (s, MSG_LOGIN, None), bad
    s1, msg, t = issue(s, "ticket", "Alice", day)
    assert t == {"login": "Alice", "no": 1, "date": day} and s1["count"] == 1 and s == blank()  # input untouched
    assert "No.00001" in msg and msg.count(RAW + "alice.svg") == 2 and "発行しました" in msg
    s2, msg, t = issue(s1, "ticket", "alice", "2027-01-01")  # the same person again, any letter case: same number, same date
    assert (t["no"], t["date"]) == (1, day) and s2["count"] == 1 and len(s2["issued"]) == 1 and "発行済み" in msg
    s3, _, t = issue(s2, "ticket", "bob-2", "2026-11-12")
    assert t["no"] == 2 and s3["count"] == 2
    for login in ("a", "W" * 39, "your-name"):  # the shortest and the longest name both stay on the paper
        body, label = draw({"login": login, "no": 99999, "date": day})
        u = name_scale("@" + login)
        assert 1.5 <= u <= 3.5 and F16.width("@" + login) * u <= 552 and login in label, (login, u)
    # gold: 1, 7, 10, the hundreds and the repdigits; never the sample; told in the answer by one fixed sentence
    assert [n for n in range(201) if lucky(n)] == [1, 7, 10, 11, 22, 33, 44, 55, 66, 77, 88, 99, 100, 111, 200]
    assert lucky(77777) and lucky(1000) and not lucky(0) and not lucky(70) and not lucky(101)
    assert MSG_GOLD in issue(s, "ticket", "Alice", day)[1] and MSG_GOLD not in issue(s1, "ticket", "bob-2", day)[1]
    for no, sample, gold in ((1, False, True), (2, False, False), (0, True, False), (7, True, False)):
        body, label = draw({"login": "a", "no": no, "date": day}, sample=sample)
        assert ("url(#gd)" in body) == ('id="gd"' in body) == label.startswith("金の") == gold, (no, sample)
    for font, text in ((F16, "記念乗車券たこさし駅発行→自動発券機見本￥@No.-"), (F12, NOTES + "たこさし改札")):  # every printed character has a glyph
        assert all(font.glyph(ch) != font.glyph("?") for ch in text), text
    print("ticket ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["issue"]:
        today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()  # the date in Japan
        old = load()
        new, answer, t = issue(old, os.environ.get("TITLE", ""), os.environ.get("LOGIN", ""), today)
        if t:
            os.makedirs(os.path.dirname(STATE), exist_ok=True)
            with open(STATE, "w", encoding="utf-8", newline="\n") as f:
                json.dump(new, f, ensure_ascii=False, indent=1, sort_keys=True)
                f.write("\n")
            write(t)
        sys.stdout.buffer.write(answer.encode("utf-8") + b"\n")  # UTF-8 whatever the console is set to
    else:
        selfcheck()
