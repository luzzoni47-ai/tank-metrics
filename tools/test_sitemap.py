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

    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures:
            print(f"  {f}")
        return 1
    print(f"ALL PASS: all {len(locs)} sitemap URLs cover every public page")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
