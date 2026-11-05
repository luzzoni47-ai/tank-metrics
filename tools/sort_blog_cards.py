#!/usr/bin/env python3
"""Order the /blog Guides grid newest-first and keep it complete.

The listing was built append-only: `new_blog_post.py` added each new guide at
the END of the Guides grid, so the newest post showed up last, and the page's
ItemList schema - Google's "what is new here" signal - advertised the ten
OLDEST posts. A guide page could also lose its card entirely and become
unreachable from /blog (a page in the sitemap with no listing link is exactly
the "discovered, not indexed" shape Search Console warns about).

This rebuilds the Guides grid from the pages themselves: one card per
`blog-*.html`, ordered by that page's own `datePublished` (newest first), with
the category and accent the page already declares. A missing card is restored;
the news pane, the card markup and every page body are left alone.

    python3 tools/sort_blog_cards.py

Runs in `rebuild.sh` after the card writers and before `fix_static_seo`, so the
ItemList schema snapshots the newest-first order.
"""
from __future__ import annotations

import html as html_mod
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
LISTING = SITE / "blog.html"

GRID_OPEN = '<div class="blog-grid">'
CARD_RE = re.compile(r'<a class="blog-card".*?</a>', re.S)
SLUG_RE = re.compile(r'class="blog-card" href="/([^"]+)"')
ACCENT_RE = re.compile(r'border-top-color:\s*(#[0-9A-Fa-f]{6})')
CAT_RE = re.compile(r'<span class="cat">(.*?)</span>')
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
DESC_RE = re.compile(r'<meta[^>]+name="description"[^>]*content="([^"]*)"', re.I)
TAG2_RE = re.compile(r'<span class="tag2">(.*?)</span>')
DATE_RE = re.compile(r'"datePublished":\s*"([^"]+)"')
DEFAULT_ACCENT = "#4285f4"
MISSING_DATE = "0000-00-00"


def page_meta(slug: str) -> dict | None:
    """Read the fields a card needs from the page itself."""
    f = SITE / f"blog-{slug}.html"
    if not f.exists():
        return None
    t = f.read_text(encoding="utf-8", errors="replace")
    title = (TITLE_RE.search(t) or [None, ""])[1].split(" | ")[0].strip()
    desc = (DESC_RE.search(t) or [None, ""])[1].strip()
    cat = (TAG2_RE.search(t) or [None, "Guides"])[1].strip()
    date = (DATE_RE.search(t) or [None, MISSING_DATE])[1]
    return {"title": title, "desc": desc, "cat": cat, "date": date}


def accent_map(cards: list[tuple[str, str, str]]) -> dict[str, str]:
    """Most common accent per category, taken from the cards already present."""
    counts: dict[str, dict[str, int]] = {}
    for _slug, accent, cat in cards:
        if accent and cat:
            counts.setdefault(cat, {}).setdefault(accent, 0)
            counts[cat][accent] += 1
    return {cat: max(v, key=v.get) for cat, v in counts.items()}


def make_card(slug: str, meta: dict, accent: str) -> str:
    return (
        f'<a class="blog-card" href="/{slug}" style="border-top-color:{accent}">'
        f'<span class="cat">{meta["cat"]}</span>'
        f'<h2>{meta["title"]}</h2>'
        f'<p>{meta["desc"]}</p>'
        f'<span class="readmore">Read the guide \u2192</span> </a>'
    )


def main() -> int:
    text = LISTING.read_text(encoding="utf-8")
    pane = text.index('id="paneGuides"')
    grid_open = text.index(GRID_OPEN, pane)
    inner_start = grid_open + len(GRID_OPEN)
    inner_end = text.index("</div>", inner_start)
    inner = text[inner_start:inner_end]

    parsed: list[tuple[str, str, str, str]] = []  # slug, accent, cat, card_html
    for card in CARD_RE.findall(inner):
        slug = SLUG_RE.search(card)
        accent = ACCENT_RE.search(card)
        cat = CAT_RE.search(card)
        parsed.append((
            slug.group(1) if slug else "",
            accent.group(1) if accent else "",
            cat.group(1) if cat else "",
            card,
        ))

    accents = accent_map([(s, a, c) for s, a, c, _ in parsed])
    existing = {s: card for s, _a, _c, card in parsed if s}

    # Every guide page must have exactly one card. Build the full set from the
    # pages, then sort it by the page's own date.
    rows: list[tuple[str, str]] = []  # date, slug
    for f in sorted(SITE.glob("blog-*.html")):
        slug = f.name[len("blog-"):-len(".html")]
        meta = page_meta(slug)
        if not meta:
            continue
        rows.append((meta["date"], slug))

    rows.sort(key=lambda r: (r[0], r[1]), reverse=True)

    added, kept = 0, 0
    out = ""
    seen = set()
    for _date, slug in rows:
        if slug in existing:
            out += existing[slug]
            kept += 1
        else:
            meta = page_meta(slug)
            accent = accents.get(meta["cat"], DEFAULT_ACCENT)
            out += make_card(slug, meta, accent)
            added += 1
        seen.add(slug)

    # A card whose page is gone (rare) is kept so nothing silently disappears.
    for s, _a, _c, card in parsed:
        if s and s not in seen:
            out += card
            kept += 1

    if out == inner:
        print(f"blog cards: {kept + added} already newest-first, nothing to do")
        return 0

    LISTING.write_text(text[:inner_start] + out + text[inner_end:], encoding="utf-8")
    print(f"blog cards: {kept} kept, {added} restored, ordered newest-first")
    return 0


if __name__ == "__main__":
    sys.exit(main())
