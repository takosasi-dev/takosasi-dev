#!/usr/bin/env python3
"""The passengers' train: everyone who starred one of the repos looks out of a window.

    assets/riders.svg

update_live.py calls live(ctx) with ctx["stars"] (newest first, one entry per person, the owner left out).

    python3 scripts/ext_riders.py        # self-check
    python3 scripts/ext_riders.py 30     # draw assets/riders.svg with 30 made-up passengers, to look at a crowd

An SVG shown through <img> cannot load anything from outside, so each avatar is fetched (64px) and put
into the picture as a data: URI. Only avatars.githubusercontent.com is asked, only a small PNG or JPEG is
taken, and anything else (no network, a redirect elsewhere, another format) becomes a circle with the
first letter of the login. Standard library only.
"""
import base64
import datetime
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

HOST = "https://avatars.githubusercontent.com/"
LIMIT = 100_000                 # bytes; a 64px avatar is a few KB
SEATS, PER_CAR = 12, 4
CW, GAP, HW, WIN, TOP = 234, 4, 96, 46, 12   # car width, coupling, head width, window size, roof line
TRAIN_H = TOP + 92
JST = datetime.timezone(datetime.timedelta(hours=9))


def kind(data):
    """The MIME type if the bytes start like a PNG or a JPEG, else None."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    return None


def avatar(url):
    """The avatar as a data: URI, or None. Never raises: a missing face must not stop the daily run."""
    if not isinstance(url, str) or not url.startswith(HOST):
        return None
    try:
        req = urllib.request.Request(url + ("&" if "?" in url else "?") + "s=64", headers={"User-Agent": "profile-readme"})
        with urllib.request.urlopen(req, timeout=10) as r:
            if not r.geturl().startswith(HOST):  # redirected to somewhere else
                return None
            data = r.read(LIMIT + 1)
    except Exception:
        return None
    mime = kind(data)
    if len(data) > LIMIT or not mime:
        return None
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


def window(j, x, y, rider, face):
    box = f'x="{x}" y="{y}" width="{WIN}" height="{WIN}"'
    out = f'<rect {box} rx="5" fill="#27303b"/>'
    if rider is None:  # an empty seat: just a reflection on the glass
        return out + f'<path d="M{x + 9} {y + WIN - 9}l{WIN - 18}-{WIN - 18}" stroke="#fff" stroke-opacity=".07" stroke-width="7" stroke-linecap="round"/>'
    if face:
        out += (f'<clipPath id="w{j}"><rect {box} rx="5"/></clipPath>'
                f'<image clip-path="url(#w{j})" {box} preserveAspectRatio="xMidYMid slice" href="{face}"/>')
    else:
        col = LINE[sum(rider["login"].encode()) % len(LINE)]
        out += (f'<circle cx="{x + WIN / 2}" cy="{y + WIN / 2}" r="17" fill="{col}"/>'
                f'<text x="{x + WIN / 2}" y="{y + WIN / 2 + 8}" text-anchor="middle" font-family="{MONO}" font-size="23" font-weight="800" fill="#fff">{esc(rider["login"][0].upper())}</text>')
    return out + f'<rect {box} rx="5" fill="none" stroke="#5d6570" stroke-width="2"/>'


def train(riders, faces):
    """The train standing at the platform, head to the right. The newest passenger sits right behind the driver."""
    cars = max(1, -(-len(riders) // PER_CAR))
    L = HW + cars * (CW + GAP)
    x0 = (W - L) // 2
    hx = x0 + L - HW
    wheel = lambda cx: f'<circle cx="{cx}" cy="{TOP + 74}" r="6" fill="#2b2f36" stroke="#8a9099"/>'  # noqa: E731
    out = ""
    for i in range(cars):
        x = hx - (i + 1) * (CW + GAP)
        out += (f'<rect x="{x}" y="{TOP}" width="{CW}" height="70" rx="6" fill="#eceff2" stroke="#8a9099"/>'
                f'<rect x="{x}" y="{TOP + 61}" width="{CW}" height="3" fill="{LINE[2]}"/>'
                f'<rect x="{x + CW}" y="{TOP + 50}" width="{GAP}" height="5" fill="#555b64"/>')
        for k in range(PER_CAR):
            j = i * PER_CAR + k
            r = riders[j] if j < len(riders) else None
            out += window(j, x + CW - 10 - WIN - k * 56, TOP + 9, r, r and faces.get(r["login"]))
        out += "".join(wheel(x + dx) for dx in (24, 44, CW - 44, CW - 24))
    out += (f'<path d="M{hx} {TOP}h{HW - 42}q32 4 42 46v24h-{HW}z" fill="#eceff2" stroke="#8a9099"/>'
            f'<path d="M{hx + HW - 44} {TOP + 8}h8q18 4 26 28h-34z" fill="#27303b"/>'
            f'<rect x="{hx + 8}" y="{TOP + 9}" width="40" height="20" rx="3" fill="#27303b"/>'
            f'<text x="{hx + 28}" y="{TOP + 23.5}" text-anchor="middle" font-family="{GOTH}" font-size="12" font-weight="700" fill="#fff">スター</text>'
            f'<rect x="{hx}" y="{TOP + 61}" width="{HW}" height="3" fill="{LINE[2]}"/>'
            f'<circle cx="{hx + HW - 6}" cy="{TOP + 62}" r="4" fill="#ffd84a"/>'
            + "".join(wheel(hx + dx) for dx in (18, 38, HW - 28)))
    css = (f"@keyframes ra{{from{{transform:translateX(-{x0 + L + 20}px)}}}}"  # it pulls in once, when the picture loads
           ".ra{animation:ra 3s cubic-bezier(.15,.75,.25,1) both}@media (prefers-reduced-motion:reduce){.ra{animation:none}}")
    track = (f'<path d="M0 {TOP + 81}H{W}" stroke="#8a9099" stroke-width="2.5"/>'
             f'<path d="M2 {TOP + 86}H{W}" stroke="#6a717b" stroke-width="5" stroke-dasharray="4 12"/>')
    return f'<style>{css}</style>{track}<g class="ra">{out}</g>'


def day(at):
    """MM/DD in Japan of an ISO time in UTC ("2026-11-10T16:20:00Z")."""
    return datetime.datetime.fromisoformat(at.replace("Z", "+00:00")).astimezone(JST).strftime("%m/%d")


def draw(stars, faces):
    riders = stars[:SEATS]
    n, more = len(stars), len(stars) - len(riders)
    wide = len(riders) > 6                      # few: one a line, with what they starred. many: three names a line
    lines = (-(-len(riders) // 3) if wide else len(riders)) + (1 if more else 0) or 2
    y0 = TRAIN_H + 4
    b = Board("p", LED_X, y0 + 40, LED_COLS, 28 + 18 * lines)
    w = b.put(F16, "乗客", 7, 4, GREEN, invert=True)
    b.put(F16, "ご乗車ありがとうございます", 15 + w, 4, AMBER)
    b.put(F16, f"{n}名", 397, 4, AMBER, right=True)
    for i, r in enumerate(riders):
        if wide:
            b.put(F16, F16.fit(r["login"], 126), 6 + (i % 3) * 132, 26 + (i // 3) * 18, AMBER)
        else:
            tw = b.put(F16, f'{F16.fit(r["repo"], 150)} {day(r["at"])}', 397, 26 + i * 18, GREEN, right=True)
            b.put(F16, F16.fit(r["login"], 397 - tw - 16), 6, 26 + i * 18, AMBER)
    if more:
        b.put(F16, f"ほか {more}名", 397, 26 + (lines - 1) * 18, GREEN, right=True)
    if not riders:
        b.put(F16, "最初の乗客を募集中です。", 6, 26, GREEN)
        b.put(F16, "スターを付けると、この列車に乗れます。", 6, 44, GREEN)
    h = y0 + 40 + b.h + 17
    save("riders.svg", W, h,
         train(riders, faces) + casing(W, h, "ご乗車のお客様", "Passengers", "スターを付けた方が乗客になります", y=y0) + b.svg() + seam(b, 23),
         f"スターを付けた方を乗せた列車。乗客 {n} 名" + (": " + "、".join(esc(r["login"]) for r in riders) if riders else "。最初の乗客を募集中"))


def live(ctx):
    stars = ctx.get("stars") or []
    # update_live.py given a saved response (an argument) is a local preview: draw without asking the network.
    online = len(sys.argv) < 2 or os.environ.get("RIDERS_FETCH")
    draw(stars, {s["login"]: avatar(s["avatar"]) for s in stars[:SEATS]} if online else {})
    return {}


if __name__ == "__main__":
    if sys.argv[1:] and sys.argv[1].isdigit():  # a made-up crowd, to look at the layout
        fake = [{"login": name, "avatar": "", "at": f"2026-11-{10 - i % 9:02d}T03:00:00Z", "repo": repo}
                for i, (name, repo) in enumerate(zip(
                    ["a", "octo-cat", "M" * 39, "ARTS-Night", "bob-2", "x9", "long-long-login-name-1234", "Zed"] * 4,
                    ["kanade-daw", "minecraft-building-blocks-plus", "takosasi-dev", "net-diag"] * 8))][:int(sys.argv[1])]
        draw(fake, {})
    else:
        png = b"\x89PNG\r\n\x1a\n" + b"\0" * 8
        assert kind(png) == "image/png" and kind(b"\xff\xd8\xff\xe0") == "image/jpeg"
        assert kind(b"<svg onload=alert(1)>") is None and kind(b"GIF89a") is None and kind(b"") is None
        for bad in ["", None, "http://avatars.githubusercontent.com/u/1", "https://example.com/a.png",
                    "https://avatars.githubusercontent.com.evil.example/u/1", "file:///etc/passwd"]:
            assert avatar(bad) is None, bad  # refused before any request is made
        assert day("2026-11-10T16:20:00Z") == "11/11"  # past 15:00 UTC it is the next day in Japan
        print("riders ok")
