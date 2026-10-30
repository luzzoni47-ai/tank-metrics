#!/usr/bin/env python3
"""Put the search-engine verification tags in every page's <head>.

Google's tag already ships from each generator, which is why it kept going
missing on a page a generator did not know about. Bing's tag has no generator
at all, so it is added here, once, as a post-pass over the built site.

This runs over `rglob("*.html")`, not `glob("*.html")`: the flat glob silently
skips the nested pages (the product page and the keyword pages), and a
verification tag missing from the page Google sends people to is exactly the
bug this file exists to prevent.

Idempotent: an existing tag is rewritten in place, never duplicated.

    python3 tools/add_site_verification.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"

GOOGLE = "CyIhu9CYYQapfzYJOeSLTP_XY_HWq0McbmY4uX342o4"
BING = "AA5D99339B17E03BF38E9D3CA67A125C"

TAGS = (
    f'<meta name="google-site-verification" content="{GOOGLE}">',
    f'<meta name="msvalidate.01" content="{BING}">',
)

# Match the whole tag with its content, so a rotated token replaces the old one
# instead of sitting beside it.
EXISTING = re.compile(
    r'<meta name="(?:google-site-verification|msvalidate\.01)" content="[^"]*">')


def strip_tags(t: str) -> str:
    return EXISTING.sub("", t)


def insert(t: str, tags: str) -> str | None:
    if "<meta charset" in t:
        i = t.index("<meta charset")
        j = t.index(">", i) + 1
        return t[:j] + tags + t[j:]
    if "<head>" in t:
        return t.replace("<head>", "<head>" + tags, 1)
    return None


def main() -> None:
    changed = 0
    skipped = []
    for f in sorted(SITE.rglob("*.html")):
        t = f.read_text(encoding="utf-8")
        clean = strip_tags(t)
        out = insert(clean, "".join(TAGS))
        if out is None:
            skipped.append(str(f.relative_to(SITE)))
            continue
        if out != t:
            f.write_text(out, encoding="utf-8")
            changed += 1

    total = len(list(SITE.rglob("*.html")))
    print(f"verification tags: {changed} file(s) updated, {total} scanned")
    if skipped:
        print(f"  SKIP (no head): {', '.join(skipped)}")


if __name__ == "__main__":
    main()
