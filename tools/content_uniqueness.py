#!/usr/bin/env python3
"""Measure duplicate content across the calculator pages - the real indexing blocker.

Only 5 of 125 pages were indexed. The site is technically clean (every sitemap
URL answers 200, has a title, a canonical, a description, no noindex, and
IndexNow announces every change), so none of the usual blockers explain it.

Two facts do:

  1. IndexNow does not reach Google. Google never adopted the protocol; a ping
     goes to Bing, Yandex, Seznam and Naver. The daily IndexNow sweep is real
     and worth keeping, but it cannot be the reason Google indexes a page.
  2. 97 of the 101 calculators have no guide of their own. `gen_tool_pages.py`
     falls back to a shared per-CATEGORY template, so every calculator in a
     category renders the same "What this calculator is for", "How the maths
     works", "Common mistakes" and worked-example prose. On the live site two
     pages in the same category share 60-73% of their 5-word phrases.

Google does not index near-duplicate pages; it picks one and leaves the rest
out. That is why five pages got in and the other hundred did not.

This tool measures the overlap so the number is visible and can be driven down
as real per-calculator copy replaces the shared template. It runs against the
BUILT files through tools/url-map.json, so it sees exactly what a crawler sees.

    python3 tools/content_uniqueness.py              # report
    python3 tools/content_uniqueness.py --top 15     # worst pairs
    python3 tools/content_uniqueness.py --live       # measure the live site
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
URL_MAP = ROOT / "tools" / "url-map.json"

# 5-word shingles. Long enough that boilerplate nav and a shared sentence about
# rounding both count, short enough to catch a paragraph copied between pages.
SHINGLE = 5
# A pair above this is close enough that Google will likely index only one of
# them. Reported as a blocker, not a warning.
DUPLICATE = 0.50

STRIP = re.compile(r"<(script|style|nav|footer|header|aside)[^>]*>.*?</\1>", re.S | re.I)
TAGS = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def guide_text(html: str) -> str:
    """The prose a crawler reads, minus the shell.

    The page shell (topbar, footer, inline calculator logic) is identical on
    every page by design and would swamp the measurement. What matters for
    duplicate-content is the guide copy under the calculator.
    """
    h = STRIP.sub(" ", html)
    # The guide lives in the .page-wrap block, after the calculator card.
    m = re.search(r'<div class="page-wrap"[^>]*>(.*)$', h, re.S | re.I)
    body = m.group(1) if m else h
    body = TAGS.sub(" ", body)
    return WS.sub(" ", body).strip()


def shingles(text: str) -> set[str]:
    w = text.split()
    return {" ".join(w[i:i + SHINGLE]) for i in range(max(0, len(w) - SHINGLE + 1))}


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / max(1, len(a | b))


def local_pages() -> list[tuple[str, str]]:
    """Every calculator page in the build, as (path, html)."""
    pages = []
    for p in sorted((PUBLIC / "site" / "tools").glob("*.html")):
        pages.append((f"/{p.stem}", p.read_text(encoding="utf-8", errors="replace")))
    return pages


def live_pages() -> list[tuple[str, str]]:
    import ssl
    import urllib.request

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    base = "https://tankmetrics.in"
    with urllib.request.urlopen(f"{base}/sitemap.xml", timeout=25, context=ctx) as r:
        xml = r.read().decode("utf-8", "replace")
    urls = [u.strip() for u in re.findall(r"<loc>\s*(.*?)\s*</loc>", xml)]
    tools = [u for u in urls if "/tools/" in u or re.search(r"^https://tankmetrics\.in/[a-z0-9-]+$", u)]

    def get(u):
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "gzip"})
        try:
            with urllib.request.urlopen(req, timeout=25, context=ctx) as f:
                b = f.read()
                if f.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    b = gzip.decompress(b)
                return u.replace(base, "") or "/", b.decode("utf-8", "replace")
        except Exception:
            return None

    with ThreadPoolExecutor(8) as ex:
        out = [x for x in ex.map(get, tools) if x]
    return out


def report(pages: list[tuple[str, str]], top: int) -> dict:
    texts = [(path, guide_text(html)) for path, html in pages]
    texts = [(p, t) for p, t in texts if len(t.split()) > 50]
    sh = {p: shingles(t) for p, t in texts}
    pairs = []
    for (p1, _), (p2, _) in itertools.combinations(texts, 2):
        j = jaccard(sh[p1], sh[p2])
        if j >= 0.30:
            pairs.append((j, p1, p2))
    pairs.sort(reverse=True)

    # For each page, its worst match: how close is it to the most similar page?
    worst: dict[str, float] = {}
    for j, p1, p2 in pairs:
        worst[p1] = max(worst.get(p1, 0), j)
        worst[p2] = max(worst.get(p2, 0), j)

    dup = sorted(
        ((p, j) for p, j in worst.items() if j >= DUPLICATE),
        key=lambda x: -x[1],
    )
    return {
        "pages_measured": len(texts),
        "pages_with_a_near_duplicate": len(dup),
        "worst_pairs": [{"overlap": round(j, 3), "a": p1, "b": p2} for j, p1, p2 in pairs[:top]],
        "worst_pages": [{"page": p, "closest_overlap": round(j, 3)} for p, j in dup[:top]],
        "median_overlap": round(
            sorted(worst.values())[len(worst) // 2], 3) if worst else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--live", action="store_true", help="measure the live site, not the build")
    args = ap.parse_args()

    pages = live_pages() if args.live else local_pages()
    if not pages:
        print("no pages found", file=sys.stderr)
        return 1

    data = report(pages, args.top)
    print(f"pages measured: {data['pages_measured']}")
    print(f"pages with a near-duplicate (>= {DUPLICATE:.0%}): "
          f"{data['pages_with_a_near_duplicate']}")
    print(f"median closest-overlap: {data['median_overlap']:.0%}")
    print()
    print("worst pairs:")
    for row in data["worst_pairs"]:
        print(f"  {row['overlap']:.0%}  {row['a']}  <>  {row['b']}")
    print()
    print("worst pages (closest match):")
    for row in data["worst_pages"]:
        print(f"  {row['closest_overlap']:.0%}  {row['page']}")

    # A machine-readable copy for the daily automation to diff between runs.
    (ROOT / "tools" / "content_uniqueness.json").write_text(
        json.dumps(data, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
