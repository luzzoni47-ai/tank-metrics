#!/usr/bin/env python3
"""Guard the translate button on the calculator pages.

Sir asked for the same language switch the blog posts have to appear on the
calculator pages too, under the calculator and above the guide. The 101 tool
pages had no Hinglish block at all, so this checks the whole path: the button
exists and is visible, the English block shows first, one tap swaps in the
Hinglish block, the label and <html lang> follow, and the Hinglish text is
roman script only (the site ships Hinglish, never Devanagari).

Run with `--static` to check the markup only.
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
TOOLS = SITE / "tools"

# One hand-written guide (emi) and two that fall back to the category template,
# so both code paths are exercised.
PAGES = [
    "/site/tools/loan-emi-calculator.html",
    "/site/tools/percentage-calculator.html",
    "/site/tools/age-calculator.html",
]

PROBE = r"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>html,body{margin:0}iframe{width:390px;height:900px;border:0}</style></head>
<body><iframe id="f"></iframe><pre id="out">pending</pre><script>
var pages = %s, i = 0, results = [];
function next() {
  if (i >= pages.length) { document.getElementById('out').textContent = JSON.stringify(results); return; }
  var f = document.getElementById('f');
  f.onload = function () {
    var d = f.contentDocument, w = f.contentWindow;
    setTimeout(function () {
      var rec = {page: pages[i]};
      var btn = d.getElementById('langToggle');
      var en = d.querySelector('.post-lang[data-lang="en"]');
      var hing = d.querySelector('.post-lang[data-lang="hinglish"]');
      rec.hasBtn = !!btn; rec.hasEn = !!en; rec.hasHing = !!hing;
      if (btn && en && hing) {
        rec.btnVisible = w.getComputedStyle(btn).display !== 'none'
          && btn.getBoundingClientRect().height > 0;
        rec.labelBefore = btn.querySelector('.lang-toggle-label').textContent;
        rec.badgeBefore = btn.querySelector('.lang-badge').textContent;
        rec.enShownFirst = !en.hidden && w.getComputedStyle(en).display !== 'none';
        rec.hingHiddenFirst = hing.hidden;
        rec.langBefore = d.documentElement.lang;
        var card = d.querySelector('.card');
        var h2s = d.querySelectorAll('.post-lang[data-lang="en"] h2');
        rec.btnBelowCard = card ? btn.getBoundingClientRect().top >= card.getBoundingClientRect().bottom - 4 : null;
        rec.btnAboveGuide = h2s.length ? btn.getBoundingClientRect().bottom <= h2s[0].getBoundingClientRect().top + 4 : null;
        btn.click();
        rec.enHiddenAfter = en.hidden;
        rec.hingShownAfter = !hing.hidden && w.getComputedStyle(hing).display !== 'none';
        rec.hingHeight = Math.round(hing.getBoundingClientRect().height);
        rec.labelAfter = btn.querySelector('.lang-toggle-label').textContent;
        rec.badgeAfter = btn.querySelector('.lang-badge').textContent;
        rec.langAfter = d.documentElement.lang;
        rec.pressed = btn.getAttribute('aria-pressed');
        rec.hingText = hing.textContent.trim();
        rec.hingChars = rec.hingText.length;
        rec.devanagari = /[\u0900-\u097F]/.test(rec.hingText);
        rec.hingHeadings = [].map.call(hing.querySelectorAll('h2'), function (h) { return h.textContent; });
        btn.click();
        rec.backToEnglish = !en.hidden && hing.hidden && d.documentElement.lang === 'en';
      }
      results.push(rec);
      i++;
      next();
    }, 800);
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
    failures = []
    for page in sorted(TOOLS.glob("*.html")):
        text = page.read_text(encoding="utf-8", errors="replace")
        rel = page.relative_to(PUBLIC)
        if 'id="langToggle"' not in text:
            failures.append(f"{rel} has no translate button")
            continue
        # Match the block itself, not the string: the toggle script also
        # contains data-lang="hinglish" in its selector, so a plain substring
        # test passes even when the block is missing (verified by deleting the
        # block from one page and watching the old check stay green).
        if not re.search(r'<div class="post-lang" data-lang="hinglish"', text):
            failures.append(f"{rel} has no Hinglish block, so the button does nothing")
        if not re.search(r'<div class="post-lang" data-lang="en"', text):
            failures.append(f"{rel} has no English guide block")
        if re.search(r"[\u0900-\u097F]", text):
            failures.append(f"{rel} contains Devanagari; the site ships Hinglish only")
    return failures


def check_toggle() -> list:
    failures = []
    probe = PUBLIC / "_lang_probe.html"
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
             "--window-size=390,900", "--virtual-time-budget=30000",
             "--dump-dom", f"http://127.0.0.1:{port}/_lang_probe.html"],
            capture_output=True, text=True, timeout=200,
        ).stdout
    finally:
        server.terminate()
        probe.unlink(missing_ok=True)

    m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
    if not m:
        return ["lang probe produced no output"]
    try:
        data = json.loads(html_mod.unescape(m.group(1)))
    except json.JSONDecodeError:
        return [f"lang probe returned unreadable data: {m.group(1)[:200]}"]

    for rec in data:
        page = rec["page"]
        if not rec.get("hasBtn"):
            failures.append(f"{page} has no translate button")
            continue
        if not rec.get("hasEn") or not rec.get("hasHing"):
            failures.append(f"{page} is missing one of the language blocks")
            continue
        if not rec.get("btnVisible"):
            failures.append(f"{page} translate button is not visible")
        if rec.get("labelBefore") != "Hinglish":
            failures.append(f"{page} label starts as {rec.get('labelBefore')!r}")
        if not rec.get("enShownFirst"):
            failures.append(f"{page} does not start in English")
        if not rec.get("hingHiddenFirst"):
            failures.append(f"{page} shows the Hinglish block before any tap")
        if rec.get("langBefore") != "en":
            failures.append(f"{page} <html lang> starts as {rec.get('langBefore')!r}")
        if rec.get("btnBelowCard") is False:
            failures.append(f"{page} translate button is not below the calculator")
        if rec.get("btnAboveGuide") is False:
            failures.append(f"{page} translate button is not above the guide")
        if not rec.get("enHiddenAfter"):
            failures.append(f"{page} English block stayed visible after the tap")
        if not rec.get("hingShownAfter"):
            failures.append(f"{page} Hinglish block did not appear after the tap")
        if (rec.get("hingHeight") or 0) < 200:
            failures.append(f"{page} Hinglish block is only {rec.get('hingHeight')}px tall")
        if rec.get("labelAfter") != "English":
            failures.append(f"{page} label after the tap is {rec.get('labelAfter')!r}")
        if rec.get("langAfter") != "hi-Latn":
            failures.append(f"{page} <html lang> after the tap is {rec.get('langAfter')!r}")
        if rec.get("pressed") != "true":
            failures.append(f"{page} aria-pressed is {rec.get('pressed')!r} when Hinglish")
        if (rec.get("hingChars") or 0) < 600:
            failures.append(
                f"{page} Hinglish block is only {rec.get('hingChars')} chars; "
                "it should carry the worked example and the guide")
        if rec.get("devanagari"):
            failures.append(f"{page} Hinglish block contains Devanagari")
        if not rec.get("backToEnglish"):
            failures.append(f"{page} a second tap did not return to English")
    return failures


def main() -> int:
    failures = check_markup()
    if "--static" not in sys.argv:
        try:
            failures += check_toggle()
        except FileNotFoundError:
            print("skip browser check: chromium not available")
        except Exception as e:
            failures.append(f"toggle check errored: {e}")
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures[:25]:
            print("  -", f)
        return 1
    print("ALL PASS: every calculator page has a working Hinglish translate button")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
