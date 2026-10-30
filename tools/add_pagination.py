#!/usr/bin/env python3
"""Add the phone pager script to the listing pages.

Sir asked for the Guides and News listings to show 10 cards at a time on a
phone, with a numbered pager underneath. The behaviour lives in
``public/site/pagination.js``; this tool only wires that file into the pages.

A tool rather than a hand edit because ``gen_news.py`` rewrites ``news.html``
from scratch on every rebuild, so anything typed into that file by hand is gone
by the next run. Idempotent: a page that already names the script is left alone.

Only the two listing pages carry a pager. The grids they hold are the ones
``pagination.js`` looks for (``.blog-grid``, ``#newsGrid``, ``#guidesGrid``).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "public" / "site"

SCRIPT = '<script defer src="/site/pagination.js"></script>'
PAGES = ("blog.html", "news.html")


def main() -> None:
    changed = 0
    for name in PAGES:
        page = SITE / name
        if not page.exists():
            continue
        text = page.read_text(encoding="utf-8")
        if SCRIPT in text:
            continue
        if "</body>" in text:
            text = text.replace("</body>", SCRIPT + "</body>", 1)
        else:
            text = text + SCRIPT
        page.write_text(text, encoding="utf-8")
        changed += 1
    print(f"pagination script added to {changed} page(s)")


if __name__ == "__main__":
    main()
