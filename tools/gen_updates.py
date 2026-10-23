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
    print(f"updates.json: version {digest}, {len(urls)} pages, {tools} tools")
    print(f"precache.json: {len(paths)} paths")


if __name__ == "__main__":
    main()
