#!/usr/bin/env python3
"""A QR code drawn in LED dots that a phone can really read. It leads to the hidden station.

    python3 scripts/ext_qr.py     # self-check

build_assets.py calls static() -> assets/qr.svg. The lit dots are the light modules and the unlit
ones the dark modules, so the code has the usual polarity (dark on light) and old readers take it too.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from style import *  # noqa: E402,F403

URL = "https://takosasi-dev.github.io/takosasi-dev/kisaragi/"
# The modules for URL: version 4 (33x33), error correction M, byte mode. "1" is a dark module.
# Made once on a PC with OpenCV (cv2.QRCodeEncoder) and pasted here, so the build needs no QR library.
# If URL changes, make it again; the picture was checked by reading a screenshot back with cv2.QRCodeDetector.
QR = """
111111101111000011111001001111111
100000101100001010101101101000001
101110100110111010101001001011101
101110101110100000110010101011101
101110100100110011011000101011101
100000100100001111111010101000001
111111101010101010101010101111111
000000001111100111101010100000000
101101110101000111100101101001011
010001010010110011110011001101101
111011101101110000101001100111011
001011010101100101001001100101000
001101101111101010000011100111000
100001000001001000010010000101110
010100110110110000011110001101100
101001010111101100011111011101100
000010110001100000100111011011100
101110001111001110101011101011011
001000110001110100101000011110110
011001010100110101100010011010001
111110100110110010010101100101100
100001010101100110011001001001001
001000111000010101100001111100111
011111000111011100010000110011000
111001110001001001000000111111010
000000001010001110010001100011010
111111101101011001110011101010000
100000101000110111101111100011111
101110100101111011101111111110110
101110101011011011001101000100001
101110101111100110100110101101000
100000100010110001011011111110001
111111101100110001110101010010100
""".split()
QUIET, K = 3, 3      # light modules around the code; LEDs per module, each way
SIDE = (len(QR) + QUIET * 2) * K
WHITE = "#fff1d0"


def static():
    n = len(QR)
    lit = [[not (QUIET <= r < QUIET + n and QUIET <= c < QUIET + n and QR[r - QUIET][c - QUIET] == "1")
            for c in range(n + QUIET * 2) for _ in range(K)] for r in range(n + QUIET * 2) for _ in range(K)]
    q = Board("q", LED_X, 40, SIDE, SIDE)
    q.raw(lit, 0, 0, WHITE)
    x = LED_X + q.w + 14
    t = Board("k", x, 40, (W - LED_X - x) // 2, SIDE)
    t.put(F16, "臨時のりば", 7, 6, RED, invert=True)
    t.put(F16, "0 番線", t.cols - 6, 6, AMBER, right=True)
    t.put(F16, "隠し駅ゆき", 6, 30, AMBER, scale=2)
    t.put(F16, "スマホのカメラをかざしてください", 6, 72, GREEN)
    t.ticker(F16, "この列車は路線図に載っていません。時刻表は白紙です。お乗りまちがいにご注意ください。　　　", 98, AMBER)
    h = 40 + q.h + 17
    save("qr.svg", W, h, casing(W, h, "連絡のりば", "Transfer", "LED の点で描いた、本当に読める QR")
         + q.svg() + t.svg() + seam(t, 26) + seam(t, 66) + seam(t, 93),
         f"LED の点で描いた QR コード。スマホのカメラで読むと隠し駅へ行ける。行き先: {URL}")


if __name__ == "__main__":  # self-check
    n = len(QR)
    assert n == 33 and all(len(r) == n and set(r) <= {"0", "1"} for r in QR)
    eye = ["1111111", "1000001", "1011101", "1011101", "1011101", "1000001", "1111111"]
    for r0, c0 in ((0, 0), (0, n - 7), (n - 7, 0)):  # the three corner marks
        assert [QR[r0 + i][c0:c0 + 7] for i in range(7)] == eye, (r0, c0)
    assert QR[6][8:n - 8] == ("10" * n)[:n - 16]  # the timing row alternates
    assert SIDE == 117
    print("qr ok")
