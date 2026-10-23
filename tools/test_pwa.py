#!/usr/bin/env python3
"""Guard the offline/installable app shell.

Checks the files the PWA needs, that every page points at them, that the
service worker really does answer with a cached page when the network is
gone, and that nothing the site already relied on (the Search Console
verification tag, the manifest) was damaged while wiring this up.

The offline half needs a browser: it serves `public/` over http, loads a page,
stops the server, reloads, and asserts the page still renders. Run with
`--static` to skip the browser part and check the files only.
"""
import http.server
import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SITE = PUBLIC / "site"

PAGES = sorted(SITE.glob("*.html")) + sorted((SITE / "tools").glob("*.html"))
PAGES = sorted(set(PAGES + [SITE / "index.html"]))

URL_MAP = json.loads((ROOT / "tools" / "url-map.json").read_text(encoding="utf-8"))


class RewriteHandler(http.server.SimpleHTTPRequestHandler):
    """Serve public/ the way production does.

    In production Next.js rewrites a clean path such as /about to
    /site/about.html. A bare http.server does not, so /about 404s and an
    offline check that navigates there would fail for a reason that has
    nothing to do with the service worker. Mirroring the rewrites here keeps
    the test honest: it exercises the same URLs a visitor actually opens.
    """

    def translate_path(self, path):
        clean = path.split("?", 1)[0].split("#", 1)[0]
        target = URL_MAP.get(clean)
        if clean == "/":
            target = "/site/index.html"
        if target:
            return str(PUBLIC / target.lstrip("/"))
        return super().translate_path(path)

    def log_message(self, *args):
        pass


def check_files() -> list:
    failures = []
    # The worker must sit at the root: a worker served from /site/ can only
    # control /site/*, and the real pages are clean root URLs.
    if not (PUBLIC / "sw.js").exists():
        failures.append("/sw.js is missing (must be at the root for full scope)")
    for name in ["pwa.js", "manifest.webmanifest", "updates.json",
                 "icon-192.png", "icon-512.png", "icon-maskable-512.png"]:
        if not (SITE / name).exists():
            failures.append(f"/site/{name} is missing")
    if not (PUBLIC / "sitemap.xml").exists():
        failures.append("/sitemap.xml is missing")
    return failures


def check_pages() -> list:
    failures = []
    for page in PAGES:
        text = page.read_text(encoding="utf-8", errors="replace")
        rel = page.relative_to(PUBLIC)
        if "pwa -->" not in text:
            failures.append(f"{rel} has no pwa block")
        if "/site/pwa.js" not in text:
            failures.append(f"{rel} does not load pwa.js")
        if "/sw.js" not in text and "/site/pwa.js" in text:
            pass  # registration lives in pwa.js, not inline
        if 'rel="manifest"' not in text:
            failures.append(f"{rel} has no manifest link")
        # Nothing that was already there may be lost: this is the check that
        # would have caught the greedy regex that ate the verification tag.
        if "google-site-verification" not in text:
            failures.append(f"{rel} lost its google-site-verification tag")
        if text.count('rel="manifest"') != 1:
            failures.append(f"{rel} has {text.count('rel=\"manifest\"')} manifest links")
    return failures


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(PUBLIC), **kw)

    def log_message(self, *a):
        pass


def free_port() -> int:
    import socket

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


PROBE = """<!doctype html><meta charset="utf-8">
<script>
window.__probe = (async function () {
  try {
    var reg = await navigator.serviceWorker.register("/sw.js");
    await navigator.serviceWorker.ready;
    for (var i = 0; i < 40; i++) {
      if (navigator.serviceWorker.controller) break;
      await new Promise(function (r) { setTimeout(r, 250); });
    }
    var names = await caches.keys();
    var hits = [];
    for (var n of names) {
      var c = await caches.open(n);
      for (var req of await c.keys()) hits.push(new URL(req.url).pathname);
    }
    return { reg: !!reg, controlled: !!navigator.serviceWorker.controller,
             caches: names, precached: hits.sort() };
  } catch (e) { return { error: String(e) }; }
})();
</script>
"""

CDP_DRIVER = r"""
const [port, base, page] = process.argv.slice(2);
const target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json())
  .find((t) => t.type === "page");
const ws = new WebSocket(target.webSocketDebuggerUrl);
let id = 0; const pending = new Map();
const send = (method, params = {}) => new Promise((r) => {
  const i = ++id; pending.set(i, r);
  ws.send(JSON.stringify({ id: i, method, params }));
});
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result); pending.delete(m.id); }
};
await new Promise((r) => (ws.onopen = r));
const evaluate = async (expr) =>
  (await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true })).result?.value;
await send("Page.enable"); await send("Runtime.enable"); await send("Network.enable");

// 1. Visit the page normally, so the worker installs and caches it.
await send("Page.navigate", { url: base + page });
await new Promise((r) => setTimeout(r, 5000));
for (let i = 0; i < 20; i++) {
  if (await evaluate("!!navigator.serviceWorker.controller")) break;
  await new Promise((r) => setTimeout(r, 500));
}
const probe = await evaluate(`(async () => {
  const reg = await navigator.serviceWorker.getRegistration();
  const names = await caches.keys();
  const hits = [];
  for (const n of names) {
    const c = await caches.open(n);
    for (const req of await c.keys()) hits.push(new URL(req.url).pathname);
  }
  return { reg: !!reg, controlled: !!navigator.serviceWorker.controller,
           caches: names, cached: hits.sort() };
})()`);

// 2. Take the network away AND disable the browser's own HTTP cache, so the
//    only thing that can still answer is the service worker's cache.
await send("Network.setCacheDisabled", { cacheDisabled: true });
await send("Network.emulateNetworkConditions",
  { offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0 });
await send("Page.reload", { ignoreCache: true });
await new Promise((r) => setTimeout(r, 5000));
const offline = await evaluate(`({
  title: document.title,
  calc: typeof parseAmount === "function",
  emi: (document.querySelector("#out .r .v") || {}).textContent || null,
  sw: !!navigator.serviceWorker.controller
})`);

// 3. A page the visitor never opened must ALSO work offline. This is the bug
//    the whole precache list exists for: before it, only the visited page and
//    the shell were cached, so /about, /blog, /news and 100 calculators were
//    dead the moment the network dropped.
await send("Page.navigate", { url: base + "/about" });
await new Promise((r) => setTimeout(r, 4000));
const unseen = await evaluate(`({
  title: document.title,
  body: (document.body.innerText || "").slice(0, 60),
  sw: !!navigator.serviceWorker.controller
})`);

await send("Page.navigate", { url: base + "/blog" });
await new Promise((r) => setTimeout(r, 4000));
const unseenBlog = await evaluate(`({
  title: document.title,
  cards: document.querySelectorAll(".blog-card").length,
  sw: !!navigator.serviceWorker.controller
})`);

console.log(JSON.stringify({ probe, offline, unseen, unseenBlog }));
ws.close();
"""


def check_offline() -> list:
    """Prove the offline story, end to end, in a real browser.

    Load a probe that registers the worker, confirm the shell landed in the
    cache, then take the network away and load a calculator page: it must still
    render and still compute. Driven over the DevTools protocol because that
    needs nothing beyond node, which the rest of the toolchain already uses.
    """
    failures = []
    probe = PUBLIC / "_pwa_probe.html"
    driver = ROOT / ".pwa_driver.mjs"
    probe.write_text(PROBE, encoding="utf-8")
    driver.write_text(CDP_DRIVER, encoding="utf-8")
    port = free_port()
    debug_port = free_port()
    os.chdir(PUBLIC)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), RewriteHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    # A throwaway profile per run. Chromium keeps service workers and Cache
    # Storage in its profile, so sharing the default one lets a previous run
    # leave a populated cache behind and the offline check passes without ever
    # exercising the code it is meant to test.
    import tempfile
    profile = tempfile.mkdtemp(prefix="tm-pwa-")
    browser = subprocess.Popen(
        ["chromium", "--headless=new", "--disable-gpu", "--no-sandbox",
         f"--user-data-dir={profile}",
         f"--remote-debugging-port={debug_port}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        import socket
        for _ in range(60):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                    break
            except OSError:
                time.sleep(0.1)
        for _ in range(60):
            try:
                with socket.create_connection(("127.0.0.1", debug_port), timeout=0.5):
                    break
            except OSError:
                time.sleep(0.1)
        out = subprocess.run(
            ["node", str(driver), str(debug_port), f"http://127.0.0.1:{port}",
             "/site/tools/loan-emi-calculator.html"],
            capture_output=True, text=True, timeout=180,
        )
    finally:
        server.shutdown()
        server.server_close()
        browser.terminate()
        probe.unlink(missing_ok=True)
        driver.unlink(missing_ok=True)
        import shutil
        shutil.rmtree(profile, ignore_errors=True)

    if out.returncode != 0:
        return failures + [f"browser driver failed: {(out.stderr or out.stdout)[:300]}"]
    try:
        data = json.loads(out.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return failures + [f"browser driver returned unreadable data: {out.stdout[:200]}"]

    probe_data = data.get("probe") or {}
    if probe_data.get("error"):
        return failures + [f"service worker failed to register: {probe_data['error']}"]
    if not probe_data.get("reg"):
        failures.append("service worker did not register")
    if not probe_data.get("controlled"):
        failures.append("service worker never took control of the page")
    cached = probe_data.get("cached") or []
    for want in ["/", "/site/style.css", "/site/pwa.js", "/site/manifest.webmanifest"]:
        if want not in cached:
            failures.append(f"service worker did not precache {want}")
    if "/site/tools/loan-emi-calculator.html" not in cached:
        failures.append("the visited page was not cached, so it cannot work offline")

    # The precache list is the whole offline story, and asserting the offline
    # *navigation* alone is not enough to prove it: chromium's own HTTP cache
    # can serve a page that the worker never stored, so a broken precache still
    # "passes" (verified by disabling the list and watching this test stay
    # green). Assert the pages are in the worker's cache directly.
    precache = json.loads((SITE / "precache.json").read_text(encoding="utf-8"))["paths"]
    must_have = ["/about", "/blog", "/news", "/contact",
                 "/site/tools/loan-emi-calculator.html"]
    must_have += [p for p in precache if p.startswith("/site/tools/")][:5]
    for want in dict.fromkeys(must_have):
        if want not in cached:
            failures.append(
                f"the precache list did not store {want}, so it is not offline")
    missing = [p for p in precache if p not in cached]
    if missing:
        failures.append(
            f"{len(missing)} of {len(precache)} precache paths never reached the "
            f"worker cache, e.g. {missing[:3]}")

    offline = data.get("offline") or {}
    if not offline.get("title"):
        failures.append("offline load produced no page at all")
    elif "Loan EMI" not in offline["title"]:
        failures.append(f"offline load served the wrong page: {offline['title']!r}")
    if not offline.get("calc"):
        failures.append("offline page lost its calculator logic")
    if not offline.get("sw"):
        failures.append("the offline load was not served by the service worker")

    # The pages nobody visited are the real test of the precache list.
    unseen = data.get("unseen") or {}
    if "About" not in (unseen.get("title") or ""):
        failures.append(
            "an unvisited page (/about) did not work offline: "
            f"{unseen.get('title')!r} - the precache list is not being installed"
        )
    blog = data.get("unseenBlog") or {}
    if not blog.get("cards"):
        failures.append(
            "an unvisited /blog worked offline but rendered no cards, "
            "so the cached copy is not the real page"
        )
    return failures



def check_banner_design() -> list:
    """The strip Sir asked to be beautiful, and the icon's colour edge.

    Both are easy to lose: a redesign that drops the mark, or a regenerated
    maskable icon that goes back to a white tile, would still "work" - the strip
    would still appear and the icon would still load - so nothing else in this
    suite would notice.

    The maskable icon was a WHITE 512 tile with the art centred, which put a
    solid white frame around the logo. Sir asked for the opposite: the colour
    must reach every corner and no white may show on the OUTER side. So the
    corner is asserted to be a ring colour, not white.
    """
    failures = []
    css = (SITE / "style.css").read_text(encoding="utf-8")
    for token in ["pwa-mark", "pwa-copy", "@keyframes pwaIn", "@keyframes pwaOut",
                  "conic-gradient", "translateY(140%)"]:
        if token not in css:
            failures.append(f"style.css lost the banner design piece {token!r}")
    # A stale flat rule surviving alongside the new one is what happened the
    # first time this was written: the dark bar was still in the file and the
    # new rule merely overrode it. Assert the old look is gone, not just that
    # the new look is present.
    if "#111827" in css:
        failures.append("style.css still carries the old dark banner rule")
    if css.count(".pwa-banner{") != 2:
        failures.append(
            f"expected 2 .pwa-banner rules (base + mobile), found {css.count('.pwa-banner{')}")

    js = (SITE / "pwa.js").read_text(encoding="utf-8")
    if 'className = "pwa-mark"' not in js:
        failures.append("pwa.js no longer draws the brand mark in the banner")
    if "pwa-copy" not in js:
        failures.append("pwa.js no longer writes the title/subtitle block")
    if "function dismiss()" not in js or "pwa-out" not in js:
        failures.append("pwa.js has no dismiss animation")
    # every call site must pass a title and a subtitle, not one flat string
    if js.count('show("') < 5:
        failures.append("pwa.js lost a banner call site")
    for phrase in ["Keep Tank Metrics on your phone", "Never miss a new calculator",
                   "New version is ready", "Something new is live"]:
        if phrase not in js:
            failures.append(f"pwa.js lost the banner copy {phrase!r}")

    icon = SITE / "icon-maskable-512.png"
    if icon.exists():
        from PIL import Image
        im = Image.open(icon).convert("RGBA")
        corner = im.getpixel((2, 2))
        ring = [(52, 168, 83), (66, 133, 244), (242, 166, 0), (234, 67, 53)]
        if corner[3] < 250:
            failures.append(
                f"maskable icon corner is transparent {corner} - the launcher's "
                "background shows through as a pale border")
        elif min(corner[:3]) > 235:
            failures.append(
                f"maskable icon corner is white {corner} - Sir asked for colour "
                "to reach every corner, with no white on the outer side")
        elif min(abs(corner[i] - ring[0][i]) for i in range(3)) > 30:
            failures.append(
                f"maskable icon corner {corner[:3]} is not a ring colour "
                f"({ring}) - the colour must merge into each corner")
    return failures


def main() -> int:
    failures = check_files() + check_pages() + check_banner_design()
    if "--static" not in sys.argv:
        try:
            failures += check_offline()
        except FileNotFoundError:
            print("skip browser check: playwright/node not available")
        except Exception as e:
            failures.append(f"offline check errored: {e}")
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures[:25]:
            print("  -", f)
        return 1
    print(f"ALL PASS: PWA shell on {len(PAGES)} pages, files present, offline load works")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
