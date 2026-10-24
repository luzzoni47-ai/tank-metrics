#!/usr/bin/env python3
"""Keep the site footer's Legal and Digital Products columns in step.

The footer is emitted by three generators (gen_tool_pages, gen_news and
gen_landing_page) and is also baked into the hand-written pages, so a product
link placed in a template would drift across 129 copies. This script is the one
place that decides what those two columns say, and rebuild.sh runs it after
every generator has written its pages.

It enforces three things on every page:

  * The Legal column carries all four legal pages, the refund policy included.
    Only the landing page footer had the refund link before.
  * A fifth column, Digital Products, holds the product. The heading is the
    category and the link below it is the product's name.
  * Nothing links to the retired /digital-products hub, which is now a
    permanent redirect to the product page. A link there costs the visitor a
    round trip and splits one page's ranking signals across two URLs.

    python3 tools/gen_products_page.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"

PRODUCT = "Indian Business Financial Model"
PRODUCT_URL = "/digital-products/indian-business-financial-model"

STALE_ITEM_RE = re.compile(
    r'<li><a href="/digital-products">Digital Products</a></li>')
STALE_HREF = 'href="/digital-products"'

LEGAL_RE = re.compile(
    r'(<div class="footer-col"><h4>Legal</h4><ul>)(.*?)(</ul></div>)', re.S)
POPULAR_RE = re.compile(
    r'(<div class="footer-col"><h4>Popular</h4><ul>.*?</ul></div>)', re.S)

REFUND_ITEM = '<li><a href="/refund-policy">Refund Policy</a></li>'
PRODUCT_COL = (
    '<div class="footer-col"><h4>Digital Products</h4><ul>'
    f'<li><a href="{PRODUCT_URL}">{PRODUCT}</a></li></ul></div>')

FOOTER_OPEN = '<footer class="site-footer">'
PRODUCT_HEADING = "<h4>Digital Products</h4>"


def normalise(text: str) -> str:
    """Return the page with both footer columns correct. Idempotent."""
    # Retire the hub link first. Doing it after the href rewrite below would
    # leave a second copy of the product link sitting inside the Legal column.
    text = STALE_ITEM_RE.sub("", text)
    text = text.replace(STALE_HREF, f'href="{PRODUCT_URL}"')

    def legal(m: re.Match) -> str:
        head, items, tail = m.group(1), m.group(2), m.group(3)
        if "/refund-policy" in items:
            return m.group(0)
        return head + items + REFUND_ITEM + tail

    text = LEGAL_RE.sub(legal, text)

    if PRODUCT_HEADING not in text:
        text, n = POPULAR_RE.subn(
            lambda m: m.group(1) + PRODUCT_COL, text, count=1)
        if n != 1:
            raise SystemExit(
                "a footer has no Popular column, so the product column has no "
                "anchor to sit after - fix the footer template")
    return text


def main() -> None:
    pages = sorted(SITE.rglob("*.html"))
    changed = 0
    missing = []
    for p in pages:
        t = orig = p.read_text(encoding="utf-8")
        if FOOTER_OPEN not in t:
            continue
        t = normalise(t)
        if PRODUCT_HEADING not in t:
            missing.append(p.relative_to(SITE).as_posix())
            continue
        if t != orig:
            p.write_text(t, encoding="utf-8")
            changed += 1
    if missing:
        raise SystemExit(f"pages without the product column: {missing}")
    print(f"footer normalised on {changed} of {len(pages)} page(s)")
    print(f"product link: {PRODUCT_URL}")


if __name__ == "__main__":
    main()
