#!/usr/bin/env python3
"""Write public/site/updates.json, the "what is new" marker.

The static pages cannot push anything on their own, so a returning visitor is
told about new content when the page opens: it fetches this file, compares the
version with what it stored last time, and speaks up if they differ. The
version is a hash of the sitemap, so adding a calculator or a post changes it
and nothing else does.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "public" / "site"
SITEMAP = ROOT / "public" / "sitemap.xml"


def main() -> None:
    urls = []
    if SITEMAP.exists():
        import re
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
    print(f"updates.json: version {digest}, {len(urls)} pages, {tools} tools")


if __name__ == "__main__":
    main()
