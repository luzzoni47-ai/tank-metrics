#!/usr/bin/env python3
"""Keep tools/gsc_submit_list.txt in step with the sitemap.

The list is what gets pushed to Search Console, so a URL that is in the
sitemap but not the list is a page Google is never told about. It drifted by
eight URLs (the newer guides and news stories) because it was maintained by
hand. This merges instead: existing entries are kept, anything new in the
sitemap is added, and the whole file is written in alphabetical order.

    python3 tools/sync_gsc_list.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "public" / "sitemap.xml"
LIST = ROOT / "tools" / "gsc_submit_list.txt"


def main() -> None:
    locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", SITEMAP.read_text(encoding="utf-8"))
    listed = [l.strip() for l in LIST.read_text(encoding="utf-8").splitlines() if l.strip()]
    merged = sorted(set(locs) | set(listed))
    added = sorted(set(locs) - set(listed))
    LIST.write_text("\n".join(merged) + "\n", encoding="utf-8")
    print(f"list: {len(listed)} -> {len(merged)} ({len(added)} added)")
    for a in added:
        print("  +", a)


if __name__ == "__main__":
    main()
