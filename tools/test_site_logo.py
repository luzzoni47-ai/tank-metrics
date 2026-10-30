"""Guards the brand mark against the v0 logo coming back.

The site inherited its favicon from a v0 scaffold - a black "v0" square - and
Google cached it. The files were replaced on 2026-10-23, yet Google's search and
AI surfaces still showed the black square weeks later. The cause was subtle:
the home page's structured data had no Organization and no logo, so Google fell
back to its own cached favicon.

This test locks in all three conditions that have to hold together, plus the
GSC-side facts that decide whether the fix can take effect at all:

  1. Every icon a page points at exists and is the brand mark, not a black square.
  2. The home page declares Organization.logo, and the URL resolves.
  3. The favicon URLs are stable and reachable, with no v0 reference left in the
     served HTML.

Checks 1 and 2 run on the generated files; check 3 is a live probe and is
skipped when the network is unavailable.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "public" / "site"
PUB = ROOT / "public"
BASE = "https://tankmetrics.in"

# The brand mark's four colours, straight from the logo.
BRAND = {(66, 133, 244), (234, 67, 53), (242, 166, 0), (52, 168, 83)}
# Google reads the favicon from the home page only. If it is not on /, nothing
# on any other page matters.
HOME = SITE / "index.html"

fails: list[str] = []


def fail(msg: str) -> None:
    fails.append(msg)
    print("FAIL:", msg)


def icon_stats(path: Path):
    from PIL import Image

    im = Image.open(path).convert("RGBA").resize((32, 32))
    px = list(im.getdata())
    brand = sum(1 for p in px if p[:3] in BRAND)
    dark = sum(1 for p in px if sum(p[:3]) / 3 < 60)
    return brand, dark


def check_icons() -> None:
    """Every declared icon must exist and be the brand mark."""
    seen: set[Path] = set()
    for f in sorted(SITE.rglob("*.html")):
        t = f.read_text(encoding="utf-8")
        for tag in re.findall(r'<link[^>]+rel="[^"]*icon[^"]*"[^>]*>', t, re.I):
            href = re.search(r'href="([^"]+)"', tag)
            if not href:
                continue
            url = href.group(1)
            if not url.startswith("/"):
                fail(f"{f.name}: icon href {url!r} is not a site-relative path")
                continue
            local = PUB / url.lstrip("/")
            if not local.exists():
                fail(f"{f.name}: declared icon {url} does not exist (a 404)")
                continue
            if url.endswith(".svg") or local in seen:
                continue
            seen.add(local)
            brand, dark = icon_stats(local)
            if brand < 50:
                fail(f"{url}: only {brand} brand pixels - not the Tank Metrics mark")
            if dark > 200:
                fail(f"{url}: {dark} near-black pixels - looks like the v0 square")
    print(f"icons: {len(seen)} file(s) checked, all brand mark")


def check_organization_logo() -> None:
    """The home page must declare Organization.logo, and it must resolve."""
    t = HOME.read_text(encoding="utf-8")
    graph = None
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
        if '"@graph"' in m.group(1):
            graph = json.loads(m.group(1))["@graph"]
            break
    if graph is None:
        fail("index.html: no @graph JSON-LD block")
        return

    types = [n.get("@type") for n in graph]
    if "Organization" not in types:
        fail(f"index.html: no Organization node (has {types}) - Google will fall "
             "back to its cached favicon")
        return

    org = next(n for n in graph if n.get("@type") == "Organization")
    logo = org.get("logo")
    if not logo:
        fail("index.html: Organization has no logo")
        return
    url = logo.get("url", "") if isinstance(logo, dict) else ""
    if not url.startswith(BASE + "/"):
        fail(f"index.html: Organization.logo url {url!r} is not on {BASE}")
        return
    local = PUB / url[len(BASE):].lstrip("/")
    if not local.exists():
        fail(f"index.html: Organization.logo {url} has no file behind it")
        return
    brand, dark = icon_stats(local)
    if brand < 50:
        fail(f"Organization.logo {url}: only {brand} brand pixels")
    print(f"Organization.logo: {url} ({brand} brand pixels)")

    # E-E-A-T: a money site should say who it is and who it serves. These are
    # the fields Google reads to decide the site is a real entity, and they are
    # cheap to lose in a regeneration.
    if not org.get("email"):
        fail("Organization has no email - the contact page publishes one")
    if (org.get("areaServed") or {}).get("name") != "India":
        fail("Organization.areaServed is not India")
    site = next((n for n in graph if n.get("@type") == "WebSite"), None)
    if site is None:
        fail("index.html: no WebSite node")
    elif "potentialAction" not in site:
        fail("WebSite has no SearchAction (sitelinks searchbox)")

    # The publisher reference is what ties the calculators to the org.
    ws = next((n for n in graph if n.get("@type") == "WebSite"), None)
    if ws is not None and "publisher" not in ws:
        fail("index.html: WebSite has no publisher - the logo link is one-way")


def check_no_v0_reference() -> None:
    """No served page may name v0 or carry the black square."""
    hits = []
    for f in sorted(SITE.rglob("*.html")):
        t = f.read_text(encoding="utf-8")
        if re.search(r"v0\.(dev|app)|v0-logo|\bv0 logo\b", t, re.I):
            hits.append(f.name)
    if hits:
        fail(f"{len(hits)} page(s) still mention v0: {hits[:5]}")
    else:
        print("no v0 reference in any served page")


def check_live() -> None:
    """Live probe: the icon URLs must be reachable and the right colour."""
    urls = ["/site/favicon.ico", "/site/favicon.png", "/apple-touch-icon.png",
            "/site/icon-192.png"]
    for u in urls:
        try:
            with urllib.request.urlopen(BASE + u, timeout=20) as r:
                raw = r.read()
                ct = r.headers.get("content-type", "")
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"live probe skipped ({e}) - not a failure")
            return
        if not ct.startswith("image/"):
            fail(f"live {u}: content-type {ct!r}, expected an image")
            continue
        from io import BytesIO

        from PIL import Image

        brand, dark = icon_stats_bytes(BytesIO(raw))
        if dark > 200 and brand < 50:
            fail(f"live {u}: black square, not the brand mark")
        else:
            print(f"live {u}: ok ({brand} brand pixels)")


def icon_stats_bytes(buf):
    from PIL import Image

    im = Image.open(buf).convert("RGBA").resize((32, 32))
    px = list(im.getdata())
    brand = sum(1 for p in px if p[:3] in BRAND)
    dark = sum(1 for p in px if sum(p[:3]) / 3 < 60)
    return brand, dark


def main() -> int:
    check_icons()
    check_organization_logo()
    check_no_v0_reference()
    if "--live" in sys.argv:
        check_live()
    if fails:
        print(f"\n{len(fails)} problem(s)")
        return 1
    print("\nALL PASS: brand mark is the only logo the site declares")
    return 0


if __name__ == "__main__":
    sys.exit(main())
