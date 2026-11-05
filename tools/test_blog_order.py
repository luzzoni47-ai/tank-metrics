#!/usr/bin/env python3
"""Guard the /blog Guides grid: complete, and newest-first.

Two defects this catches, both silent on the live site:
- a guide page with no card (unreachable from /blog, "discovered not indexed"),
- a new guide appended at the END, so the newest post showed up last and the
  page's ItemList schema advertised the oldest ten.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "public" / "site"
LISTING = SITE / "blog.html"

SLUG_RE = re.compile(r'class="blog-card" href="/([^"]+)"')
DATE_RE = re.compile(r'"datePublished":\s*"([^"]+)"')


def main() -> int:
    t = LISTING.read_text(encoding="utf-8")
    pane = t.split('id="paneGuides"')[1].split('id="paneNews"')[0]
    slugs = SLUG_RE.findall(pane)

    fails = []

    pages = sorted(p.name[len("blog-"):-len(".html")]
                   for p in SITE.glob("blog-*.html"))
    missing = [s for s in pages if s not in slugs]
    if missing:
        fails.append(f"guide page(s) with no /blog card: {missing}")

    dupes = sorted({s for s in slugs if slugs.count(s) > 1})
    if dupes:
        fails.append(f"guide card(s) listed twice: {dupes}")

    dates = []
    for s in slugs:
        f = SITE / f"blog-{s}.html"
        m = DATE_RE.search(f.read_text(encoding="utf-8", errors="replace")) if f.exists() else None
        dates.append(m.group(1) if m else "0000-00-00")

    for i in range(1, len(dates)):
        if dates[i] > dates[i - 1]:
            fails.append(
                f"not newest-first at position {i + 1}: "
                f"{slugs[i]} ({dates[i]}) appears after {slugs[i - 1]} ({dates[i - 1]})")
            break

    if fails:
        for f in fails:
            print("FAIL:", f)
        return 1
    print(f"ALL PASS: {len(slugs)} guide cards, complete and newest-first")
    return 0


if __name__ == "__main__":
    sys.exit(main())
