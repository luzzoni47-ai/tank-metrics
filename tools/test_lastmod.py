#!/usr/bin/env python3
"""Guard lastmod honesty: a page that did not change must not re-date.

On 2026-10-31 all 178 sitemap URLs said "today", every day. wire_crawl_graph
wrote the sitemap at step 46 of rebuild.sh, but add_pwa, add_pagination,
fix_static_seo and add_site_verification rewrote every page after it, so the
hash it stored never matched the file that shipped and every run re-dated the
whole sitemap. Google discounts a lastmod that always says "today", so the one
indexing lever this repo controls was dead.

The failure was silent - every other test passed, because none of them ran the
rebuild twice and compared. This one does the cheap version of that: it checks
that lastmod_stamp.py, run twice in a row with no page edits between, reports
no changes on the second pass.

    python3 tools/test_lastmod.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "public" / "sitemap.xml"
LEDGER = Path(__file__).resolve().parent / "lastmod.json"
PLACEHOLDER = "1970-01-01"


def main() -> int:
    if not SITEMAP.is_file():
        print("FAIL: public/sitemap.xml is missing")
        return 1
    text = SITEMAP.read_text(encoding="utf-8")
    if PLACEHOLDER in text:
        print(f"FAIL: {text.count(PLACEHOLDER)} URL(s) still hold the lastmod "
              "placeholder - lastmod_stamp.py did not run after the page writers")
        return 1
    if not LEDGER.is_file():
        print("FAIL: tools/lastmod.json is missing; lastmod_stamp.py never ran")
        return 1

    before_sm = text
    before_lm = LEDGER.read_text(encoding="utf-8")

    # A second pass with no page edits must change nothing. If the stamp is
    # taken from a half-finished page, or keyed on the wrong path, this is the
    # step that re-dates everything and the assertion below catches it.
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "lastmod_stamp.py")],
        capture_output=True, text=True)
    out = proc.stdout.strip()
    if proc.returncode != 0:
        print(f"FAIL: lastmod_stamp.py exited {proc.returncode}: {out} {proc.stderr.strip()}")
        return 1
    m = re.search(r"(\d+) changed, (\d+) unchanged", out)
    if not m:
        print(f"FAIL: could not read lastmod_stamp.py output: {out}")
        return 1
    changed, unchanged = int(m.group(1)), int(m.group(2))
    if changed:
        print(f"FAIL: {changed} URL(s) re-dated on a no-op run - lastmod is "
              "not honest, so Google will discount the whole sitemap")
        return 1

    if SITEMAP.read_text(encoding="utf-8") != before_sm:
        print("FAIL: sitemap changed on a no-op lastmod pass")
        return 1
    if LEDGER.read_text(encoding="utf-8") != before_lm:
        print("FAIL: lastmod ledger changed on a no-op lastmod pass")
        return 1

    urls = len(re.findall(r"<lastmod>", before_sm))
    print(f"ALL PASS: {unchanged} lastmods stable on a no-op run, "
          f"0 re-dated, {urls} URLs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
