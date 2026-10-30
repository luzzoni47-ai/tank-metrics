#!/usr/bin/env python3
"""Make the Tank Metrics brand mark the only logo Google can find.

Why this exists
---------------
The site inherited its icons from a v0 scaffold. That scaffold's icon was a
black "v0" square, and Google cached it. The site files were replaced with the
brand mark on 2026-10-23, but Google's favicon cache still served the black v0
square weeks later - the site looked correct and search did not.

Three things had to be true for Google to pick the brand mark up, and only two
of them were:

1. The icon files are the brand mark.                    (already true)
2. Every page points its <link rel="icon"> at them.      (already true)
3. The home page declares the logo in structured data.   (was missing)

Point 3 matters because the home page's JSON-LD had WebSite, SoftwareApplication
and FAQPage but no Organization and no logo. Google reads the site logo for
search and AI surfaces from an Organization.logo, and falls back to its own
cached favicon when there is none - which is how the v0 square kept showing.

What it does
------------
- Adds an Organization node with a logo ImageObject to the home page graph, and
  links the existing WebSite and SoftwareApplication nodes to it.
- Writes /apple-touch-icon.png at the site root. Google and iOS both probe that
  exact path, and it was a 404 while only /site/apple-touch-icon existed.
- Fails loudly if any icon a page points at is not the brand mark, so a v0 icon
  cannot come back unnoticed.

Idempotent: the Organization node is replaced, never duplicated.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "public" / "site"
PUB = ROOT / "public"
BASE = "https://tankmetrics.in"

# The four Google colours the brand mark is built from. An icon made of these is
# the brand mark; an icon that is nearly all black is the v0 square.
BRAND = {(66, 133, 244), (234, 67, 53), (242, 166, 0), (52, 168, 83)}
LOGO_PNG = SITE / "icon-512.png"

ORG_ID = f"{BASE}/#organization"
GRAPH_RE = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>', re.S)


def organization() -> dict:
    """The Organization node, with the logo Google needs to drop the v0 cache."""
    return {
        "@type": "Organization",
        "@id": ORG_ID,
        "name": "Tank Metrics",
        "url": BASE + "/",
        "description": "Free business and money calculators for India.",
        "logo": {
            "@type": "ImageObject",
            "url": f"{BASE}/site/icon-512.png",
            "width": 512,
            "height": 512,
        },
        "image": {"@id": ORG_ID + "/logo"},
    }


def patch_home_graph() -> None:
    page = SITE / "index.html"
    t = page.read_text(encoding="utf-8")
    m = None
    for cand in GRAPH_RE.finditer(t):
        if '"@graph"' in cand.group(1):
            m = cand
            break
    if not m:
        raise SystemExit("index.html: no @graph JSON-LD block found")

    data = json.loads(m.group(1))
    graph = data["@graph"]
    graph = [n for n in graph if n.get("@type") != "Organization"]
    # Organization first: it is the publisher for everything after it.
    graph.insert(0, organization())

    for node in graph:
        if node.get("@type") in ("WebSite", "SoftwareApplication"):
            node.setdefault("publisher", {"@id": ORG_ID})

    data["@graph"] = graph
    block = ('<script type="application/ld+json">'
             + json.dumps(data, ensure_ascii=False) + "</script>")
    page.write_text(t[:m.start()] + block + t[m.end():], encoding="utf-8")
    print("home graph: Organization.logo added")


def root_apple_touch_icon() -> None:
    """Both Google and iOS probe /apple-touch-icon.png; it used to 404."""
    dest = PUB / "apple-touch-icon.png"
    shutil.copyfile(SITE / "favicon.png", dest)
    print(f"wrote {dest.relative_to(ROOT)} ({dest.stat().st_size} bytes)")


def icon_is_brand_mark(path: Path) -> tuple[bool, str]:
    im = Image.open(path).convert("RGBA").resize((32, 32))
    px = list(im.getdata())
    brand = sum(1 for p in px if p[:3] in BRAND)
    dark = sum(1 for p in px if sum(p[:3]) / 3 < 60)
    if brand < 50:
        return False, f"{path.name}: only {brand} brand pixels, looks like another logo"
    if dark > 200:
        return False, f"{path.name}: {dark} near-black pixels, looks like the v0 square"
    return True, f"{path.name}: {brand} brand pixels"


def check_icons() -> None:
    """Every icon a page points at must be the brand mark.

    This is the guard against the exact regression that caused the problem: the
    files silently reverting to a v0 icon while every page still looks fine.
    """
    checked = set()
    problems = []
    for f in sorted(SITE.rglob("*.html")):
        t = f.read_text(encoding="utf-8")
        for tag in re.findall(r'<link[^>]+rel="[^"]*icon[^"]*"[^>]*>', t, re.I):
            href = re.search(r'href="([^"]+)"', tag)
            if not href:
                continue
            url = href.group(1)
            local = PUB / url.lstrip("/") if url.startswith("/") else None
            if local is None or url.endswith(".svg"):
                continue
            if not local.exists():
                problems.append(f"{f.name}: {url} is a 404")
                continue
            if local in checked:
                continue
            checked.add(local)
            ok, msg = icon_is_brand_mark(local)
            print("  " + ("ok   " if ok else "FAIL ") + msg)
            if not ok:
                problems.append(f"{f.name}: {msg}")

    if problems:
        for p in sorted(set(problems)):
            print("PROBLEM:", p)
        raise SystemExit(f"{len(problems)} icon problem(s) - Google would show the old logo")
    print(f"icons ok: {len(checked)} file(s), all brand mark")


def main() -> None:
    # Guard first: if an icon is not the brand mark, fail before copying it to
    # /apple-touch-icon.png, or the bad file is propagated as well as reported.
    check_icons()
    patch_home_graph()
    root_apple_touch_icon()


if __name__ == "__main__":
    main()
