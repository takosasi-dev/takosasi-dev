"use strict";
/* The station master's office: a locked door that opens for one word. The word is hidden somewhere else
   (not in this site); here are only its SHA-256 sums, so reading this file does not give it away.
   Opening the door presses the extra stamp of the rally, and a visitor who has it finds the door open. */
(() => {
  const { C, Board, width } = LED;
  const $ = id => document.getElementById(id);
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const PALE = "#9fb3c6";
  const SALT = "takosasi-dev/ekicho:";
  const KEYS = ["8d48e73badbc1589bd5c6fefc6508c853e1bff16dc3434de5ede84a1840aaec7",   // the word in Latin letters
                "2c8bbadf3b280169a4e8b77d9b856d0b9f23310abcb057d1d68d69d6b8a3a2da"];  // the word in hiragana

  // Full-width letters, capitals and katakana are the same word.
  const plain = s => s.normalize("NFKC").trim().toLowerCase().replace(/[ァ-ヶ]/g, c => String.fromCharCode(c.charCodeAt(0) - 0x60));
  async function fits(s) {
    const sum = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(SALT + plain(s)));
    return KEYS.includes([...new Uint8Array(sum)].map(b => b.toString(16).padStart(2, "0")).join(""));
  }

  let open = false, wrong = 0, bad = 0, busy = false;   // bad: the board says "wrong key" until this time

  function unlock() {
    open = true;
    Rally.stamp("ekicho");
    const d = new Date(Rally.read().ekicho || Date.now());
    $("when").textContent = `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日`;
    $("lock").hidden = true;
    $("inside").hidden = false;
    $("state").textContent = "開いています";
    $("msg").textContent = "鍵が開きました。";
    $("rally-note").textContent = "構内スタンプラリーの台紙に、7 つ目の印を押しておきました。";
  }

  async function knock() {
    const s = $("word").value;
    if (busy || open || !plain(s)) return;
    busy = true;
    let ok = false;
    try {
      ok = await fits(s);
    } catch (e) {   // no crypto.subtle (a page that is not served over https)
      $("msg").textContent = "この端末では、鍵を確かめられません。";
      busy = false;
      return;
    }
    busy = false;
    if (ok) return unlock();
    wrong++;
    bad = performance.now() + 2000;
    $("msg").textContent = `鍵が合いません(${wrong} 回目)。` + (wrong >= 3 ? "手がかり: 駅前の信号機は、昼も夜も同じ言葉を打っています。" : "");
    $("word").select();
  }
  $("open").addEventListener("click", knock);
  $("word").addEventListener("keydown", e => { if (e.key === "Enter" && !e.isComposing) knock(); });

  const b = new Board($("board"), [402, 180], [66, 86]);
  function frame(ms) {
    const t = ms / 1000, N = b.narrow, R = b.cols - 5, col = open ? C.GREEN : C.RED;
    const big = open ? "開錠" : ms < bad ? "鍵が合いません" : "施錠中", k = N && width(big, 2) > b.cols - 8 ? 1 : 2;
    b.begin();
    b.text("駅長室", 7, 5, col, { invert: true });
    if (N) b.text(big, (b.cols - width(big, k)) >> 1, k === 2 ? 26 : 34, col, { scale: k });
    else {
      if (ms >= bad || calm || t % .5 < .35) b.text(big, 84, 4, col, { scale: 2 });
      if (open || ms >= bad) {   // the long "wrong key" needs the whole row
        b.text(open ? "名誉駅長" : "関係者以外", R, 4, PALE, { right: true });
        b.text(open ? "ご在室" : "立入禁止", R, 22, PALE, { right: true });
      }
    }
    b.ticker(open ? "ようこそ、駅長室へ。　　名誉駅長の席は、窓ぎわにご用意しました。　　お茶はセルフサービスです。　　　"
                  : "関係者以外立入禁止。　　合言葉をご存じの方は、下の欄へどうぞ。　　　", N ? 66 : 46, open ? C.GREEN : C.AMBER, calm ? 0 : t, 22);
    b.end();
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  if (Rally.read().ekicho) {   // has been here before: the door is open
    unlock();
    $("msg").textContent = "";
  }
})();
