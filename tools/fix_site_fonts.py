#!/usr/bin/env python3
"""Put the home page's fonts on every page.

The tool, category and news pages get their font link from a generator, so
swapping the link there covers them. Two kinds of page are written by hand or
copied from another page and never see a generator:

* the static pages (about, contact, blog, the legal pages);
* every guide, because `new_blog_post.py` copies the shell from an existing
  post, so a post written today inherits whatever font link its reference
  carried.

Those 31 pages kept loading Poppins and Gloock while the rest of the site
moved to Plus Jakarta Sans and Inter, so the site looked like two sites. This
runs after the page writers and rewrites the old link in place, so a guide
added later is corrected on its next rebuild without anyone remembering to.

Idempotent: a page already carrying the new link is left alone.

    python3 tools/fix_site_fonts.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
sys.path.insert(0, str(ROOT / "tools"))
from design import OLD_FONT_LINK, SITE_FONT_LINK  # noqa: E402


def main() -> None:
    changed, already, stale = 0, 0, []
    for page in sorted(SITE.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        if OLD_FONT_LINK in text:
            page.write_text(text.replace(OLD_FONT_LINK, SITE_FONT_LINK),
                            encoding="utf-8")
            changed += 1
        elif SITE_FONT_LINK in text:
            already += 1
        else:
            stale.append(page.relative_to(SITE).as_posix())
    print(f"font link updated on {changed} page(s), {already} already current")
    # A page with neither link has a font problem this script cannot see, and
    # silence there is how the split look came back last time. Name it.
    if stale:
        print(f"  {len(stale)} page(s) carry neither font link: {stale[:5]}")


if __name__ == "__main__":
    main()
