#!/usr/bin/env python3
"""Guard the site-wide menu drawer.

Every page carries a three-dot button. On the home page it opens the category
sidebar; on the other 123 pages it must open the drawer from `nav.js`, and the
close control must sit at the BOTTOM of that drawer (Sir asked for it there).
The button used to be `visibility:hidden` on those pages and wired to nothing,
so a visitor who arrived on a calculator from Google had no route to the blog,
the news or another tool.

The behaviour is checked in a real browser at phone width, because the whole
point is what a thumb can reach. Run with `--static` to check the markup only.
"""
import html as html_mod
import json
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SITE = PUBLIC / "site"

# One tool page (the case Sir described), plus a blog post and a static page.
PAGES = [
    "/site/tools/loan-emi-calculator.html",
    "/site/blog-what-is-ebitda.html",
    "/site/about.html",
]

PROBE = r"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>html,body{margin:0}iframe{width:390px;height:844px;border:0}</style></head>
<body><iframe id="f"></iframe><pre id="out">pending</pre><script>
var pages = %s, i = 0, results = [];
function next() {
  if (i >= pages.length) { document.getElementById('out').textContent = JSON.stringify(results); return; }
  var f = document.getElementById('f');
  f.onload = function () {
    var d = f.contentDocument, w = f.contentWindow;
    setTimeout(function () {
      var rec = {page: pages[i]};
      var btn = d.getElementById('menuBtn');
      if (!btn) { rec.error = 'no menu button'; results.push(rec); i++; next(); return; }
      rec.btnDisplay = w.getComputedStyle(btn).display;
      rec.btnVisible = btn.getBoundingClientRect().width > 0;
      rec.btnText = (btn.textContent || '').trim();
      btn.click();
      setTimeout(function () {
        var dr = d.querySelector('.nav-drawer');
        rec.drawerBuilt = !!dr;
        rec.drawerOpen = !!dr && dr.classList.contains('open');
        if (dr) {
          var c = d.querySelector('.nav-drawer-close');
          var r = dr.getBoundingClientRect();
          var cr = c ? c.getBoundingClientRect() : null;
          rec.closeGapFromBottom = cr ? Math.round(r.bottom - cr.bottom) : null;
          rec.closeWidthVsDrawer = cr ? Math.round(cr.width) : null;
          rec.drawerWidth = Math.round(r.width);
          rec.closeText = c ? (c.textContent || '').trim() : '';
          rec.links = [].map.call(d.querySelectorAll('.nav-drawer-links a'),
                                   function (a) { return a.textContent; });
          rec.tools = d.querySelectorAll('.nav-drawer-tools a').length;
          rec.scrimOpen = !!d.querySelector('.nav-scrim.open');
          rec.bodyLocked = d.documentElement.classList.contains('nav-open');
          if (c) {
            c.click();
            rec.closedAfterClick = !dr.classList.contains('open');
            rec.unlockedAfterClick = !d.documentElement.classList.contains('nav-open');
          }
        }
        results.push(rec);
        i++;
        next();
      }, 650);
    }, 900);
  };
  f.src = pages[i];
}
next();
</script></body></html>
"""


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def check_markup() -> list:
    """Every page loads nav.js and shows a three-dot button, home excluded."""
    failures = []
    pages = [SITE / "index.html"]
    pages += sorted(SITE.glob("*.html"))
    pages += sorted((SITE / "tools").glob("*.html"))
    for page in sorted(set(pages)):
        text = page.read_text(encoding="utf-8", errors="replace")
        rel = page.relative_to(PUBLIC)
        if "/site/nav.js" not in text:
            failures.append(f"{rel} does not load nav.js")
        m = re.search(r'<button[^>]*id="menuBtn"[^>]*>(.*?)</button>', text)
        if not m:
            failures.append(f"{rel} has no menuBtn button")
            continue
        if "visibility:hidden" in m.group(0):
            failures.append(f"{rel} hides the menu button, so the drawer is unreachable")
        if "\u2022" not in m.group(1):
            failures.append(f"{rel} menu button is not the three dots: {m.group(1)!r}")
    return failures


def check_drawer() -> list:
    failures = []
    probe = PUBLIC / "_nav_probe.html"
    probe.write_text(PROBE % json.dumps(PAGES), encoding="utf-8")
    port = free_port()
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=PUBLIC, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(40):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                    break
            except OSError:
                time.sleep(0.1)
        dom = subprocess.run(
            ["chromium", "--headless", "--disable-gpu", "--no-sandbox",
             "--window-size=390,844", "--virtual-time-budget=40000",
             "--dump-dom", f"http://127.0.0.1:{port}/_nav_probe.html"],
            capture_output=True, text=True, timeout=200,
        ).stdout
    finally:
        server.terminate()
        probe.unlink(missing_ok=True)

    m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
    if not m:
        return ["nav probe produced no output"]
    try:
        data = json.loads(html_mod.unescape(m.group(1)))
    except json.JSONDecodeError:
        return [f"nav probe returned unreadable data: {m.group(1)[:200]}"]

    for rec in data:
        page = rec["page"]
        if rec.get("error"):
            failures.append(f"{page} -> {rec['error']}")
            continue
        if not rec.get("btnVisible"):
            failures.append(f"{page} menu button is not visible")
        if rec.get("btnText") != "\u2022\u2022\u2022":
            failures.append(f"{page} menu button text is {rec.get('btnText')!r}")
        if not rec.get("drawerBuilt"):
            failures.append(f"{page} clicking the menu built no drawer")
            continue
        if not rec.get("drawerOpen"):
            failures.append(f"{page} drawer did not open")
        if not rec.get("links"):
            failures.append(f"{page} drawer has no navigation links")
        if not rec.get("tools"):
            failures.append(f"{page} drawer lists no popular calculators")
        if not rec.get("scrimOpen"):
            failures.append(f"{page} drawer opened without a scrim")
        if not rec.get("bodyLocked"):
            failures.append(f"{page} page still scrolls behind the open drawer")
        gap = rec.get("closeGapFromBottom")
        if gap is None:
            failures.append(f"{page} drawer has no close button")
        elif gap > 30:
            failures.append(
                f"{page} close button sits {gap}px above the drawer bottom, "
                "but Sir wants it at the bottom")
        if rec.get("closeWidthVsDrawer", 0) < rec.get("drawerWidth", 0) * 0.7:
            failures.append(f"{page} close button is not a full-width target")
        if not rec.get("closedAfterClick"):
            failures.append(f"{page} close button did not close the drawer")
        if not rec.get("unlockedAfterClick"):
            failures.append(f"{page} scrolling stayed locked after closing")
    return failures


def main() -> int:
    failures = check_markup()
    if "--static" not in sys.argv:
        try:
            failures += check_drawer()
        except FileNotFoundError:
            print("skip browser check: chromium not available")
        except Exception as e:
            failures.append(f"drawer check errored: {e}")
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures[:25]:
            print("  -", f)
        return 1
    print("ALL PASS: three-dot menu opens a drawer on every page, close at the bottom")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
