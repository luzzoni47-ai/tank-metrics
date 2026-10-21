"""Guards the mobile layout of the static pages.

Chromium is driven at a 390px viewport and each page is inspected for
horizontal overflow, the inset of its content blocks, and the footer heart.
The prose pages (about/contact/blog and the blog posts) sit in a full-bleed
`.page-wrap`, so they need the same 28px gutter that `.legal-page` gets from
its 10px margin plus 18px padding. Without it their text runs to the screen
edge while the legal pages look inset.
"""

import json
import re
import socket
import subprocess
import sys

import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
WIDTH, HEIGHT = 390, 844
GUTTER = 28
# Served straight from public/ by a plain HTTP server, so the probe and the
# iframes share an origin and can be measured without booting Next.
PAGES = [
    "/site/privacy-policy.html",
    "/site/terms-and-conditions.html",
    "/site/disclaimer.html",
    "/site/about.html",
    "/site/blog.html",
    "/site/contact.html",
    "/site/blog-what-is-ebitda.html",
    "/site/news.html",
    "/site/news-shark-tank-usa-polygons-foldable-spoon-deal.html",
    "/site/tools/sip-calculator.html",
]

PROBE = """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body><pre id="out">pending</pre><script>
const pages = %s, results = [];
let done = 0;
pages.forEach(p => {
  const f = document.createElement('iframe');
  f.style.width = '100%%'; f.style.height = '600px'; f.src = p;
  f.onload = () => {
    try {
      const d = f.contentDocument, de = d.documentElement;
      const overflow = de.scrollWidth - de.clientWidth;
      const insets = {};
      for (const sel of ['.page-hero', '.page-wrap', '.blog-grid', '.legal-page']) {
        const el = d.querySelector(sel);
        if (el) {
          const r = el.getBoundingClientRect(), cs = f.contentWindow.getComputedStyle(el);
          // Legal pages inset via margin, prose pages via padding; what matters
          // is where the text actually starts.
          insets[sel] = {text: Math.round(r.left + parseFloat(cs.paddingLeft) || 0)};
        }
      }
      const hv = d.querySelector('.footer-heart');
      let heart = null;
      if (hv) {
        const r = hv.getBoundingClientRect(), cs = f.contentWindow.getComputedStyle(hv);
        heart = {w: Math.round(r.width), fill: cs.fill};
      }
      results.push({page: p, overflow, insets, heart});
    } catch (e) { results.push({page: p, error: String(e)}); }
    if (++done === pages.length) document.getElementById('out').textContent = JSON.stringify(results);
  };
  document.body.appendChild(f);
});
</script></body></html>
"""


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> int:
    probe = PUBLIC / "_layout_probe.html"
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
             f"--window-size={WIDTH},{HEIGHT}", "--virtual-time-budget=10000",
             "--dump-dom", f"http://127.0.0.1:{port}/_layout_probe.html"],
            capture_output=True, text=True, timeout=180,
        ).stdout
    finally:
        server.terminate()
        probe.unlink(missing_ok=True)

    m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
    if not m:
        print("FAIL: probe produced no output")
        return 1
    import html as html_mod
    data = json.loads(html_mod.unescape(m.group(1)))

    failures = []
    for r in sorted(data, key=lambda x: x["page"]):
        if r.get("error"):
            failures.append(f"{r['page']} -> {r['error']}")
            continue
        if r["overflow"] > 0:
            failures.append(f"{r['page']} overflows horizontally by {r['overflow']}px")
        for sel, box in r["insets"].items():
            if box["text"] != GUTTER:
                failures.append(f"{r['page']} {sel} text starts at {box['text']}px, expected {GUTTER}px")
        heart = r["heart"]
        if not heart:
            failures.append(f"{r['page']} has no .footer-heart")
        else:
            if heart["w"] != 12:
                failures.append(f"{r['page']} heart is {heart['w']}px wide, expected 12px")
            if heart["fill"] != "rgb(234, 67, 53)":
                failures.append(f"{r['page']} heart fill is {heart['fill']}, expected red")

    print(f"pages checked: {len(data)}")
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures:
            print("  " + f)
        return 1
    print(f"ALL PASS: every page keeps a {GUTTER}px mobile gutter and a red footer heart")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
