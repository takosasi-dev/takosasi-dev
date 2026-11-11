"use strict";
/* The station that is not on the map: a board with no next train, an empty timetable, a stamp for whoever got here. */
(() => {
  const { Board, Sound, width } = LED;
  const $ = id => document.getElementById(id);
  const two = n => String(n).padStart(2, "0");
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const DIM = "#c98a1c", PALE = "#9fb3c6";
  const MSG = "この駅は路線図に載っていません。　　時刻表は白紙です。　　遠くで太鼓と鈴の音がしますが、気のせいでしょう。　　"
    + "線路を歩いて帰るのは危険です。下の出口をご利用ください。　　　";

  const b = new Board($("board"), [402, 180], [66, 86]);
  function frame(ms) {
    const t = ms / 1000, N = b.narrow, R = b.cols - 5;
    b.begin();
    if (calm || t % 9 < 8.82) {   // now and then the board goes dark for a moment
      b.text("次の列車", 7, 5, DIM, { invert: true });
      if (N) {
        b.text("未定", (b.cols - width("未定", 2)) >> 1, 26, DIM, { scale: 2 });
      } else {
        b.text("未定", 84, 4, DIM, { scale: 2 });
        b.text("行先　未定", R, 4, PALE, { right: true });
        b.text("のりば　？", R, 22, PALE, { right: true });
      }
      b.ticker(MSG, N ? 66 : 46, DIM, calm ? 0 : t, 22);
    }
    b.end();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  // The timetable: every hour is there, no minute is.
  for (let h = 5; h <= 24; h++) {
    const tr = $("hours").appendChild(document.createElement("tr"));
    tr.appendChild(document.createElement("th")).textContent = h % 24;
    tr.appendChild(document.createElement("td"));
  }

  const now = new Date();
  $("when").textContent = `${now.getFullYear()}.${two(now.getMonth() + 1)}.${two(now.getDate())} ${two(now.getHours())}:${two(now.getMinutes())}`;

  // Getting here is one of the six stamps of the rally in the concourse.
  Rally.stamp("kisaragi");
  $("rally-note").textContent = "構内スタンプラリーの台紙にも、印を押しておきました。";

  // A drum far away, then small bells.
  $("listen").addEventListener("click", () => {
    for (const at of [0, .9, 1.8, 2.25, 2.7]) Sound.note(62, at, .5, .3);
    for (const [f, at] of [[2637, 3.3], [3136, 3.45], [2637, 3.9], [3136, 4.05], [2794, 4.5]]) Sound.note(f, at, .5, .03);
  });
})();
