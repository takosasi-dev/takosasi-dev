#!/usr/bin/env python3
"""Station name signs for the featured repos: assets/stations/<repo>.svg. Standard library only.

The featured repos form a loop line. Each repo's own README shows its sign (the image is served from
this repo, so it follows the line when the featured set changes) and two text links that go through
docs/line/, which looks the neighbours up in docs/data.json. Nothing in the other READMEs goes stale.

    python3 scripts/ext_stations.py            # self-check
    python3 scripts/ext_stations.py snippet    # the lines to paste into each repo's README
"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

USER = "takosasi-dev"
RAW = f"https://raw.githubusercontent.com/{USER}/{USER}/main/assets/stations"
LINE_URL = f"https://{USER}.github.io/{USER}/line/"


def neighbours(feat, i):
    """(previous, next) on the loop."""
    return feat[i - 1], feat[(i + 1) % len(feat)]


def sign(i, feat, col, sym):
    (repo, name), ((_, prev), (_, nxt)) = feat[i], neighbours(feat, i)
    # 800 wide and shown at 640 in the READMEs, so the neighbours on the band stay readable.
    size = min(42, 560 / max(len(name), 1))  # long names shrink instead of running into the corners
    body = (
        f'<g font-family="{GOTH}"><rect x="2" y="4" width="796" height="122" rx="7" fill="{PLATE}" stroke="{PLATE_EDGE}" stroke-width="2"/>'
        f'<rect x="3" y="78" width="794" height="34" fill="{col}"/>'
        f'<circle cx="52" cy="42" r="25" fill="#fff" stroke="{col}" stroke-width="7"/>'
        f'<text x="52" y="39" text-anchor="middle" font-size="16" font-weight="800" fill="#111">{sym}</text>'
        f'<text x="52" y="56" text-anchor="middle" font-size="15" font-weight="800" fill="#111">{i + 1:02d}</text>'
        f'<text x="400" y="{40 + size * .36:.0f}" text-anchor="middle" font-size="{size:.0f}" font-weight="700" fill="#111" letter-spacing="2">{esc(name)}</text>'
        f'<text x="400" y="72" text-anchor="middle" font-size="12" fill="#666" letter-spacing="3" font-family="{MONO}">{esc(repo.upper())}</text>'
        f'<text x="22" y="102" font-size="19" font-weight="700" fill="#fff">◀ {esc(prev)}</text>'
        f'<text x="778" y="102" text-anchor="end" font-size="19" font-weight="700" fill="#fff">{esc(nxt)} ▶</text>'
        f'<text x="400" y="101" text-anchor="middle" font-size="13" font-weight="700" fill="#fff" opacity=".85" letter-spacing="3">たこさし線</text>'
        f'<text x="778" y="30" text-anchor="end" font-size="12" fill="#666" font-family="{MONO}" letter-spacing="2">TAKOSASI-DEV LINE</text></g>')
    save(f"stations/{repo}.svg", 800, 130, body, f"たこさし線 {name} 駅。前の駅は {prev}、次の駅は {nxt}")


def snippet(repo):
    """What goes at the end of a featured repo's README. It never needs editing again: the picture and the
    two links follow the line by themselves."""
    return (f'<!-- takosasi-dev line: the sign and the links follow https://github.com/{USER}/{USER} -->\n'
            f'<p align="center">\n'
            f'<a href="https://github.com/{USER}"><img src="{RAW}/{repo}.svg" width="640" alt="たこさし線の駅名標(作者のほかの制作物へ)"></a><br>\n'
            f'<a href="{LINE_URL}?from={repo}&amp;go=prev">◀ 前の駅</a> ・ '
            f'<a href="https://github.com/{USER}">路線図</a> ・ '
            f'<a href="{LINE_URL}?from={repo}&amp;go=next">次の駅 ▶</a>\n'
            f'</p>\n')


def live(ctx):
    feat = ctx["feat"]
    os.makedirs(os.path.join(ROOT, "assets", "stations"), exist_ok=True)
    for old in glob.glob(os.path.join(ROOT, "assets", "stations", "*.svg")):  # signs of repos that left the line
        os.remove(old)
    for i, (repo, _) in enumerate(feat):
        _, _, _, sym, col, _ = ctx["CAT"][ctx["cat_of"][repo]]
        sign(i, feat, col, sym)
    return {}


if __name__ == "__main__":
    f = [("a", "A"), ("b", "B"), ("c", "C")]
    assert neighbours(f, 0) == (("c", "C"), ("b", "B")) and neighbours(f, 2) == (("b", "B"), ("a", "A"))
    assert neighbours(f[:1], 0) == (("a", "A"), ("a", "A"))  # a line of one station points at itself
    assert "from=koe-loom&amp;go=next" in snippet("koe-loom")
    if sys.argv[1:] == ["snippet"]:
        import json
        with open(os.path.join(ROOT, "docs", "data.json"), encoding="utf-8") as fh:
            for s in json.load(fh)["line"]:
                print(f"--- {s['repo']}\n{snippet(s['repo'])}")
    print("stations ok")
