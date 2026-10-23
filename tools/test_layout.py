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


def check_image_hosts() -> list:
    """Every <img> must be same-origin, and the file it names must exist.

    The CSP in next.config.mjs is `img-src 'self' data:`, so an image served
    from anywhere else is silently blocked: the markup looks right, the page
    loads, and the picture simply never appears. That is exactly how the founder
    photo went missing from /about - it pointed at Vercel Blob. A same-origin
    path that names no file fails the same way, so both are checked.
    """
    failures = []
    for page in sorted(PUBLIC.glob("site/**/*.html")):
        text = page.read_text(encoding="utf-8", errors="replace")
        for src in re.findall(r'<img[^>]*\ssrc="([^"]*)"', text):
            if src.startswith("data:"):
                continue
            if not src.startswith("/"):
                failures.append(
                    f"{page.relative_to(PUBLIC)} loads an off-site image ({src}); "
                    "CSP img-src is 'self' data:, so it will not render"
                )
                continue
            if not (PUBLIC / src.lstrip("/")).is_file():
                failures.append(
                    f"{page.relative_to(PUBLIC)} points at {src}, which is not in public/"
                )
    return failures


def check_top_strip() -> list:
    """The header stripe must use the logo's four colours everywhere it appears.

    The same stripe is drawn in three separate rules - `.tricolor` for desktop,
    `.topbar:after` for mobile, and a `.topbar::after` in the desktop media
    query - so changing one and missing another silently leaves an old stripe on
    the screen. That happened: the mobile bar was updated and desktop still
    showed the old saffron/white/green. Pin all three to the logo variables.
    """
    css = (PUBLIC / "site" / "style.css").read_text(encoding="utf-8")
    logo = ["var(--blue)", "var(--red)", "var(--yellow)", "var(--green)"]
    failures = []
    # Four rules mention the stripe; the fourth only repositions it on mobile
    # (`top:0;bottom:auto`) and paints nothing, so only the gradients matter.
    gradients = [
        r for r in re.findall(r"\.tricolor\{[^}]*\}|\.topbar::?after\{[^}]*\}", css)
        if "linear-gradient" in r
    ]
    if len(gradients) != 3:
        failures.append(f"expected 3 painted header stripes, found {len(gradients)}")
    for rule in gradients:
        name = rule.split("{")[0]
        missing = [v for v in logo if v not in rule]
        if missing:
            failures.append(
                f"{name} is not using the logo colours (missing {', '.join(missing)})"
            )
    return failures


def report(failures: list, note: str = "") -> None:
    if note:
        failures.insert(0, note)
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures:
            print("  " + f)
    else:
        print("ALL PASS")


def check_close_button() -> list:
    """The mobile calculator close `×` must sit just under the tip line.

    It used to be `position:absolute; bottom:22px` inside a fixed full-screen
    card, so on a card whose content is short it floated ~426px below the Tip
    line - marooned at the bottom of the screen, nowhere near the calculator it
    closes. It is in normal flow now. Measure the real gap rather than trusting
    the CSS, because the card is only full-screen while focused.
    """
    probe = PUBLIC / "_close_probe.html"
    probe.write_text(
        """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>html,body{margin:0}iframe{width:390px;height:844px;border:0}</style></head>
<body><iframe id="f" src="/site/index.html"></iframe><pre id="out">pending</pre><script>
document.getElementById('f').onload = function () {
  var f = this, d = f.contentDocument;
  setTimeout(function () {
    var card = d.querySelector('.card');
    if (!card) { document.getElementById('out').textContent = JSON.stringify({error: 'no card'}); return; }
    card.click();
    setTimeout(function () {
      var close = d.querySelector('.calculator-focus-close');
      var tip = card.querySelector('.benchmark');
      if (!close) { document.getElementById('out').textContent = JSON.stringify({error: 'no close button'}); return; }
      if (!tip) { document.getElementById('out').textContent = JSON.stringify({error: 'no tip line'}); return; }
      var c = close.getBoundingClientRect(), t = tip.getBoundingClientRect();
      document.getElementById('out').textContent = JSON.stringify({
        gap: Math.round(c.top - t.bottom),
        closeText: close.textContent,
        position: f.contentWindow.getComputedStyle(close).position,
      });
    }, 700);
  }, 1300);
};
</script></body></html>
""",
        encoding="utf-8",
    )
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
             f"--window-size={WIDTH},{HEIGHT}", "--virtual-time-budget=15000",
             "--dump-dom", f"http://127.0.0.1:{port}/_close_probe.html"],
            capture_output=True, text=True, timeout=180,
        ).stdout
    finally:
        server.terminate()
        probe.unlink(missing_ok=True)

    m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
    if not m:
        return ["close-button probe produced no output"]
    import html as html_mod
    try:
        data = json.loads(html_mod.unescape(m.group(1)))
    except json.JSONDecodeError:
        return ["close-button probe returned unreadable data"]
    if data.get("error"):
        return [f"close button: {data['error']}"]
    if data["closeText"] != "\u00d7":
        return [f"close button reads {data['closeText']!r}, expected '×'"]
    if data["position"] == "absolute":
        return ["close button is absolutely positioned again; it will float away from the tip line"]
    if not 0 <= data["gap"] <= 60:
        return [f"close button sits {data['gap']}px below the tip line, expected 0-60px"]
    return []


def check_favicon() -> list:
    """Google will only show a favicon whose side is a multiple of 48px.

    The mark was rendered at 256x256 - square, live, correct colours, and
    silently ignored by Google's favicon crawler, so search results kept the
    old cached v0 icon. The declared `sizes` must also match the real file: a
    <link> that claims 64x64 over a 256x256 file is the kind of disagreement
    that gets the whole icon distrusted.
    """
    import struct

    failures = []
    for rel in ("favicon.png", "site/favicon.png"):
        p = PUBLIC / rel
        if not p.is_file():
            failures.append(f"{rel} is missing")
            continue
        w, h = struct.unpack(">II", p.read_bytes()[16:24])
        if w != h:
            failures.append(f"{rel} is {w}x{h}, not square")
        if w % 48:
            failures.append(
                f"{rel} is {w}x{w}; Google needs a side that is a multiple of 48 "
                "(48, 96, 144, 192) or it drops the icon from search results"
            )
    # Every page must declare the size that the file actually is, and point at
    # the manifest so a phone home-screen shortcut gets the brand mark too.
    for page in sorted(PUBLIC.glob("site/**/*.html")):
        text = page.read_text(encoding="utf-8", errors="replace")
        for tag in re.findall(r'<link[^>]+rel="[^"]*icon[^"]*"[^>]*>', text):
            m = re.search(r'sizes="(\d+)x(\d+)"', tag)
            if m and "favicon.png" in tag and int(m.group(1)) != 192:
                failures.append(
                    f"{page.relative_to(PUBLIC)} declares favicon.png as "
                    f"{m.group(1)}x{m.group(2)} but the file is 192x192"
                )
        if "manifest.webmanifest" not in text:
            failures.append(
                f"{page.relative_to(PUBLIC)} has no manifest link; a phone "
                "home-screen shortcut would fall back to a generic icon"
            )
    return failures


def check_icon_shape() -> list:
    """The app icon must be the same rounded square as the banner mark.

    The icon used to be a circle while the install banner drew a squircle, so
    the brand looked like two different logos. Sir asked for the app icon to
    match the banner.

    Telling them apart needs a measurement, not a pixel probe. A circle and a
    squircle are both opaque at the centre of the top edge and both transparent
    in the corner, so the first version of this check - which looked at exactly
    those two pixels - passed on the circle it was meant to catch. The real
    difference is how much of the TOP ROW is covered: a disc only touches it
    over ~11% of the width, while a rounded square spans ~47%. Require 30%.
    """
    failures = []
    from PIL import Image
    for rel in ("site/icon-192.png", "site/icon-512.png", "site/favicon.png"):
        p = PUBLIC / rel
        if not p.is_file():
            failures.append(f"{rel} is missing")
            continue
        im = Image.open(p).convert("RGBA")
        w, h = im.size
        px = im.load()
        top = sum(1 for x in range(w) if px[x, 0][3] > 128)
        pct = top / w
        if px[1, 1][3] > 8:
            failures.append(f"{rel} has an opaque top-left corner - not a rounded square")
        if pct < 0.30:
            failures.append(
                f"{rel} covers only {pct:.0%} of its top row, which is the "
                "signature of a circle. The banner mark is a rounded square "
                "(~47%); Sir asked the app icon to match it"
            )
    return failures


def check_manifest() -> list:
    """The web app manifest must exist and name icons that really are there.

    Without it, "Add to Home Screen" shows a grey placeholder instead of the
    Tank Metrics mark - the one place a logo is most visible and most obviously
    wrong when it is missing.
    """
    failures = []
    manifest = PUBLIC / "site" / "manifest.webmanifest"
    if not manifest.is_file():
        return ["site/manifest.webmanifest is missing"]
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"site/manifest.webmanifest is not valid JSON: {exc}"]
    icons = data.get("icons") or []
    if not any(i.get("sizes") == "512x512" for i in icons):
        failures.append("manifest has no 512x512 icon (Chrome wants one)")
    if not any(i.get("purpose") == "maskable" for i in icons):
        failures.append("manifest has no maskable icon (Android crops it badly)")
    for i in icons:
        src = i.get("src", "")
        if not src.startswith("/"):
            failures.append(f"manifest icon {src!r} is not a same-origin path")
        elif not (PUBLIC / src.lstrip("/")).is_file():
            failures.append(f"manifest names {src}, which is not in public/")
    return failures



def check_focus_scroll() -> list:
    """Focusing or typing in a calculator must not move the document.

    On mobile a tapped card is lifted into a `position:fixed` full-screen
    overlay. `focusCard` used to call `scrollIntoView({block:"center"})` on that
    card, and this runs on every focus and every keystroke. Scrolling a fixed
    element into view scrolls the *document*, so the first character typed threw
    the page to the top and the card was left floating over the wrong scroll
    offset. The overlay is already full-screen, so there is nothing to scroll to.

    The scroll offset itself cannot be read through the `--dump-dom` harness the
    other checks use (headless reports scrollY as 0), so this asserts the call is
    gone and the overlay tracks the keyboard with dvh instead of 100vh.
    """
    failures = []
    html = (PUBLIC / "site" / "index.html").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"function focusCard\(.*?\n", html)
    if not m:
        return ["index.html has no focusCard function"]
    body = m.group(0)
    if "scrollIntoView" in body:
        failures.append(
            "focusCard calls scrollIntoView; on a position:fixed card that "
            "scrolls the document, so typing a number throws the page to the top"
        )
    css = (PUBLIC / "site" / "style.css").read_text(encoding="utf-8")
    rule = re.search(r"\.card\.calculator-focused\{[^}]*\}", css)
    if not rule:
        failures.append("style.css has no .card.calculator-focused rule")
    elif "100dvh" not in rule.group(0):
        failures.append(
            ".card.calculator-focused sizes itself with 100vh; when the on-screen "
            "keyboard opens the browser scrolls the page. Use 100dvh."
        )
    return failures



# Sir asked for the blank bands inside the /about content block to go. They came
# from four margins stacking (see the comment in style.css), so a later edit that
# only touches one of them silently brings the hole back. Measure the real
# rendered gap at desktop width, where the holes were visible.
ABOUT_PROBE = """<!doctype html><html><body><pre id="out">pending</pre><script>
const f = document.createElement('iframe');
f.style.cssText = 'width:1200px;height:3200px;border:0';
f.onload = () => setTimeout(() => {
  const d = f.contentDocument, w = f.contentWindow;
  const hero = d.querySelector('.page-hero');
  const photo = d.querySelector('.about-photo');
  const pw = d.querySelector('.page-wrap');
  const next = photo ? photo.nextElementSibling : null;
  const last = pw ? pw.lastElementChild : null;
  const top = (el) => el.getBoundingClientRect().top;
  const bottom = (el) => el.getBoundingClientRect().bottom;
  document.getElementById('out').textContent = JSON.stringify({
    gapHeroToPhoto: Math.round(top(photo) - bottom(hero)),
    gapPhotoToNext: next ? Math.round(top(next) - bottom(photo)) : null,
    gapLastToEnd: last ? Math.round(bottom(pw) - bottom(last)) : null,
    gapHeroToBlock: Math.round(top(pw) - bottom(hero)),
  });
}, 900);
f.src = '/site/about.html?cb=' + Math.random();
document.body.appendChild(f);
</script></body></html>
"""

# The measured gaps on the fixed page. A little slack, so a font or a
# one-pixel rounding change does not fail the build, but the old 168px band
# could never slip back in.
ABOUT_MAX = {
    "gapHeroToPhoto": 40,
    "gapPhotoToNext": 20,
    "gapLastToEnd": 40,
    "gapHeroToBlock": 26,
}


def check_about_gaps() -> list:
    """The /about block must not open a hole above or below the founder photo."""
    failures = []
    probe = PUBLIC / "_about_probe.html"
    probe.write_text(ABOUT_PROBE, encoding="utf-8")
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
             "--window-size=1300,3300", "--virtual-time-budget=12000",
             "--dump-dom", f"http://127.0.0.1:{port}/_about_probe.html"],
            capture_output=True, text=True, timeout=180,
        ).stdout
    finally:
        server.terminate()
        probe.unlink(missing_ok=True)

    m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
    if not m:
        return ["about gap probe produced no output"]
    import html as html_mod
    data = json.loads(html_mod.unescape(m.group(1)))
    for key, limit in ABOUT_MAX.items():
        got = data.get(key)
        if got is None:
            failures.append(f"/about {key} could not be measured")
        elif got > limit:
            failures.append(
                f"/about {key} is {got}px, expected <= {limit}px - the blank "
                "band Sir asked to remove is back"
            )
    return failures


def main() -> int:
    failures = (
        check_image_hosts()
        + check_top_strip()
        + check_close_button()
        + check_favicon()
        + check_icon_shape()
        + check_manifest()
        + check_focus_scroll()
        + check_about_gaps()
    )

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
        report(failures, "probe produced no output")
        return 1
    import html as html_mod
    data = json.loads(html_mod.unescape(m.group(1)))

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
    report(failures)
    if failures:
        return 1
    print(f"ALL PASS: every page keeps a {GUTTER}px mobile gutter and a red footer heart")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
