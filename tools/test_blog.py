"""Checks the blog: two-column listing, under-₹10,000 examples, Hindi toggle.

Serves public/ over a plain HTTP server and drives chromium, so it needs no
Next.js build. The Hindi toggle is exercised for real: the button is clicked
and the visibility of the English and Hindi blocks is read back.
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
SITE = PUBLIC / "site"

POSTS = [
    "/site/blog-what-is-ebitda.html",
    "/site/blog-ltv-cac-ratio-explained.html",
    "/site/blog-startup-valuation-explained.html",
    "/site/blog-burn-rate-runway-guide.html",
]
MONEY_LIMIT = 10000

PROBE = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body><pre id="out">pending</pre><script>
const posts = %s;
const gridUrl = '/site/blog.html';
const results = {grid: {}, posts: {}};
function measureGrid(cb) {
  const f = document.createElement('iframe');
  f.style.width = '100%%'; f.style.height = '600px'; f.src = gridUrl;
  f.onload = () => {
    const d = f.contentDocument;
    const g = d.querySelector('.blog-grid');
    const cs = f.contentWindow.getComputedStyle(g);
    const r = g.getBoundingClientRect();
    results.grid = {
      columns: cs.gridTemplateColumns.split(' ').length,
      template: cs.gridTemplateColumns,
      width: Math.round(r.width),
      overflow: d.documentElement.scrollWidth - d.documentElement.clientWidth
    };
    cb();
  };
  document.body.appendChild(f);
}
function measurePosts(cb) {
  let done = 0;
  posts.forEach(p => {
    const f = document.createElement('iframe');
    f.style.width = '100%%'; f.style.height = '600px'; f.src = p;
    f.onload = () => {
      const d = f.contentDocument, w = f.contentWindow;
      const en = d.querySelector('.post-lang[data-lang="en"]');
      const hi = d.querySelector('.post-lang[data-lang="hi"]');
      const btn = d.getElementById('langToggle');
      const rec = {hasEn: !!en, hasHi: !!hi, hasBtn: !!btn};
      if (btn) {
        const body = d.querySelector('.post-lang[data-lang="en"]');
        const meta = d.querySelector('.post-meta');
        const wrap = d.querySelector('.page-wrap');
        rec.btnRight = Math.round(btn.getBoundingClientRect().right);
        rec.wrapRight = Math.round(wrap.getBoundingClientRect().right);
        rec.inMetaRow = meta.contains(btn);
        rec.metaRowAligned = Math.abs(
          Math.round(btn.getBoundingClientRect().top + btn.getBoundingClientRect().height / 2)
          - Math.round(meta.getBoundingClientRect().top + meta.getBoundingClientRect().height / 2)
        ) <= 8;
        rec.switchAboveBody = btn.getBoundingClientRect().bottom <= body.getBoundingClientRect().top + 1;
        rec.visible = w.getComputedStyle(btn).display !== 'none'
          && btn.getBoundingClientRect().height > 0;
        rec.btnHeight = Math.round(btn.getBoundingClientRect().height);
        rec.labelBefore = btn.querySelector('.lang-toggle-label').textContent;
        rec.badgeBefore = (btn.querySelector('.lang-badge') || {}).textContent || '';
      }
      if (en && hi && btn) {
        const hing = d.querySelector('.post-lang[data-lang="hinglish"]');
        rec.hasHinglish = !!hing;
        rec.enHiddenBefore = en.hidden;
        rec.hiHiddenBefore = hi.hidden;
        rec.langBefore = d.documentElement.lang;
        btn.click();
        rec.enHiddenAfter = en.hidden;
        rec.hiHiddenAfter = hi.hidden;
        rec.langAfter = d.documentElement.lang;
        rec.hiVisible = w.getComputedStyle(hi).display !== 'none';
        rec.enVisible = w.getComputedStyle(en).display !== 'none';
        rec.labelAfter = btn.querySelector('.lang-toggle-label').textContent;
        rec.badgeAfter = (btn.querySelector('.lang-badge') || {}).textContent || '';
        btn.click();
        if (hing) {
          rec.hinglishVisible = w.getComputedStyle(hing).display !== 'none'
            && hing.getBoundingClientRect().height > 100;
          rec.enGoneInHinglish = w.getComputedStyle(en).display === 'none';
          rec.hiGoneInHinglish = w.getComputedStyle(hi).display === 'none';
          rec.hinglishLatinOnly = !/[\u0900-\u097F]/.test(hing.textContent);
          rec.hinglishChars = hing.textContent.trim().length;
        }
        btn.click();
        rec.hiHiddenRestored = hi.hidden;
        rec.hingHiddenRestored = hing ? hing.hidden : true;
      }
      results.posts[p] = rec;
      if (++done === posts.length) cb();
    };
    document.body.appendChild(f);
  });
}
measureGrid(() => measurePosts(() => {
  document.getElementById('out').textContent = JSON.stringify(results);
}));
</script></body></html>
"""


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run_probe(width: int) -> dict:
    probe = PUBLIC / "_blog_probe.html"
    probe.write_text(PROBE % json.dumps(POSTS), encoding="utf-8")
    port = free_port()
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=PUBLIC, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}/_blog_probe.html"
    try:
        # Wait until the probe is actually served: a bare TCP connect succeeds
        # while the handler is still starting, which makes chromium race it.
        for _ in range(80):
            try:
                with urllib.request.urlopen(url, timeout=1) as resp:
                    if resp.status == 200:
                        break
            except Exception:
                time.sleep(0.1)
        # Headless chromium occasionally finishes its virtual-time budget before
        # the iframes have settled; a couple of retries keeps the suite stable.
        dom = ""
        for attempt in range(3):
            dom = subprocess.run(
                ["chromium", "--headless", "--disable-gpu", "--no-sandbox",
                 f"--window-size={width},844", "--virtual-time-budget=30000",
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
        raise SystemExit(f"FAIL: probe did not finish (got {payload[:120]!r})")
    return json.loads(payload)


def check_amounts(failures: list) -> None:
    for path in sorted(SITE.glob("blog*.html")):
        body = re.sub(r"<[^>]+>", " ", path.read_text())
        for m in re.finditer(r"₹([\d,]+)", body):
            value = int(m.group(1).replace(",", ""))
            if value >= MONEY_LIMIT:
                failures.append(f"{path.name}: example amount {m.group(0)} is not under ₹{MONEY_LIMIT:,}")


def main() -> int:
    failures = []
    check_amounts(failures)

    desktop = run_probe(1280)
    grid = desktop["grid"]
    if grid.get("columns") != 2:
        failures.append(f"blog listing has {grid.get('columns')} columns at 1280px, expected 2 ({grid.get('template')})")
    if grid.get("overflow", 0) > 0:
        failures.append(f"blog listing overflows at 1280px by {grid['overflow']}px")

    mobile = run_probe(390)
    if mobile["grid"].get("columns") != 1:
        failures.append(f"blog listing has {mobile['grid'].get('columns')} columns at 390px, expected 1")

    for page, rec in desktop["posts"].items():
        if not (rec.get("hasEn") and rec.get("hasHi") and rec.get("hasBtn")):
            failures.append(f"{page}: missing English block, Hindi block or toggle button")
            continue
        if rec["enHiddenBefore"] or not rec["hiHiddenBefore"]:
            failures.append(f"{page}: wrong initial state (en hidden={rec['enHiddenBefore']}, hi hidden={rec['hiHiddenBefore']})")
        if rec["hiHiddenAfter"] or not rec["enHiddenAfter"]:
            failures.append(f"{page}: toggle did not switch languages")
        if not rec["hiVisible"]:
            failures.append(f"{page}: Hindi block is not displayed after toggling")
        if rec["langAfter"] != "hi" or rec["langBefore"] != "en":
            failures.append(f"{page}: lang attribute {rec['langBefore']} -> {rec['langAfter']}, expected en -> hi")
        # The label and badge advertise the *next* mode, so after the first
        # click (now showing Hindi) they read "Hinglish" / "H".
        if rec["labelAfter"] != "Hinglish":
            failures.append(f"{page}: button label after first click is {rec['labelAfter']!r}")
        if rec.get("badgeAfter") != "H":
            failures.append(f"{page}: badge after first click is {rec.get('badgeAfter')!r}")
        if not rec.get("hasHinglish"):
            failures.append(f"{page}: no Hinglish block found")
        elif not rec.get("hinglishVisible"):
            failures.append(f"{page}: Hinglish block is not displayed on the second click")
        elif not rec.get("enGoneInHinglish") or not rec.get("hiGoneInHinglish"):
            failures.append(f"{page}: English/Hindi still visible in Hinglish mode")
        elif not rec.get("hinglishLatinOnly"):
            failures.append(f"{page}: Hinglish block still contains Devanagari")
        if not rec["hiHiddenRestored"]:
            failures.append(f"{page}: third click did not return to English")
        if not rec.get("hingHiddenRestored"):
            failures.append(f"{page}: Hinglish block still visible after returning to English")
        if not rec.get("visible"):
            failures.append(f"{page}: language switch is not visible")
        if rec.get("labelBefore") != "हिंदी":
            failures.append(f"{page}: switch label is {rec.get('labelBefore')!r}")
        if rec.get("badgeBefore") != "अ":
            failures.append(f"{page}: switch badge is {rec.get('badgeBefore')!r}")
        if not rec.get("inMetaRow"):
            failures.append(f"{page}: switch is not on the category/date line")
        if not rec.get("metaRowAligned"):
            failures.append(f"{page}: switch is not vertically aligned with the meta row")
        if abs(rec.get("btnRight", 0) - rec.get("wrapRight", 0)) > 40:
            failures.append(
                f"{page}: switch not right-aligned (right={rec.get('btnRight')}, "
                f"content right={rec.get('wrapRight')})"
            )
        if rec.get("btnHeight", 99) > 26:
            failures.append(f"{page}: switch is too tall ({rec.get('btnHeight')}px), expected a small badge")
        if not rec.get("switchAboveBody"):
            failures.append(f"{page}: switch does not sit above the article body")

    print(f"posts checked: {len(desktop['posts'])}")
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures:
            print("  " + f)
        return 1
    print("ALL PASS: 2-column listing, every example under ₹10,000, Hindi toggle works")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
