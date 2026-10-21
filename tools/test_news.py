#!/usr/bin/env python3
"""Guards the news desk.

Checks the shape of tools/news.json before anything is rendered, then drives
chromium over the built pages to confirm the Hinglish toggle really swaps the
bodies. The JSON checks matter most: a story with a mismatched heading count or
a stray Devanagari character would ship a broken language switch.

    python3 tools/test_news.py
"""
import html as html_mod
import json
import re
import socket
import subprocess
import sys
import threading
import http.server
import functools
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SITE = PUBLIC / "site"
NEWS = json.loads((ROOT / "tools" / "news.json").read_text(encoding="utf-8"))

REQUIRED = ["slug", "title", "dek", "category", "date", "date_display",
            "source_name", "body_en", "body_hinglish"]


def check_json(failures: list) -> None:
    seen = set()
    for it in NEWS["items"]:
        for key in REQUIRED:
            if not it.get(key):
                failures.append(f"{it.get('slug', '?')}: missing {key}")
        slug = it.get("slug", "")
        if slug in seen:
            failures.append(f"{slug}: duplicate slug")
        seen.add(slug)
        if not re.fullmatch(r"[a-z0-9-]+", slug):
            failures.append(f"{slug}: slug must be lowercase words joined by dashes")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", it.get("date", "")):
            failures.append(f"{slug}: date must be YYYY-MM-DD")

        en, hi = it.get("body_en", []), it.get("body_hinglish", [])
        if not en or not hi:
            continue
        en_heads = sum(len(re.findall(r"<h[23][ >]", b)) for b in en)
        hi_heads = sum(len(re.findall(r"<h[23][ >]", b)) for b in hi)
        if en_heads != hi_heads:
            failures.append(
                f"{slug}: English has {en_heads} headings, Hinglish has {hi_heads}")
        if en_heads < 4:
            failures.append(f"{slug}: only {en_heads} headings, too thin for a news page")
        dev = re.findall(r"[\u0900-\u097F]", " ".join(hi))
        if dev:
            failures.append(f"{slug}: Hinglish block contains Devanagari "
                            f"({''.join(sorted(set(dev)))[:20]})")

        words = len(re.sub(r"<[^>]+>", " ", " ".join(en)).split())
        if words < 400:
            failures.append(f"{slug}: English body is {words} words, expected 400+")

        cta = it.get("cta") or {}
        for key in ("text", "href", "label"):
            if not cta.get(key):
                failures.append(f"{slug}: cta missing {key}")


def check_pages(failures: list) -> None:
    for it in NEWS["items"]:
        p = SITE / f"news-{it['slug']}.html"
        if not p.exists():
            failures.append(f"{it['slug']}: page not generated")
            continue
        t = p.read_text(encoding="utf-8")
        for need in ("<title>", 'name="description"', 'rel="canonical"',
                     "NewsArticle", "BreadcrumbList", 'data-lang="en"',
                     'data-lang="hinglish"', 'id="langToggle"',
                     "G-MHZ0V6HFC6", it["cta"]["href"]):
            if need not in t:
                failures.append(f"{it['slug']}: page lacks {need}")
        if t.count("<h1>") != 1:
            failures.append(f"{it['slug']}: page has {t.count('<h1>')} h1 tags, expected 1")

    idx = SITE / "news.html"
    if not idx.exists():
        failures.append("/news index not generated")
        return
    t = idx.read_text(encoding="utf-8")
    for it in NEWS["items"]:
        if f'href="/{it["slug"]}"' not in t:
            failures.append(f"/news index does not link {it['slug']}")


PROBE = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body><pre id="out">pending</pre><script>
const pages = %s, results = {};
let done = 0;
pages.forEach(p => {
  const f = document.createElement('iframe');
  f.style.width = '100%%'; f.style.height = '600px'; f.src = p;
  f.onload = () => {
    const d = f.contentDocument, w = f.contentWindow;
    const btn = d.getElementById('langToggle');
    const en = d.querySelector('.post-lang[data-lang="en"]');
    const hi = d.querySelector('.post-lang[data-lang="hinglish"]');
    const rec = {};
    if (btn && en && hi) {
      rec.enVisibleBefore = !en.hidden;
      rec.hiHiddenBefore = hi.hidden;
      btn.click();
      rec.enHiddenAfter = en.hidden;
      rec.hiVisibleAfter = !hi.hidden;
      rec.langAfter = d.documentElement.lang;
      rec.labelAfter = d.querySelector('.lang-toggle-label').textContent;
      rec.badgeAfter = d.querySelector('.lang-badge').textContent;
      btn.click();
      rec.backToEnglish = !en.hidden && hi.hidden;
      rec.labelRestored = d.querySelector('.lang-toggle-label').textContent;
    }
    results[p] = rec;
    if (++done === pages.length) document.getElementById('out').textContent = JSON.stringify(results);
  };
  document.body.appendChild(f);
});
</script></body></html>
"""


def run_probe(width: int) -> dict:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(PUBLIC))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    pages = [f"/site/news-{it['slug']}.html" for it in NEWS["items"]]
    probe = PUBLIC / "_newsprobe.html"
    probe.write_text(PROBE % json.dumps(pages), encoding="utf-8")
    url = f"http://127.0.0.1:{port}/_newsprobe.html"
    dom = ""
    try:
        for _ in range(3):
            dom = subprocess.run(
                ["chromium", "--headless", "--disable-gpu", "--no-sandbox",
                 f"--window-size={width},844", "--virtual-time-budget=30000",
                 "--dump-dom", url],
                capture_output=True, text=True, timeout=240,
            ).stdout
            m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
            if m and html_mod.unescape(m.group(1)).strip().startswith("{"):
                break
        m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
        if not m:
            raise SystemExit("FAIL: news probe produced no output")
        return json.loads(html_mod.unescape(m.group(1)))
    finally:
        server.shutdown()
        server.server_close()
        probe.unlink(missing_ok=True)


def check_toggle(failures: list) -> None:
    results = run_probe(1280)
    for page, rec in results.items():
        if not rec:
            failures.append(f"{page}: no toggle found")
            continue
        if not rec.get("enVisibleBefore") or not rec.get("hiHiddenBefore"):
            failures.append(f"{page}: Hinglish block is not hidden on load")
        if not rec.get("enHiddenAfter") or not rec.get("hiVisibleAfter"):
            failures.append(f"{page}: toggle did not swap to Hinglish")
        if rec.get("langAfter") != "hi-Latn":
            failures.append(f"{page}: lang attribute after toggle is {rec.get('langAfter')!r}")
        if rec.get("labelAfter") != "English":
            failures.append(f"{page}: label after toggle is {rec.get('labelAfter')!r}")
        if rec.get("badgeAfter") != "A":
            failures.append(f"{page}: badge after toggle is {rec.get('badgeAfter')!r}")
        if not rec.get("backToEnglish"):
            failures.append(f"{page}: second click did not return to English")


def main() -> int:
    failures: list = []
    check_json(failures)
    check_pages(failures)
    if not failures:
        check_toggle(failures)
    print(f"stories checked: {len(NEWS['items'])}")
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures:
            print("  " + f)
        return 1
    print("ALL PASS: news JSON is sound, every page has its SEO head, "
          "and the Hinglish toggle swaps both ways")
    return 0


if __name__ == "__main__":
    sys.exit(main())
