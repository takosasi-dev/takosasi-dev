#!/usr/bin/env python3
"""More mini games for the waiting room. Standard library only.

    static()   log-1..5.svg (read the access log), diff-a/b/answer.svg (spot the difference), game-5..8.svg
    live(ctx)  subnet.svg (a new subnet question every morning), amida.svg (a new ladder lottery every
               morning), and the answers for README between the LOGQUIZ / SUBNET / AMIDA markers

Called by build_assets.py and update_live.py. `python3 scripts/ext_games.py` runs the self-check.
The answers of the log quiz are generated from the table below, so README cannot drift away from it.
"""
import ipaddress
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

RIGHT, WRONG = "<b>正解。</b>", "<b>不正解。</b>"


def fold(summary, body):
    return f"<details><summary>{summary}</summary><blockquote>{body}</blockquote></details>"


# --------------------------------------------------------------------------- game 5: read the access log
# One question: six log rows and three candidate line numbers (number, is it the attack, what to tell the player).
# A row is (source, method, path, status), or with the time in front when the timing matters.
# Sources are documentation addresses only (RFC 5737). The payloads are short textbook samples.
LOGS = [
    ([("198.51.100.23", "GET", "/item?id=42", "200"),
      ("192.0.2.14", "GET", "/item?id=9999", "404"),
      ("198.51.100.23", "GET", "/cart", "200"),
      ("203.0.113.5", "GET", "/item?id=abc", "400"),
      ("203.0.113.80", "GET", "/item?id=1'+OR+'1'='1", "200"),
      ("192.0.2.77", "POST", "/cart/add", "302")],
     [(2, False, "無い商品番号を開いて 404 になっただけです。攻撃の記号はありません。"),
      (4, False, "数字のはずの所に abc を入れて 400。入力まちがいの範囲です。引用符や OR はありません。"),
      (5, True, "SQL インジェクションです。番号が入るはずの id に、引用符と OR '1'='1(いつでも成り立つ条件)が入っています。")]),
    ([("192.0.2.31", "GET", "/dl?f=manual.pdf", "200"),
      ("203.0.113.42", "GET", "/dl?f=../../etc/passwd", "200"),
      ("198.51.100.9", "GET", "/dl?f=price-2026.pdf", "200"),
      ("192.0.2.31", "GET", "/dl?f=manual.pdf", "304"),
      ("198.51.100.64", "GET", "/dl?f=old/2019.pdf", "404"),
      ("192.0.2.8", "GET", "/favicon.ico", "404")],
     [(2, True, "パスのさかのぼり(ディレクトリトラバーサル)です。ファイル名に ../ を重ねて、公開フォルダの外にある /etc/passwd を読もうとしています。"),
      (4, False, "304 は「前に渡した物から変わっていない」の返事。ふつうの再読み込みです。"),
      (5, False, "フォルダの区切り / はありますが、../ で上にはさかのぼっていません。古いファイルが無くて 404 になっただけです。")]),
    ([("198.51.100.40", "GET", "/ping?h=192.0.2.1", "200"),
      ("198.51.100.40", "GET", "/ping?h=192.0.2.300", "400"),
      ("192.0.2.90", "GET", "/ping?h=gw.example", "200"),
      ("203.0.113.7", "GET", "/ping?h=192.0.2.1;id", "200"),
      ("192.0.2.90", "GET", "/ping?h=", "400"),
      ("198.51.100.3", "POST", "/ping", "405")],
     [(2, False, "300 は IP アドレスに無い数字。打ちまちがいで 400 になっただけです。"),
      (4, True, "コマンド注入です。ホスト名の後ろに ; を付けて、別のコマンド(id)を続けて走らせようとしています。"),
      (6, False, "この URL では POST が許されておらず 405。; や | のような記号はありません。")]),
    ([("192.0.2.55", "GET", "/?q=led+board", "200"),
      ("198.51.100.12", "GET", "/?q=1<2", "200"),
      ("192.0.2.55", "GET", "/?q=c%2B%2B", "200"),
      ("198.51.100.12", "GET", "/?q=", "200"),
      ("203.0.113.99", "GET", "/?q=<script>x</script>", "200"),
      ("192.0.2.201", "GET", "/robots.txt", "200")],
     [(2, False, "< はありますが、タグの形になっていません。「1<2」を調べただけです。"),
      (3, False, "%2B は + を URL 用に書き換えた物。「c++」を調べただけです。"),
      (5, True, "クロスサイトスクリプティング(XSS)です。検索語に <script> タグを入れ、ページにそのまま出力されてスクリプトが動くかを試しています。")]),
    ([("12:00:01", "198.51.100.7", "GET", "/login", "200"),
      ("12:00:03", "203.0.113.66", "POST", "/login", "401"),
      ("12:00:03", "203.0.113.66", "POST", "/login", "401"),
      ("12:00:04", "192.0.2.15", "POST", "/login", "401"),
      ("12:00:04", "203.0.113.66", "POST", "/login", "401"),
      ("12:00:05", "203.0.113.66", "POST", "/login", "401")],
     [(1, False, "ログイン画面を開いただけ(GET で 200)です。"),
      (3, True, "総当たり(ブルートフォース)です。同じ 203.0.113.66 が、2 秒のあいだに 4 回続けてログインに失敗しています。人の手では打てない速さです。"),
      (4, False, "別の送信元の、1 回だけの失敗です。パスワードの打ちまちがいでしょう。")]),
]


def log_boards():
    for i, (rows, _) in enumerate(LOGS, 1):
        timed = len(rows[0]) == 5
        xs = (22, 94, 206, 246) if timed else (22, 22, 134, 174)  # time, source, method, path (in dots)
        b = Board("l", LED_X, 58, LED_COLS, 4 + 18 * len(rows))
        for n, row in enumerate(rows):
            y = 3 + n * 18
            src, method, path, status = row[-4:]
            b.put(F16, str(n + 1), 6, y, AMBER)
            if timed:
                b.put(F16, row[0], xs[0], y, GREEN)
            b.put(F16, src, xs[1], y, GREEN)
            b.put(F16, method, xs[2], y, GREEN)
            b.put(F16, F16.fit(path, 365 - xs[3]), xs[3], y, AMBER)
            b.put(F16, status, 397, y, {"2": GREEN, "5": RED}.get(status[0], AMBER), right=True)
        h = 58 + b.h + 17
        heads = "".join(f'<text x="{LED_X + 2 * x}" y="50">{t}</text>' for x, t in
                        [(5, "行"), (xs[1], "送信元"), (xs[2], "メソッド"), (xs[3], "パス")] + ([(xs[0], "時刻")] if timed else []))
        heads = (f'<g font-family="{GOTH}" font-size="10.5" fill="#aab0b8">{heads}'
                 f'<text x="815" y="50" text-anchor="end">状態</text></g>')
        save(f"log-{i}.svg", W, h, casing(W, h, "アクセスログ", f"Question {i}/{len(LOGS)}", "攻撃の行を 1 つ選んでください") + heads + b.svg(),
             f"アクセスログ 第 {i} 問。" + "。".join(f"{n} 行目: {' '.join(r)}" for n, r in enumerate(rows, 1)))


def log_md():
    out = []
    for i, (_, options) in enumerate(LOGS, 1):
        out.append(f'<b>第 {i} 問</b>\n\n<img src="assets/log-{i}.svg" width="100%" alt="アクセスログ 第 {i} 問(6 行)">\n'
                   + "\n".join(fold(f"{n} 行目", (RIGHT if ok else WRONG) + esc(why)) for n, ok, why in options))
    return "\n\n".join(out)


# --------------------------------------------------------------------------- game 6: the subnet question of the day
def subnet_quiz(today):
    """One question, seeded by the date. Returns (address/prefix, question, [(answer, correct?, comment)], how to work it out)."""
    rnd = random.Random(today + ":subnet")
    p = rnd.choice([25, 26, 26, 27, 27, 28, 28, 29, 30, 20, 21, 22, 23])
    idx = 3 if p > 24 else 2          # the octet the prefix cuts through
    block = 2 ** (8 - p % 8)          # size of one block in that octet
    while True:
        o = rnd.choice([[192, 168], [10, rnd.randrange(256)], [172, rnd.randrange(16, 32)]]) + [rnd.randrange(256), rnd.randrange(256)]
        host = ipaddress.ip_address(".".join(map(str, o)))
        net = ipaddress.ip_network(f"{host}/{p}", strict=False)
        if host not in (net.network_address, net.broadcast_address):
            break
    na, bc, n = net.network_address, net.broadcast_address, net.num_addresses
    lo = o[idx] // block * block
    assert int(str(na).split(".")[idx]) == lo  # the explanation below must agree with ipaddress
    nth, whole = ("最後の数字", "/24") if idx == 3 else ("3 番目の数字", "/16")
    how = (f"/{p} は、{nth}を {block} ずつに区切ります。{o[idx]} は {lo}〜{lo + block - 1} の区切りに入るので、"
           f"ネットワークアドレスは {na}、ブロードキャストアドレスは {bc}。"
           f"アドレスは全部で {n:,} 個、使えるホストはそこから 2 を引いて {n - 2:,} 台です。")
    kind = rnd.choice(["net", "bc", "hosts"])
    if kind == "net":
        ask, good = "のネットワークアドレスは？", str(na)
        bad = [(str(ipaddress.ip_network(f"{host}/{8 * idx}", strict=False).network_address), f"それは {whole} のときの答えです。/{p} はもっと細かく区切ります。"),
               (str(na + 1), "それは最初に使えるホストのアドレスです。ネットワークアドレスはその 1 つ前です。"),
               (str(na + n), "それは 1 つ後ろの区切りの先頭です。")]
    elif kind == "bc":
        ask, good = "のブロードキャストアドレスは？", str(bc)
        bad = [(str(ipaddress.ip_network(f"{host}/{8 * idx}", strict=False).broadcast_address), f"それは {whole} のときの答えです。/{p} はもっと細かく区切ります。"),
               (str(bc - 1), "それは最後に使えるホストのアドレスです。ブロードキャストアドレスはその 1 つ後ろです。"),
               (str(bc + 1), "それは 1 つ後ろの区切りのネットワークアドレスです。")]
    else:
        ask, good = "で使えるホストは何台？", f"{n - 2:,} 台"
        bad = [(f"{n:,} 台", "それはアドレスの総数です。ネットワークアドレスとブロードキャストアドレスの 2 つは使えません。"),
               (f"{n - 1:,} 台", "引くのは 2 つです(ネットワークアドレスとブロードキャストアドレス)。"),
               (f"{2 * n - 2:,} 台", f"それは /{p - 1} のときの答えです。")]
    options = [(good, True, how)] + [(a, False, why) for a, why in rnd.sample([x for x in bad if x[0] != good], 2)]
    rnd.shuffle(options)
    return f"{host}/{p}", ask, options, how


def subnet(today):
    cidr, ask, options, _ = subnet_quiz(today)
    b = Board("n", LED_X, 40, LED_COLS, 82)
    w = b.put(F16, "本日の問題", 7, 4, GREEN, invert=True)
    b.put(F16, f"{today[5:7]}/{today[8:10]}", 15 + w, 4, AMBER)
    b.put(F16, cidr, 6, 24, AMBER, scale=2)
    b.put(F16, ask, 6, 62, GREEN)
    save("subnet.svg", W, 221, casing(W, 221, "本日のサブネット問題", "Daily quiz", "毎朝 6 時すぎに入れ替わります") + b.svg() + seam(b, 58),
         f"本日のサブネット問題: {cidr} {ask}")
    return "\n".join(fold(a, (RIGHT if ok else WRONG) + why) for a, ok, why in options)


# --------------------------------------------------------------------------- game 7: ladder lottery (amidakuji)
def amida_draw(today):
    """Nine rungs, one per level, each joining column g and g+1. Returns (rungs, where each start ends up)."""
    rnd = random.Random(today + ":amida")
    while True:
        rungs, prev = [], None
        for _ in range(9):
            prev = rnd.choice([g for g in range(3) if g != prev])  # the same gap twice in a row would undo itself
            rungs.append(prev)
        ends = []
        for pos in range(4):
            for g in rungs:
                pos += 1 if g == pos else -1 if g == pos - 1 else 0
            ends.append(pos)
        if ends != [0, 1, 2, 3]:  # a lottery that sends everyone straight down is no fun
            return rungs, ends


def amida(ctx):
    today, user = ctx["today"], ctx["USER"]
    rungs, ends = amida_draw(today)
    picks = random.Random(today + ":amida-picks").sample(sorted(ctx["repos"], key=lambda r: r["name"]), 4)
    xs, top, H = [129, 325, 521, 717], 118, 470
    out = (f'<g font-family="{GOTH}"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="7" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
           f'<text x="24" y="38" font-size="23" font-weight="700" fill="#111" letter-spacing="3">あみだくじ</text>'
           f'<text x="156" y="37" font-size="13" fill="#666" font-family="{MONO}" letter-spacing="1">{today[5:7]}/{today[8:10]}</text>'
           f'<text x="{W - 24}" y="37" text-anchor="end" font-size="14" font-weight="700" fill="#555">のりばを 1 つ選んで、線を下へたどってください</text>'
           f'<g stroke="#333" stroke-width="7" stroke-linecap="round">')
    out += "".join(f'<path d="M{x} {top}V330"/>' for x in xs)
    out += "".join(f'<path d="M{xs[g]} {138 + lv * 21}H{xs[g + 1]}"/>' for lv, g in enumerate(rungs)) + "</g>"
    for i, x in enumerate(xs):
        out += (f'<circle cx="{x}" cy="92" r="21" fill="{LINE[i]}"/>'
                f'<text x="{x}" y="100" text-anchor="middle" font-size="24" font-weight="700" fill="#fff">{i + 1}</text>'
                f'<circle cx="{x}" cy="356" r="21" fill="#333"/>'
                f'<text x="{x}" y="364" text-anchor="middle" font-size="23" font-weight="700" fill="#fff" class="ni">{"ABCD"[i]}</text>')
    for i, r in enumerate(picks):  # which repo each exit is; which start reaches it is left to the player
        x, y = 40 + (i % 2) * 400, 412 + (i // 2) * 34
        name = r["name"] if len(r["name"]) <= 26 else r["name"][:25] + "…"
        out += (f'<circle cx="{x + 12}" cy="{y - 8}" r="13" fill="#333"/>'
                f'<text x="{x + 12}" y="{y - 2}" text-anchor="middle" font-size="15" font-weight="700" fill="#fff" class="ni">{"ABCD"[i]}</text>'
                f'<text x="{x + 34}" y="{y}" font-size="21" font-weight="700" fill="#111" font-family="{MONO}">{esc(name)}</text>')
    save("amida.svg", W, H, out + "</g>",
         "あみだくじ。のりば 1〜4 から線をたどる。行き先 " + "、".join(f'{"ABCD"[i]}: {r["name"]}' for i, r in enumerate(picks)))
    folds = []
    for i, e in enumerate(ends):
        r = picks[e]
        desc = ctx["DESC"].get(r["name"]) or r["desc"]
        folds.append(fold(f"{i + 1} 番のりば", f'<b>{"ABCD"[e]}</b> に着きます。本日のおすすめは '
                          f'<a href="https://github.com/{user}/{r["name"]}">{esc(r["name"])}</a>' + (f"({esc(desc)})" if desc else "") + "。"))
    return "\n".join(folds)


# --------------------------------------------------------------------------- game 8: spot the difference
# (time, type, colour of the type, destination, platform). The stations are the ones of the transfer maze.
DEPART = [("06:17", "快速", AMBER, "リリース", "1"), ("06:32", "各停", GREEN, "テスト", "2"), ("06:45", "特急", RED, "仕様書", "3"),
          ("07:03", "各停", GREEN, "バグの山", "4"), ("07:20", "快速", AMBER, "積みプロジェクト", "2"), ("07:41", "特急", RED, "完璧な設計", "5")]
NOTICE = "黄色い線の内側でお待ちください"
# Board B: the same, except these five places.
DEPART_B = [("06:11",) + DEPART[0][1:], ("06:32", "各停", AMBER, "テスト", "2"), DEPART[2], DEPART[3],
            DEPART[4][:4] + ("3",), DEPART[5][:3] + ("完壁な設計", "5")]
NOTICE_B = "黄色い線の外側でお待ちください"
# Where they are: (row, field) -> the characters that differ (None = the whole cell). Row 6 is the notice.
MARKS = {(0, "time"): (4, 5), (1, "kind"): None, (4, "track"): None, (5, "dest"): (1, 2), (6, "notice"): (5, 6)}


def depart_board(name, title, rows, notice, marks=()):
    b = Board("d", LED_X, 58, LED_COLS, 150)
    frames = ""

    def cell(s, cx, cy, col, key, invert=False, right=False):
        """Draw one cell. In the answer picture the part that differs blinks and gets a frame."""
        nonlocal frames
        w = F16.width(s) + (4 if invert else 0)
        cx = cx - w if right else cx
        if key not in marks:
            b.put(F16, s, cx, cy, col, invert=invert)
            return
        a, e = marks[key] or (0, len(s))
        x0, x1 = cx + F16.width(s[:a]), cx + F16.width(s[:e]) + (4 if invert else 0)
        if invert:
            b.put(F16, s, cx, cy, col, invert=True, blink=True)
        else:
            b.put(F16, s[:a], cx, cy, col)
            b.put(F16, s[a:e], x0, cy, col, blink=True)
            b.put(F16, s[e:], cx + F16.width(s[:e]), cy, col)
        frames += (f'<rect x="{b.x + (x0 - 3) * 2}" y="{b.y + (cy - 3) * 2}" width="{(x1 - x0 + 5) * 2}" height="42" rx="4" '
                   f'fill="none" stroke="#ff4a36" stroke-width="2.5"/>')

    for i, (time, kind, col, dest, track) in enumerate(rows):
        y = 4 + i * 20
        cell(time, 5, y, GREEN, (i, "time"))
        cell(kind, 54, y, col, (i, "kind"), invert=True)
        cell(dest, 98, y, AMBER, (i, "dest"))
        cell(track, 397, y, GREEN, (i, "track"), right=True)
    cell(notice, 5, 130, AMBER, (6, "notice"))
    h = 58 + b.h + 17
    heads = (f'<g font-family="{GOTH}" font-size="10.5" fill="#aab0b8"><text x="31" y="50">時刻</text><text x="129" y="50">種別</text>'
             f'<text x="217" y="50">行先</text><text x="815" y="50" text-anchor="end">のりば</text></g>')
    save(name, W, h, casing(W, h, title, "Departures") + heads + b.svg() + seam(b, 125) + frames, title)


def diff_boards():
    depart_board("diff-a.svg", "発車案内 A", DEPART, NOTICE)
    depart_board("diff-b.svg", "発車案内 B", DEPART_B, NOTICE_B)
    depart_board("diff-answer.svg", "発車案内 B(答え)", DEPART_B, NOTICE_B, MARKS)


# --------------------------------------------------------------------------- hooks
def static():
    log_boards()
    diff_boards()
    for n, (ja, en) in enumerate([("ログ読み検定", "LOG READING"), ("本日のサブネット問題", "SUBNET QUIZ"),
                                  ("あみだくじ", "LADDER LOTTERY"), ("発車標の間違い探し", "SPOT THE DIFFERENCE")], 5):
        plate(f"game-{n}.svg", LINE[4], "遊", f"{n:02d}", ja, en)


def live(ctx):
    return {"LOGQUIZ": log_md(), "SUBNET": subnet(ctx["today"]), "AMIDA": amida(ctx)}


if __name__ == "__main__":  # self-check: python3 scripts/ext_games.py
    import datetime

    for rows, options in LOGS:
        assert len(rows) == 6 and sum(ok for _, ok, _ in options) == 1 and len({n for n, _, _ in options}) == 3
        for r in rows:
            assert any(ipaddress.ip_address(r[-4]) in ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")), r
            assert F16.width(r[-2]) <= 176 and all(c == "?" or F16.glyph(c) != F16.glyph("?") for c in "".join(r)), r
    day = datetime.date(2026, 1, 1)
    for k in range(100):
        today = (day + datetime.timedelta(days=k)).isoformat()
        cidr, ask, options, how = subnet_quiz(today)
        net = ipaddress.ip_network(cidr, strict=False)
        assert net.is_private and net.num_addresses >= 4
        assert len({a for a, _, _ in options}) == 3 and sum(ok for _, ok, _ in options) == 1
        good = next(a for a, ok, _ in options if ok)
        want = {"のネ": str(net.network_address), "のブ": str(net.broadcast_address), "で使": f"{net.num_addresses - 2:,} 台"}[ask[:2]]
        assert good == want and str(net.network_address) in how and str(net.broadcast_address) in how, (cidr, good, want)
        assert F16.width(cidr) * 2 <= 390 and subnet_quiz(today) == (cidr, ask, options, how)  # fits the board; same day, same question
        rungs, ends = amida_draw(today)
        assert sorted(ends) == [0, 1, 2, 3] and ends != [0, 1, 2, 3] and len(rungs) == 9
    assert len(DEPART) == len(DEPART_B) and NOTICE != NOTICE_B
    diffs = sum(a != b for ra, rb in zip(DEPART, DEPART_B) for a, b in zip(ra, rb)) + 1
    assert diffs == len(MARKS) == 5, diffs
    for s in [NOTICE, NOTICE_B] + [c for r in DEPART + DEPART_B for c in (r[0], r[1], r[3], r[4])]:
        assert all(F16.glyph(c) != F16.glyph("?") for c in s), s
    print("ext_games ok")
