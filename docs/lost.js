"use strict";
/* The page for an address that does not exist (404.html): the visitor rode past the last station.
   The address that was asked for is shown as plain text, cut short, and never parsed as HTML. */
(() => {
  const { C, Board, width } = LED;
  const $ = id => document.getElementById(id);
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const MSG = "乗り過ごしました。　　この駅はありません。　　折り返しの列車は、下の出口から出ます。　　　";

  let path = location.pathname;
  try { path = decodeURIComponent(path); } catch (e) { /* a broken escape: show it as it came */ }
  $("asked").textContent = "お探しの行先: " + [...path].slice(0, 60).join("") + ([...path].length > 60 ? "…" : "");

  const b = new Board($("board"), [402, 180], [66, 86]);
  function frame(ms) {
    const t = ms / 1000, N = b.narrow, R = b.cols - 5, big = "この駅はありません";
    b.begin();
    b.text("404", 7, 5, C.RED, { invert: true });
    if (N) b.text(big, (b.cols - width(big)) >> 1, 34, C.RED);
    else b.text(big, R, 4, C.RED, { scale: 2, right: true });
    b.ticker(MSG, N ? 66 : 46, C.AMBER, calm ? 0 : t, 22);
    b.end();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
