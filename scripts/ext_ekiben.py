#!/usr/bin/env python3
"""The ekiben stand ("駅弁"): a counter that is on no sign. Standard library only.

Nothing in README points here. Whoever opens an issue titled exactly "ekiben" or "駅弁" is told
today's boxed lunch by .github/workflows/ekiben.yml, which runs `python3 scripts/ext_ekiben.py serve`
and answers with what it prints. Nothing is kept and nothing is committed.

    python3 scripts/ext_ekiben.py                    # self-check
    TITLE=ekiben python3 scripts/ext_ekiben.py serve

The issue title comes from a stranger. Only serve() looks at it, it accepts nothing but the exact
pattern below, and the issue body and the login are never read. The answer is one of the fixed
sentences here, chosen by the date in Japan: nothing the visitor typed is in it. Any other title
gets no answer at all (the workflow then leaves the issue alone).
"""
import datetime
import os
import re
import sys

# Used with fullmatch: nothing before, nothing after. The workflow's "==" does not look at letter case,
# so this does not either; ASCII only, so that no look-alike letter (the Kelvin sign for K) gets through.
TITLE_RE = re.compile(r"ekiben|駅弁", re.IGNORECASE | re.ASCII)

# (name, one line about it). Invented boxes, after the things this profile is made of.
MENU = [
    ("たこめし", "たこの炊き込みごはん。当駅でいちばん古い駅弁です。"),
    ("パケット幕の内", "443 番と 53 番のおかずを通しました。あやしい物は検問で落としています。"),
    ("発車標のり弁", "のりを LED の点の形に切って並べました。離れて見ると「のり」と読めます。"),
    ("鉄壁ファイアウォール重", "三段重ねです。上の段から順に見て、最初に合った段だけ召し上がれます。"),
    ("暴走トロッコ牛めし", "勢いよく盛りました。カーブでは傾けないでください。"),
    ("声色いなり", "食べる人によって味が変わる、と評判のいなり寿司です。"),
    ("八十八鍵ちらし", "具を鍵盤の順に並べました。左から食べると音階になります。"),
    ("草むすび", "緑の濃さが 5 段階のおむすびです。毎日 1 個ずつどうぞ。"),
    ("終電おにぎり", "終電のあとに握った 2 個入り。深夜のコミットのお供に。"),
    ("遅延証明つきカツサンド", "CI が落ちた日のためのカツサンド。遅延証明書を 1 枚お付けします。"),
    ("回送弁当", "ふたを開けても、何も入っていません。回送ですので、お召し上がりにはなれません。"),
    ("404 弁当", "お探しの弁当は見つかりませんでした。包み紙だけお渡しします。"),
]


def serve(title, today):
    """The answer for this title on this day (YYYY-MM-DD), or None when the title is not exactly right."""
    if not isinstance(title, str) or not TITLE_RE.fullmatch(title):
        return None
    name, about = MENU[datetime.date.fromisoformat(today).toordinal() % len(MENU)]
    return (f"本日の駅弁は「{name}」です。{about}\n\n"
            "この売り場は、どの案内にも載っていません。見つけてくださって、ありがとうございます。駅弁は日替わりです。")


def selfcheck():
    day = "2026-11-11"
    for bad in ["", "ekiben ", " ekiben", "ekiben\n", "ekibens", "ekiben: 1", "an ekiben", "ekiben; rm -rf /", "`id`", "$(id)", "ekiben$(id)",
                "駅弁 ", "駅弁ください", "駅弁\n", "eKiben", "ekiben\x00", "ticket", "board: 1", None, 1, b"ekiben"]:
        assert serve(bad, day) is None, bad
    for ok in ["ekiben", "EKIBEN", "Ekiben", "駅弁"]:  # the same box for everybody on the same day
        assert serve(ok, day) == serve("ekiben", day) and "本日の駅弁は「" in serve(ok, day), ok
    start = datetime.date.fromisoformat(day)
    names = [serve("駅弁", (start + datetime.timedelta(days=i)).isoformat()).split("「")[1].split("」")[0] for i in range(len(MENU))]
    assert sorted(names) == sorted(n for n, _ in MENU) and len(set(names)) == len(MENU) >= 12  # a new box every day, each one in turn
    assert all("\n" not in n + a and "@" not in n + a and "`" not in n + a and "<" not in n + a for n, a in MENU)  # plain text: no mention, no markup
    print("ekiben ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["serve"]:
        today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()  # the date in Japan
        answer = serve(os.environ.get("TITLE", ""), today)
        if answer:
            sys.stdout.buffer.write(answer.encode("utf-8") + b"\n")  # UTF-8 whatever the console is set to
    else:
        selfcheck()
