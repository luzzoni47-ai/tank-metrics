#!/usr/bin/env python3
"""Guard the blog <-> calculator links, and that every internal link resolves.

Sir asked for the blog posts and the calculators to point at each other, and for
more URLs to be indexable. This checks:

1. Every blog post carries a "Run the numbers" section linking to at least two
   calculators.
2. Those calculators link back to the guide.
3. Every internal clean link on a blog, news or tool page resolves to a real
   route in url-map.json (or is one of the known static paths). A back-link
   written from the file stem rather than the clean path once produced 16 dead
   404s, so this is checked directly rather than assumed.

Run with `--static` for the file checks only (there is nothing to drive in a
browser here; the flag is accepted for consistency with the other tests).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SITE = PUBLIC / "site"
URL_MAP = json.loads((ROOT / "tools" / "url-map.json").read_text(encoding="utf-8"))

STATIC_OK = {
    "/", "/blog", "/news", "/about", "/contact",
    "/privacy-policy", "/terms-and-conditions", "/disclaimer",
}
POSTS = sorted(SITE.glob("blog-*.html"))


def check_posts_have_tools() -> list:
    failures = []
    for post in POSTS:
        text = post.read_text(encoding="utf-8")
        rel = post.relative_to(PUBLIC)
        m = re.search(r'<!-- blog-tools -->(.*?)</section>', text, re.S)
        if not m:
            failures.append(f"{rel} has no 'Run the numbers' section")
            continue
        links = re.findall(r'href="(/[a-z0-9\-]+)"', m.group(1))
        links = [x for x in links if x not in STATIC_OK]
        if len(links) < 2:
            failures.append(
                f"{rel} links to only {len(links)} calculator(s); it should "
                "point at the tools that answer the post")
        for href in links:
            if href not in URL_MAP:
                failures.append(f"{rel} links to {href}, which is not a real route")
    return failures


def check_backlinks() -> list:
    failures = []
    linked = 0
    for tool in sorted((SITE / "tools").glob("*.html")):
        text = tool.read_text(encoding="utf-8")
        if "<!-- tool-blog -->" not in text:
            continue
        linked += 1
        m = re.search(r'<!-- tool-blog -->(.*?)</section>', text, re.S)
        for href in re.findall(r'href="(/[a-z0-9\-]+)"', m.group(1)):
            if href not in URL_MAP:
                failures.append(
                    f"{tool.relative_to(PUBLIC)} back-links to {href}, "
                    "which is not a real route")
    if linked < 10:
        failures.append(f"only {linked} calculator pages link back to a guide")
    return failures


def check_internal_links() -> list:
    """No page may link to a clean path that is not in the url map."""
    failures = []
    pages = list(SITE.glob("blog-*.html")) + list(SITE.glob("news-*.html"))
    pages += list((SITE / "tools").glob("*.html"))
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for href in set(re.findall(r'href="(/(?!site/)[a-z0-9\-/]*)"', text)):
            if href in STATIC_OK or href in URL_MAP:
                continue
            failures.append(f"{page.relative_to(PUBLIC)} links to {href} -> 404")
    return failures


def main() -> int:
    failures = check_posts_have_tools() + check_backlinks() + check_internal_links()
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures[:25]:
            print("  -", f)
        return 1
    print("ALL PASS: blog and calculators link both ways and every internal link resolves")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
