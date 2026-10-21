#!/usr/bin/env python3
"""Add Article + BreadcrumbList schema to the static blog posts.

The news pages already carry NewsArticle and breadcrumb structured data, but
the guides did not. That is what Google and the AI answer engines read to work
out what a page is about, who wrote it and when, so a guide without it is
weaker than it should be.

The date comes from the visible `.post-meta` span (e.g. "September 18, 2026"),
so the markup and the page can never disagree. Re-running is safe: an existing
block written by this script is replaced, not duplicated.

    python3 tools/add_blog_schema.py
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
BASE = "https://tankmetrics.in"
MARKER = "<!-- blog-schema -->"

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
DESC_RE = re.compile(r'<meta[^>]+name="description"[^>]*content="([^"]*)"', re.I)
CANON_RE = re.compile(r'<link[^>]+rel="canonical"[^>]*href="([^"]+)"', re.I)
DATE_RE = re.compile(r'<span>([A-Z][a-z]+ \d{1,2}, \d{4})</span>')
CAT_RE = re.compile(r'<span class="tag2">(.*?)</span>')
EXISTING = re.compile(re.escape(MARKER) + r".*?(?=</head>)", re.S)


def blocks(path: Path) -> str | None:
    t = path.read_text(encoding="utf-8")
    title = (TITLE_RE.search(t) or [None, ""])[1].strip()
    desc = (DESC_RE.search(t) or [None, ""])[1].strip()
    canon = (CANON_RE.search(t) or [None, ""])[1].strip()
    m = DATE_RE.search(t)
    if not (title and canon and m):
        return None
    try:
        date = datetime.strptime(m.group(1), "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return None
    cat_m = CAT_RE.search(t)
    section = cat_m.group(1).strip() if cat_m else "Guides"

    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title.split(" | ")[0],
        "description": desc,
        "datePublished": date,
        "dateModified": date,
        "articleSection": section,
        "inLanguage": "en-IN",
        "mainEntityOfPage": {"@type": "WebPage", "@id": canon},
        "author": {"@type": "Organization", "name": "Tank Metrics"},
        "publisher": {"@type": "Organization", "name": "Tank Metrics",
                      "url": BASE},
        "isAccessibleForFree": True,
    }
    crumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": BASE + "/blog"},
            {"@type": "ListItem", "position": 3, "name": title.split(" | ")[0],
             "item": canon},
        ],
    }
    out = MARKER
    for b in (article, crumb):
        out += ('<script type="application/ld+json">'
                + json.dumps(b, ensure_ascii=False) + "</script>")
    return out


def main() -> None:
    changed = 0
    for f in sorted(SITE.glob("blog-*.html")):
        new = blocks(f)
        if not new:
            print(f"  SKIP (no title/canonical/date): {f.name}")
            continue
        t = f.read_text(encoding="utf-8")
        if MARKER in t:
            t = EXISTING.sub("", t)
        t = t.replace("</head>", new + "</head>", 1)
        f.write_text(t, encoding="utf-8")
        changed += 1
        print(f"  schema added: {f.name}")
    print(f"\nposts updated: {changed}")


if __name__ == "__main__":
    main()
