#!/usr/bin/env python3
"""Write the two static markers the app shell reads.

``updates.json`` is the "what is new" marker. The static pages cannot push
anything on their own, so a returning visitor is told about new content when
the page opens: it fetches this file, compares the version with what it stored
last time, and speaks up if they differ. The version is a hash of the sitemap,
so adding a calculator or a post changes it and nothing else does.

``precache.json`` is the offline page list. The service worker used to cache
only the shell plus whatever page happened to be visited, so a visitor who
read one calculator had nothing else offline - /about, /blog, /news and the
rest of the 101 tools all failed. The worker now reads this list on install
and stores every page, which is the whole point of an offline calculator site.
"""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "public" / "site"
SITEMAP = ROOT / "public" / "sitemap.xml"
SW = ROOT / "public" / "sw.js"

# The shell assets the service worker serves cache-first. Its VERSION must
# change whenever any of them changes, or a returning visitor keeps the old
# copy: a CSS-only fix (like a pager restyle) would never reach them because
# the sitemap - the old version source - did not move. sw.js itself is NOT in
# this list, or rewriting it would change its own hash.
SHELL_ASSETS = (
    "public/site/style.css",
    "public/site/pagination.js",
    "public/site/pwa.js",
    "public/site/theme.js",
    "public/site/rating.js",
    "public/site/manifest.webmanifest",
)


def asset_version() -> str:
    """A version tag over the cache-first shell assets."""
    h = hashlib.sha256()
    for rel in SHELL_ASSETS:
        p = ROOT / rel
        if p.exists():
            h.update(p.read_bytes())
    return "tm-" + h.hexdigest()[:10]


def write_sw_version() -> str:
    """Stamp the asset hash into sw.js so the browser sees a new worker.

    The browser only re-runs install (which re-fetches the shell) when sw.js
    changes byte-for-byte. Rewriting the VERSION constant here is what makes a
    stylesheet edit invalidate the old cache.
    """
    version = asset_version()
    text = SW.read_text(encoding="utf-8")
    new_text, n = re.subn(
        r'const VERSION = "[^"]*";', f'const VERSION = "{version}";', text, count=1
    )
    if n == 0:
        raise SystemExit("sw.js has no `const VERSION` line to stamp")
    if new_text != text:
        SW.write_text(new_text, encoding="utf-8")
    return version


def main() -> None:
    urls = []
    if SITEMAP.exists():
        urls = re.findall(r"<loc>([^<]+)</loc>", SITEMAP.read_text(encoding="utf-8"))
    digest = hashlib.sha256("\n".join(sorted(urls)).encode()).hexdigest()[:12]
    tools = len(list((SITE / "tools").glob("*.html")))
    data = {
        "version": digest,
        "pages": len(urls),
        "tools": tools,
        "label": f"{tools} calculators and {len(urls)} pages - all free, all offline.",
        "href": "/blog",
    }
    (SITE / "updates.json").write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")

    # The sitemap is absolute; the worker wants same-origin paths, and "/" must
    # be in the list because the home page is a rewrite that the sitemap covers
    # with its own entry but the worker has to fetch by path.
    paths = []
    for u in urls:
        p = urlparse(u).path or "/"
        if p not in paths:
            paths.append(p)
    if "/" not in paths:
        paths.insert(0, "/")
    (SITE / "precache.json").write_text(
        json.dumps({"version": digest, "paths": paths}, indent=1) + "\n", encoding="utf-8"
    )
    sw_version = write_sw_version()
    print(f"updates.json: version {digest}, {len(urls)} pages, {tools} tools")
    print(f"precache.json: {len(paths)} paths")
    print(f"sw.js: VERSION {sw_version} (shell asset hash)")


if __name__ == "__main__":
    main()
