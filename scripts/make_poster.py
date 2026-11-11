#!/usr/bin/env python3
"""Make the picture on a project card from a screenshot. Run by hand; the daily workflow never needs it.

    python scripts/make_poster.py <repo> <image file> [where to cut a tall image: 0 = top ... 1 = bottom, default 0.5]

Writes assets/posters/<repo>.jpg (792x356, cropped to fill). Needs Pillow, the only non-standard
library in this repository. A featured repo without a poster gets a plain name plate instead.
"""
import os
import sys

from PIL import Image

W, H = 792, 356  # twice the size it is shown at

if __name__ == "__main__":
    repo, src = sys.argv[1], sys.argv[2]
    im = Image.open(src)
    im.seek(0)
    im = im.convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - W) // 2, round((im.height - H) * float(sys.argv[3] if len(sys.argv) > 3 else 0.5))
    out = os.path.join(os.path.dirname(__file__), "..", "assets", "posters", repo + ".jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.crop((x, y, x + W, y + H)).save(out, "JPEG", quality=74, optimize=True)
    print("wrote", out, os.path.getsize(out))
