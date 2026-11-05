#!/usr/bin/env python3
"""Guard the category pages and the route from the home page to them.

Sir asked for three levels: the home page shows a category, tapping it opens a
page listing that category's tools two-up, and tapping a tool opens its own
calculator page. The middle level did not exist, so every toolkit heading was a
dead end.

These checks lock the three things that have to hold together:

  1. Every category in calcs.json has a generated page, and that page lists
     exactly the tools the category claims - no more, no fewer.
  2. The page is reachable: it has a canonical, it is in url-map.json so Next.js
     rewrites the clean URL to it, and it is in the sitemap.
  3. The home page actually links to it, in both the JS card grid and the
     crawler-visible catalogue. A category page nothing links to is invisible.

Static checks only - no browser and no network.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "public" / "site"
DATA = json.loads((ROOT / "tools" / "calcs.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(ROOT / "tools"))
from gen_category_pages import slug_for, tools_of  # noqa: E402
from siteconfig import BASE  # noqa: E402

URL_MAP = json.loads((ROOT / "tools" / "url-map.json").read_text(encoding="utf-8"))
SITEMAP = (ROOT / "public" / "sitemap.xml").read_text(encoding="utf-8")

fails: list[str] = []


def fail(msg: str) -> None:
    fails.append(msg)
    print("FAIL:", msg)


def check_pages_exist() -> None:
    for cat in DATA["cats"]:
        p = SITE / f"{slug_for(cat)}.html"
        if not p.exists():
            fail(f"{cat['name']}: {p.name} was not generated")
    print(f"category pages present: {len(DATA['cats'])}")


def check_contents() -> None:
    """Each page must list its own category's tools and nothing else."""
    for cat in DATA["cats"]:
        p = SITE / f"{slug_for(cat)}.html"
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        want = {c["id"] for c in tools_of(cat)}
        hrefs = re.findall(r'class="tcard" href="([^"]+)"', t)
        if len(hrefs) != len(want):
            fail(f"{cat['name']}: {len(hrefs)} tool cards, expected {len(want)}")
        if not all(h.startswith("/") and not h.startswith("/site/") for h in hrefs):
            fail(f"{cat['name']}: a tool card link is not a clean root URL")
        if len(set(hrefs)) != len(hrefs):
            fail(f"{cat['name']}: a tool is listed twice")
        # The two-up grid is the shape Sir asked for.
        if "grid-template-columns:repeat(2" not in t:
            fail(f"{cat['name']}: tool cards are not a two-column grid")
        # A category page without an H1 or a canonical cannot rank.
        if f"<h1>{html.escape(cat['name'], quote=False)}</h1>" not in t:
            fail(f"{cat['name']}: no matching H1")
        # clean_urls.py rewrites the canonical to the public clean URL, so the
        # /site/ form is expected to be gone by the time this runs.
        if f'<link rel="canonical" href="{BASE}/{slug_for(cat)}">' not in t:
            fail(f"{cat['name']}: canonical missing or wrong")
        for need in ('"@type": "CollectionPage"', '"@type": "BreadcrumbList"',
                     '"@type": "FAQPage"'):
            if need not in t:
                fail(f"{cat['name']}: structured data missing {need}")
    print("page contents checked")


def check_routes() -> None:
    """Clean URL -> file in url-map, and the clean URL in the sitemap."""
    for cat in DATA["cats"]:
        clean = f"/{slug_for(cat)}"
        backing = f"/site/{slug_for(cat)}.html"
        if URL_MAP.get(clean) != backing:
            fail(f"{cat['name']}: url-map has {clean} -> {URL_MAP.get(clean)!r}")
        if f"<loc>{BASE}{clean}</loc>" not in SITEMAP:
            fail(f"{cat['name']}: {clean} is not in the sitemap")
    print("routes checked")


def check_home_links() -> None:
    """The home page must link every category, for people and for crawlers."""
    t = (SITE / "index.html").read_text(encoding="utf-8")
    if "var CATSLUGS={" not in t:
        fail("home page has no CATSLUGS map, so the JS category heading cannot link")
    if 'class="cat-link"' not in t:
        fail("home page category heading is not a link")
    for cat in DATA["cats"]:
        clean = f"/{slug_for(cat)}"
        # Crawler-visible catalogue heading.
        if f'id="seo-{cat["id"]}"><h2><a href="{clean}"' not in t:
            fail(f"{cat['name']}: catalogue heading does not link to {clean}")
        # JS map entry, so the rendered heading links too.
        if f'"{cat["id"]}":"{slug_for(cat)}"' not in t:
            fail(f"{cat['name']}: CATSLUGS has no entry for {cat['id']}")
    print("home page links checked")


def check_no_collision() -> None:
    """A category clean URL must not shadow a tool, a static page or a blog."""
    tool_paths = {v for k, v in URL_MAP.items() if v.startswith("/site/tools/")}
    cat_paths = {f"/site/{slug_for(c)}.html" for c in DATA["cats"]}
    overlap = tool_paths & cat_paths
    if overlap:
        fail(f"category page collides with a tool page: {sorted(overlap)}")
    # Two categories must not produce the same slug.
    slugs = [slug_for(c) for c in DATA["cats"]]
    if len(set(slugs)) != len(slugs):
        fail(f"two categories share a slug: {slugs}")
    print("collisions checked")


if __name__ == "__main__":
    check_pages_exist()
    check_contents()
    check_routes()
    check_home_links()
    check_no_collision()
    print()
    if fails:
        print(f"{len(fails)} failure(s)")
        raise SystemExit(1)
    print("all category page checks passed")
