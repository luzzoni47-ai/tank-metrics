#!/usr/bin/env python3
"""Stamp an honest <lastmod> on every sitemap URL, from the FINAL files.

This is the last writer of public/sitemap.xml in rebuild.sh, and it has to be
last. wire_crawl_graph.py writes the sitemap early (step 46), then add_pwa,
add_pagination, fix_static_seo and add_site_verification rewrite every page
after it. A hash taken at step 46 is a hash of a half-finished page, so it
never matches the file that ships and every run re-dated all 178 URLs "today".
Google discounts a lastmod that always says "today", so the whole signal was
worth nothing - and the sitemap is the one indexing lever this run controls.

So the sitemap is written with a placeholder date, and this step - running
after the last page mutation - hashes the shipped file and advances a URL's
date only when that hash actually changes. Unchanged pages keep their date.

    python3 tools/lastmod_stamp.py
    python3 tools/lastmod_stamp.py --backfill   # one-off: seed dates from git
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from clean_urls import build_map

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
SITEMAP = PUBLIC / "sitemap.xml"
LEDGER = Path(__file__).resolve().parent / "lastmod.json"

# The placeholder wire_crawl_graph.py writes, so this step can tell a URL it
# still has to stamp from one already done (a re-run leaves real dates alone).
PLACEHOLDER = "1970-01-01"
DATE_RE = re.compile(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})"')


def clean_to_file() -> dict[str, str]:
    """clean public path -> backing file path relative to public/."""
    m = {clean: f"public{file}" for clean, file in build_map().items()}
    # The home page is a rewrite of /site/index.html and is not in build_map.
    m["/"] = "public/site/index.html"
    return m


def published_date(path: Path) -> str | None:
    m = DATE_RE.search(path.read_text(encoding="utf-8", errors="ignore"))
    return m.group(1) if m else None


def git_dates() -> dict[str, str]:
    """clean path -> the date its file was last committed, per git.

    Used only by --backfill, to seed the ledger from real history rather than
    claiming every page changed today. A fresh clone has no history and returns
    nothing, which is why the normal run never depends on this.
    """
    files = clean_to_file()
    rels = {rel for rel in files.values()}
    dates: dict[str, str] = {}
    # One git call for the whole set: `<date> <path>` per commit, newest first,
    # so the first sighting of a path is its last change.
    try:
        out = subprocess.run(
            ["git", "log", "--name-only", "--format=%cs", "--", *sorted(rels)],
            cwd=ROOT, capture_output=True, text=True, timeout=120).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    cur = ""
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", line):
            cur = line
        elif cur:
            rel = line
            for clean, f in files.items():
                if f == rel and clean not in dates:
                    dates[clean] = cur
    return dates


def main() -> int:
    backfill = "--backfill" in sys.argv
    if not SITEMAP.is_file():
        raise SystemExit("public/sitemap.xml is missing; run wire_crawl_graph.py first")

    files = clean_to_file()
    ledger: dict = {}
    if LEDGER.is_file():
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    if backfill:
        for clean, stamp in git_dates().items():
            digest = hashlib.sha256((PUBLIC.parent / files[clean]).read_bytes()).hexdigest()
            ledger[clean] = {"hash": digest, "lastmod": stamp}

    today = date.today().isoformat()
    text = SITEMAP.read_text(encoding="utf-8")
    out, pos, changed, kept, unstamped = [], 0, 0, 0, []
    url_re = re.compile(r"<url><loc>(.*?)</loc><lastmod>(.*?)</lastmod>", re.S)

    for m in url_re.finditer(text):
        out.append(text[pos:m.start()])
        loc, stamp = m.group(1), m.group(2)
        clean = loc.split("tankmetrics.in", 1)[-1]
        rel = files.get(clean)
        path = PUBLIC.parent / rel if rel else None
        if path is None or not path.is_file():
            # Not a page this step knows about; leave its date untouched.
            unstamped.append(clean)
            out.append(m.group(0))
            pos = m.end()
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        prev = ledger.get(clean)
        if prev and prev.get("hash") == digest and prev.get("lastmod"):
            stamp, kept = prev["lastmod"], kept + 1
        else:
            # A dated post keeps its real publication date; a post scheduled
            # ahead of today must not claim a future lastmod.
            stamp = min(published_date(path) or today, today)
            changed += 1
        ledger[clean] = {"hash": digest, "lastmod": stamp}
        out.append(f"<url><loc>{loc}</loc><lastmod>{stamp}</lastmod>")
        pos = m.end()

    out.append(text[pos:])
    SITEMAP.write_text("".join(out), encoding="utf-8")
    LEDGER.write_text(
        json.dumps(ledger, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    left = SITEMAP.read_text(encoding="utf-8").count(f"<lastmod>{PLACEHOLDER}")
    print(f"lastmod stamped: {changed} changed, {kept} unchanged, "
          f"{len(unstamped)} not mapped, {left} placeholders left")
    if unstamped:
        print("  not mapped:", ", ".join(unstamped[:5]))
    return 1 if left else 0


if __name__ == "__main__":
    raise SystemExit(main())
