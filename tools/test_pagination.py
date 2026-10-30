"""Guards the phone pager on the listing pages.

Sir asked for /blog and /news to show 10 cards at a time on a phone, with a
numbered pager underneath in the logo's colours. The behaviour is one script
(pagination.js) toggling `.page-hidden`, so the things that can silently break
are: the script not being wired into a page, the first page not being sliced to
10, a tap on "2" not revealing the next 10, the desktop view losing cards, and
the pager buttons not carrying the palette.

Chromium is driven at a 390px viewport (phone) and at 1200px (desktop). Each
check is measured from the rendered DOM, not from the source, because the pager
is built at runtime.
"""
import html as html_mod
import json
import re
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"

PROBE = """<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
<iframe id="f" style="width:%(w)dpx;height:900px;border:0" src="%(src)s"></iframe>
<pre id="out">pending</pre>
<script>
var out=document.getElementById('out');
function vis(el){return !!(el&&!el.classList.contains('page-hidden'));}
document.getElementById('f').addEventListener('load',function(){
  var w=this.contentWindow,d=this.contentDocument;
  function snap(){
    var g=d.querySelector('#paneGuides .blog-grid')||d.querySelector('.blog-grid');
    var cards=g?[].slice.call(g.querySelectorAll('.blog-card')):[];
    var nav=d.querySelector('.page-nav');
    var nums=nav?[].slice.call(nav.querySelectorAll('.page-num')):[];
    return {
      cards: cards.length,
      visible: cards.filter(vis).length,
      pager: !!nav,
      nums: nums.length,
      labels: nums.map(function(b){return b.textContent.trim();}),
      colors: nums.map(function(b){return b.style.getPropertyValue('--pg');}),
      active: nums.findIndex(function(b){return b.classList.contains('active');})
    };
  }
  var r={initial:snap()};
  var nav=d.querySelector('.page-nav');
  if(nav){
    var nums=nav.querySelectorAll('.page-num');
    if(nums[1]) nums[1].click();
    r.after_page2=snap();
    if(nums[0]) nums[0].click();
    r.back_page1=snap();
  }
  out.textContent=JSON.stringify(r);
});
</script></body></html>"""


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def run(src: str, width: int, port: int) -> dict:
    probe = PUBLIC / "_pager_probe.html"
    probe.write_text(PROBE % {"w": width, "src": src}, encoding="utf-8")
    url = f"http://127.0.0.1:{port}/_pager_probe.html"
    dom = ""
    try:
        for _ in range(3):
            dom = subprocess.run(
                ["chromium", "--headless", "--disable-gpu", "--no-sandbox",
                 f"--window-size={width},1000", "--virtual-time-budget=30000",
                 "--dump-dom", url],
                capture_output=True, text=True, timeout=240,
            ).stdout
            m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
            if m and html_mod.unescape(m.group(1)).strip().startswith("{"):
                break
            time.sleep(1)
    finally:
        probe.unlink(missing_ok=True)
    m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
    if not m:
        raise SystemExit(f"FAIL: probe produced no output for {src}")
    payload = html_mod.unescape(m.group(1)).strip()
    if not payload.startswith("{"):
        raise SystemExit(f"FAIL: probe did not finish for {src} ({payload[:160]!r})")
    return json.loads(payload)


def main() -> int:
    port = free_port()
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=PUBLIC, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(80):
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/site/blog.html", timeout=1
                ) as resp:
                    if resp.status == 200:
                        break
            except Exception:
                time.sleep(0.1)

        fails = []
        for src in ("/site/blog.html", "/site/news.html"):
            # --- phone: 10 cards, a pager, and a working tap ---
            r = run(src, 390, port)
            init = r["initial"]
            print(f"{src} @390: {json.dumps(init)}")
            if not init["pager"]:
                fails.append(f"{src}: no pager on a phone")
                continue
            if init["visible"] != 10:
                fails.append(
                    f"{src}: first page shows {init['visible']} cards, expected 10"
                )
            if init["cards"] < 11:
                fails.append(f"{src}: only {init['cards']} cards, pager not needed")
            if init["active"] != 0:
                fails.append(f"{src}: first page is not active on load")
            if init["labels"] != [str(i + 1) for i in range(init["nums"])]:
                fails.append(
                    f"{src}: numbers are {init['labels']}, expected "
                    f"1..{init['nums']}"
                )
            if init["nums"] != -(-init["cards"] // 10):
                fails.append(
                    f"{src}: {init['nums']} numbers for {init['cards']} cards"
                )
            # The palette, in order, from the logo.
            want = ["#34a853", "#4285f4", "#ea4335", "#f2a600", "#7b8794"]
            for i, c in enumerate(init["colors"][:5]):
                if c != want[i]:
                    fails.append(f"{src}: page {i+1} colour is {c!r}, expected {want[i]!r}")
            # --- tap 2, then back to 1 ---
            if "after_page2" in r:
                p2 = r["after_page2"]
                if p2["visible"] != min(10, init["cards"] - 10):
                    fails.append(
                        f"{src}: page 2 shows {p2['visible']} cards, expected "
                        f"{min(10, init['cards'] - 10)}"
                    )
                if p2["active"] != 1:
                    fails.append(f"{src}: tapping 2 did not move the active number")
                b1 = r.get("back_page1", {})
                if b1.get("visible") != 10 or b1.get("active") != 0:
                    fails.append(f"{src}: tapping 1 did not return to the first page")

            # --- desktop: every card, no pager ---
            d = run(src, 1200, port)["initial"]
            print(f"{src} @1200: {json.dumps(d)}")
            if d["pager"]:
                fails.append(f"{src}: pager is showing on a desktop")
            if d["visible"] != d["cards"]:
                fails.append(
                    f"{src}: desktop hides cards ({d['visible']} of {d['cards']} visible)"
                )
    finally:
        server.terminate()

    if fails:
        for f in fails:
            print("FAIL:", f)
        return 1
    print("ALL PASS: 10 cards per phone page, pager works, desktop untouched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
