#!/usr/bin/env python3
"""Guard the sitemap: every public page must be in it.

On 2026-10-23 the sitemap held 116 URLs while the site served 125. The nine
missing ones were all the news pages plus the /news index, because
wire_crawl_graph.write_sitemap() only globbed blog-*.html. Google had no crawl
path to any of them - they could never be indexed, which is exactly the problem
the SEO work is trying to fix. Nothing failed loudly: the monitor, the layout
tests and the PWA tests all passed, because each of them reads a different
source and none of them compares the two.

This test compares them. Every .html file under public/site that is a real page
must have a matching <loc> in the sitemap.

    python3 tools/test_sitemap.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
SITE = PUBLIC / "site"
SITEMAP = PUBLIC / "sitemap.xml"

# Pages that are deliberately not in the sitemap.
EXCLUDE = {"index.html", "_layout_probe.html", "_about_probe.html"}


def main() -> int:
    if not SITEMAP.is_file():
        print("FAIL: public/sitemap.xml is missing")
        return 1
    locs = set(re.findall(r"<loc>\s*(.*?)\s*</loc>", SITEMAP.read_text(encoding="utf-8")))
    # The sitemap holds CLEAN urls (/about, /loan-emi-calculator), so match on
    # the slug, not the file path.
    slugs = set()
    for loc in locs:
        path = loc.split("tankmetrics.in", 1)[-1].strip("/")
        slugs.add(path)

    failures = []
    missing = []
    for f in sorted(SITE.rglob("*.html")):
        rel = f.relative_to(SITE).as_posix()
        if f.name in EXCLUDE:
            continue
        # A page is expected in the sitemap under its clean slug. clean_urls.py
        # strips the blog-/news- prefix: blog-what-is-ebitda.html -> /what-is-ebitda.
        stem = f.stem
        for prefix in ("blog-", "news-"):
            if stem.startswith(prefix):
                stem = stem[len(prefix):]
                break
        candidates = {stem}
        if rel.startswith("tools/"):
            candidates.add(f.stem)
        # A page in its own directory keeps the directory in its clean URL:
        # /site/digital-products/<slug>.html is served at
        # /digital-products/<slug>, so the bare stem alone would never match.
        if "/" in rel:
            candidates.add(rel[:-len(".html")])
        if not (candidates & slugs):
            missing.append(rel)

    if missing:
        failures.append(
            f"{len(missing)} page(s) are not in the sitemap, so Google has no "
            "crawl path to them: " + ", ".join(missing[:10])
        )

    # The /news index was one of the nine that went missing.
    if "news" not in slugs:
        failures.append("/news is not in the sitemap")

    # A duplicated <loc> is invalid XML for a sitemap and makes Google distrust
    # the whole file. Two writers edit it (wire_crawl_graph and gen_news) and
    # they once disagreed on the URL shape, so every news URL landed twice -
    # 12 duplicates, and nothing caught it because the set() above hides them.
    locs_all = re.findall(r"<loc>\s*(.*?)\s*</loc>", SITEMAP.read_text(encoding="utf-8"))
    dupes = sorted({u for u in locs_all if locs_all.count(u) > 1})
    if dupes:
        failures.append(
            f"{len(dupes)} URL(s) appear more than once in the sitemap, which is "
            "invalid: " + ", ".join(dupes[:5])
        )

    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures:
            print(f"  {f}")
        return 1
    print(f"ALL PASS: all {len(locs)} sitemap URLs cover every public page")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
