#!/usr/bin/env python3
"""Guard public/llms.txt: no redirecting links, all calculators present.

llms.txt is what AI answer engines (ChatGPT, Gemini, Perplexity, Claude) read to
decide what the site offers and which URLs to cite. It shipped for months with
two faults: every link pointed at a raw `/site/*.html` path that now 308-redirects
to the clean URL, and none of the 101 calculators were listed at all. Both are
silent - the file exists and is valid markdown, so nothing failed.

This test checks the file against tools/url-map.json, the source of truth:

  1. every link is a clean public URL (no /site/, no .html), so none redirects;
  2. every calculator page in the sitemap appears in llms.txt;
  3. the main pages and the news desk are listed;
  4. no link points at a page that does not exist in url-map.

    python3 tools/test_llms.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
LLMS = PUBLIC / "llms.txt"
URL_MAP = ROOT / "tools" / "url-map.json"

LINK_RE = re.compile(r"\[[^\]]*\]\((https://tankmetrics\.in[^)]*)\)")


def main() -> int:
    if not LLMS.is_file():
        print("FAIL: public/llms.txt is missing")
        return 1
    if not URL_MAP.is_file():
        print("FAIL: tools/url-map.json is missing")
        return 1

    text = LLMS.read_text(encoding="utf-8")
    url_map = json.loads(URL_MAP.read_text(encoding="utf-8"))
    known = set(url_map.keys())

    links = [u.rstrip("/") or "/" for u in LINK_RE.findall(text)]
    problems: list[str] = []

    # 1. No raw /site/ paths or .html - those redirect.
    bad = [u for u in links if "/site/" in u or u.endswith(".html")]
    if bad:
        problems.append(f"{len(bad)} link(s) point at a redirecting path, e.g. {bad[:3]}")

    # 2. Every calculator in url-map must be listed.
    calc_paths = {cp for cp, built in url_map.items() if built.startswith("/site/tools/")}
    listed = {u.replace("https://tankmetrics.in", "") or "/" for u in links}
    missing_calcs = sorted(calc_paths - listed)
    if missing_calcs:
        problems.append(f"{len(missing_calcs)} calculator(s) missing, e.g. {missing_calcs[:3]}")

    # 3. Main pages present.
    for must in ("/", "/blog", "/news"):
        if must not in listed:
            problems.append(f"main page {must} is not listed")

    # 4. No link to an unknown page.
    unknown = sorted(u for u in listed if u not in known and u != "/")
    if unknown:
        problems.append(f"{len(unknown)} link(s) not in url-map, e.g. {unknown[:3]}")

    print(f"llms.txt links: {len(links)}  |  calculators listed: "
          f"{len(calc_paths & listed)}/{len(calc_paths)}")
    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("OK: llms.txt has clean links and every calculator")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
