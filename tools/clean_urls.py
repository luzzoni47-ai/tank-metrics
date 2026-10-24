#!/usr/bin/env python3
"""Move the site onto clean, extensionless URLs.

Every page was reachable at /site/<name>.html and every tool at
/site/tools/<slug>.html. That is what Google indexed and what the sitemap
advertised, so the address bar showed an implementation detail.

This rewrites the crawl surface to /about, /sip-calculator and
/blog/what-is-ebitda:

  1. tools/url-map.json - clean path -> the static file that backs it, which
     next.config.mjs turns into rewrites (so the URL stays clean) and into
     permanent redirects (so the old .html URLs consolidate instead of
     competing as duplicates).
  2. Every href, canonical and og:url inside public/site/**/*.html.
  3. public/sitemap.xml.

Run it after gen_tool_pages.py and wire_crawl_graph.py; both of those still
emit .html links on purpose, so this stays the single place that decides what
a public URL looks like.
"""
import json
import re
from pathlib import Path

from gen_tool_pages import build_slugs

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
DATA = json.loads((Path(__file__).parent / "calcs.json").read_text(encoding="utf-8"))

# Hand-written pages that get a clean, top-level URL.
STATIC_PAGES = {
    "about": "/about",
    "contact": "/contact",
    "blog": "/blog",
    "news": "/news",
    "privacy-policy": "/privacy-policy",
    "terms-and-conditions": "/terms-and-conditions",
    "disclaimer": "/disclaimer",
    "digital-products": "/digital-products",
    "refund-policy": "/refund-policy",
}

# Pages that live in their own directory under /site and keep a nested clean
# URL, e.g. the product landing page at /digital-products/<slug>. A flat
# STATIC_PAGES entry cannot express this, because the clean path and the file
# path share the /digital-products segment.
NESTED_PAGES = {
    "digital-products/indian-business-financial-model":
        "/digital-products/indian-business-financial-model",
}


def build_map() -> dict[str, str]:
    """clean path -> backing static file, for every public page."""
    m: dict[str, str] = {v: f"/site/{k}.html" for k, v in STATIC_PAGES.items()}
    m.update({v: f"/site/{k}.html" for k, v in NESTED_PAGES.items()})
    slugs = build_slugs(DATA["calcs"])
    for c in DATA["calcs"]:
        m[f"/{slugs[c['id']]}"] = f"/site/tools/{slugs[c['id']]}.html"
    for f in sorted(SITE.glob("news-*.html")):
        slug = f.name[len("news-"):-len(".html")]
        m[f"/{slug}"] = f"/site/{f.name}"
    for f in sorted(SITE.glob("blog-*.html")):
        slug = f.name[len("blog-"):-len(".html")]
        m[f"/{slug}"] = f"/site/{f.name}"
    dupes = [k for k in m if list(m).count(k) > 1]
    if len(set(m)) != len(m):
        raise SystemExit(f"duplicate clean paths: {dupes}")
    return dict(sorted(m.items()))


def replacements(m: dict[str, str]) -> list[tuple[str, str]]:
    """(old fragment, new fragment) pairs, relative form first.

    Absolute URLs contain the relative path as a substring, so replacing the
    relative form also fixes canonical/og:url without a second rule.
    """
    pairs = []
    for clean, file in m.items():
        pairs.append((file, clean))
        # An earlier revision nested blog posts under /blog/<slug>. Normalise
        # that so re-running never leaves a stale canonical behind.
        if file.startswith("/site/blog-"):
            pairs.append((f"/blog{clean}", clean))
    # The home page is served by a rewrite from /, so /site/index.html should
    # only ever be linked as /.
    pairs.append(("/site/index.html", "/"))
    # Longest first so /site/blog-what-is-ebitda.html is never clipped by a
    # shorter sibling rule.
    return sorted(pairs, key=lambda p: -len(p[0]))


def rewrite_html(m: dict[str, str]) -> tuple[int, int]:
    pairs = replacements(m)
    files, edits = 0, 0
    for p in sorted(SITE.rglob("*.html")):
        t = orig = p.read_text(encoding="utf-8")
        for old, new in pairs:
            if old in t:
                edits += t.count(old)
                t = t.replace(old, new)
        if t != orig:
            p.write_text(t, encoding="utf-8")
            files += 1
    return files, edits


def rewrite_sitemap(m: dict[str, str]) -> int:
    p = ROOT / "public" / "sitemap.xml"
    t = p.read_text(encoding="utf-8")
    for old, new in replacements(m):
        t = t.replace(f"https://tankmetrics.in{old}", f"https://tankmetrics.in{new}")
    p.write_text(t, encoding="utf-8")
    return t.count("<loc>")


def check_no_shadowing(m: dict[str, str]) -> list[str]:
    """A clean path must not collide with a real file or directory."""
    taken = {f"/{p.name}" for p in (ROOT / "public").iterdir()}
    taken |= {"/_next", "/api", "/site"}
    return [c for c in m if c in taken]


def main() -> None:
    m = build_map()
    clashes = check_no_shadowing(m)
    if clashes:
        raise SystemExit(f"clean paths would shadow real files: {clashes}")
    (Path(__file__).parent / "url-map.json").write_text(
        json.dumps(m, indent=2) + "\n", encoding="utf-8")
    files, edits = rewrite_html(m)
    urls = rewrite_sitemap(m)
    print(f"url-map entries: {len(m)}")
    print(f"html files rewritten: {files} ({edits} link/url edits)")
    print(f"sitemap urls: {urls}")
    print("sample:", ", ".join(list(m)[:3]))


if __name__ == "__main__":
    main()
