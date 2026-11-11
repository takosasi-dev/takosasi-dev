#!/usr/bin/env python3
"""The station behind the ticket gate: the GitHub Pages site in docs/ (https://takosasi-dev.github.io/takosasi-dev/).

    docs/font.js     static(): the LED glyphs the pages need. ASCII, plus every other character
                     found in docs/**/*.html and *.js, so run build_assets.py after editing a page.
    docs/data.json   live(ctx): what the departure board shows, with the glyphs its own text needs.

    python3 scripts/ext_site.py     # self-check

The pages draw text with these glyphs on a canvas, so nothing here ever reaches the DOM as HTML.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

DOCS = os.path.join(ROOT, "docs")


def glyphs(chars):
    """{char: [width, the 16 rows as hex]} in the 16-dot Shinonome font. A character without a glyph gets "?"."""
    out = {}
    for ch in sorted(set(chars)):
        w, rows = F16.glyph(ch)
        out[ch] = [w, "".join(f"{r:0{w // 4}x}" for r in rows)]
    return out


def write(name, text):
    with open(os.path.join(DOCS, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote docs/" + name, len(text))


def static():
    text = ""
    for folder, _, names in os.walk(DOCS):
        for n in names:
            if n.endswith((".html", ".js")) and n != "font.js":
                with open(os.path.join(folder, n), encoding="utf-8") as f:
                    text += f.read()
    chars = {chr(c) for c in range(0x20, 0x7F)} | {c for c in text if ord(c) > 0x7F}
    write("font.js", "window.FONT=" + json.dumps(glyphs(chars), ensure_ascii=False, separators=(",", ":")) + ";\n")


def build(ctx):
    counts = [d["contributionCount"] for w in ctx["cal"]["weeks"] for d in w["contributionDays"]]
    past = counts[:-1] if counts and not counts[-1] else counts  # today may still be empty
    repos = [{
        "name": r["name"],
        "cat": ctx["CAT"][ctx["cat_of"][r["name"]]][1],
        "col": ctx["CAT"][ctx["cat_of"][r["name"]]][5],
        "desc": ctx["DESC"].get(r["name"]) or r["desc"],
        "tag": r["tag"], "tag_date": r["tag_date"], "pushed": r["pushed"],
    } for r in ctx["repos"]]
    data = {
        "updated": ctx["today"],
        "counts": {"repos": len(repos), "releases": sum(r["releases"] for r in ctx["repos"]),
                   "langs": len({r["lang"] for r in ctx["repos"]} - {"-"})},
        "streak": next((i for i, c in enumerate(reversed(past)) if not c), len(past)),
        "idle": next((i for i, c in enumerate(reversed(past)) if c), len(past)),
        "repos": repos,
    }
    data["glyphs"] = glyphs(c for r in repos for v in r.values() for c in v if ord(c) > 0x7F)
    return data


def live(ctx):
    write("data.json", json.dumps(build(ctx), ensure_ascii=False, separators=(",", ":")) + "\n")
    return {}


if __name__ == "__main__":  # self-check
    g = glyphs("Aあ\U0001F600")
    assert g["A"][0] == 8 and len(g["A"][1]) == 32 and g["あ"][0] == 16 and len(g["あ"][1]) == 64
    assert g["\U0001F600"] == glyphs("?")["?"]  # no glyph -> "?", never a crash
    days = [{"contributionCount": c} for c in (0, 3, 1, 2, 0)]
    d = build({"today": "2026-11-11", "cal": {"weeks": [{"contributionDays": days}]}, "cat_of": {"x": "APPS"},
               "CAT": {"APPS": ("apps", "アプリ", "アプリ", "A", "#e5404f", GREEN)}, "DESC": {"x": "説明"},
               "repos": [{"name": "x", "desc": "", "tag": "v1", "tag_date": "2026-11-10", "pushed": "2026-11-11",
                          "lang": "Python", "releases": 2}]})
    assert d["streak"] == 3 and d["idle"] == 0 and d["counts"] == {"repos": 1, "releases": 2, "langs": 1}
    assert d["repos"][0]["cat"] == "アプリ" and set("アプリ説明") <= set(d["glyphs"])
    print("site ok")
