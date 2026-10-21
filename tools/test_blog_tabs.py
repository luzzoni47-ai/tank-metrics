"""Checks the blog tab switch: Guides vs All News panes swap on click."""
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

PROBE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>iframe{width:390px;height:844px;border:0}</style></head><body>
<iframe id="f" src="/site/blog.html"></iframe><pre id="out">pending</pre>
<script>
var out=document.getElementById('out');
function vis(el){return !!(el&&el.offsetParent!==null&&!el.hidden);}
document.getElementById('f').addEventListener('load',function(){
  var w=this.contentWindow,d=this.contentDocument;
  function snap(){
    var tg=d.getElementById('tabGuides'),tn=d.getElementById('tabNews');
    var pg=d.getElementById('paneGuides'),pn=d.getElementById('paneNews');
    return {
      guides_visible: vis(pg), news_visible: vis(pn),
      guides_active: tg.classList.contains('active'),
      news_active: tn.classList.contains('active'),
      news_cards: pn?pn.querySelectorAll('.blog-card').length:-1,
      guide_cards: pg?pg.querySelectorAll('.blog-card').length:-1,
      labels: [].map.call(d.querySelectorAll('.blog-tab'),function(b){return b.textContent.trim();})
    };
  }
  var r={initial:snap()};
  d.getElementById('tabNews').click();
  r.after_news=snap();
  d.getElementById('tabGuides').click();
  r.after_guides=snap();
  out.textContent=JSON.stringify(r);
});
</script></body></html>"""


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def main() -> int:
    probe = PUBLIC / "_tab_probe.html"
    probe.write_text(PROBE, encoding="utf-8")
    port = free_port()
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=PUBLIC, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}/_tab_probe.html"
    try:
        for _ in range(80):
            try:
                with urllib.request.urlopen(url, timeout=1) as resp:
                    if resp.status == 200:
                        break
            except Exception:
                time.sleep(0.1)
        dom = ""
        for _ in range(3):
            dom = subprocess.run(
                ["chromium", "--headless", "--disable-gpu", "--no-sandbox",
                 "--window-size=390,844", "--virtual-time-budget=30000",
                 "--dump-dom", url],
                capture_output=True, text=True, timeout=240,
            ).stdout
            m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
            if m and html_mod.unescape(m.group(1)).strip().startswith("{"):
                break
            time.sleep(1)
    finally:
        server.terminate()
        probe.unlink(missing_ok=True)

    m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
    if not m:
        raise SystemExit("FAIL: probe produced no output")
    payload = html_mod.unescape(m.group(1)).strip()
    if not payload.startswith("{"):
        raise SystemExit(f"FAIL: probe did not finish ({payload[:160]!r})")
    r = json.loads(payload)
    print(json.dumps(r, indent=1))

    fails = []
    if not (r["initial"]["guides_visible"] and not r["initial"]["news_visible"]):
        fails.append("default view is not Guides-only")
    if not (r["initial"]["guides_active"] and not r["initial"]["news_active"]):
        fails.append("default active tab is not Guides")
    if not (r["after_news"]["news_visible"] and not r["after_news"]["guides_visible"]):
        fails.append("clicking All News did not reveal the news pane")
    if not (r["after_news"]["news_active"] and not r["after_news"]["guides_active"]):
        fails.append("clicking All News did not move the active state")
    if not (r["after_guides"]["guides_visible"] and not r["after_guides"]["news_visible"]):
        fails.append("clicking Guides did not restore the guides pane")
    if r["initial"]["news_cards"] < 1:
        fails.append("news pane holds no cards")
    if r["initial"]["guide_cards"] < 1:
        fails.append("guides pane holds no cards")

    if fails:
        for f in fails:
            print("FAIL:", f)
        return 1
    print("ALL PASS: Guides and All News swap both ways on click")
    return 0


if __name__ == "__main__":
    sys.exit(main())
