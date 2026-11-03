#!/usr/bin/env python3
"""Measure duplicate content across the calculator pages - the real indexing blocker.

The site is technically clean (every sitemap URL answers 200, has a title, a
canonical, a description, no noindex, and IndexNow announces every change), so
none of the usual blockers explain a low indexed count. Near-duplicate body copy
does: Google indexes one page of a near-duplicate cluster and drops the rest.

This tool measures that overlap so the number is visible and can be driven down
as real per-calculator copy replaces shared text. It runs against the BUILT
files, so it sees exactly what a crawler sees.

What counts as "content" here:

  * The page shell (topbar, footer, inline calculator script) is identical on
    every page by design, so it is stripped before measuring.
  * The site-wide chrome blocks (call-to-action, related tools, sources, prev/
    next nav) are also identical by construction, so they are stripped too.
  * The hidden Hinglish block is a translation of the same page, not original
    content, so it is stripped - leaving it in flatters the score.
  * What remains is the English prose a reader actually gets: the intro, the
    worked example, the guide and the FAQ.

The metric is the Jaccard overlap of 5-word shingles between every pair of
pages, reported as the median of each page's closest match. Drive that median
down each run.

    python3 tools/content_uniqueness.py              # report
    python3 tools/content_uniqueness.py --top 15     # worst pairs
    python3 tools/content_uniqueness.py --live       # measure the live site
    python3 tools/content_uniqueness.py --baseline HEAD   # before/after vs a git ref
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
URL_MAP = ROOT / "tools" / "url-map.json"

# 5-word shingles. Long enough that a shared sentence about rounding counts,
# short enough to catch a paragraph copied between pages.
SHINGLE = 5
# A pair above this is close enough that Google will likely index only one of
# them. Reported as a blocker, not a warning.
DUPLICATE = 0.50

STRIP = re.compile(r"<(script|style|nav|footer|header|aside)[^>]*>.*?</\1>", re.S | re.I)
# The Hinglish tab is the same page translated. Left in, it pads every page with
# a second copy of its own wording and hides overlap.
HINGLISH = re.compile(
    r'<div class="post-lang" data-lang="hinglish".*?(?=<h2>Frequently asked questions</h2>)',
    re.S | re.I,
)
# Blocks that are byte-identical on all pages by construction. They are site
# furniture, not per-page content, so they are not what this metric tracks.
CHROME = re.compile(
    r'<div class="cta-inline".*?</div>|'
    r'<section class="related-tools".*?</section>|'
    r'<section class="tool-sources".*?</section>|'
    r'<nav class="tool-nav".*?</nav>',
    re.S | re.I,
)
TAGS = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def guide_text(html: str) -> str:
    """The English prose a crawler reads, minus the shell, the translation and chrome."""
    h = HINGLISH.sub(" ", html)
    h = CHROME.sub(" ", h)
    h = STRIP.sub(" ", h)
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


def baseline_pages(ref: str) -> list[tuple[str, str]]:
    """The built calculator pages as they were at a git ref (the honest 'before')."""
    try:
        files = subprocess.check_output(
            ["git", "ls-files", "public/site/tools/*.html"], cwd=ROOT
        ).decode().split()
        pages = []
        for f in files:
            html = subprocess.check_output(
                ["git", "show", f"{ref}:{f}"], cwd=ROOT, stderr=subprocess.DEVNULL
            ).decode("utf-8", "replace")
            pages.append((f"/{Path(f).stem}", html))
        return pages
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"baseline unavailable: {e}", file=sys.stderr)
        return []


def report(pages: list[tuple[str, str]], top: int) -> dict:
    texts = [(path, guide_text(html)) for path, html in pages]
    texts = [(p, t) for p, t in texts if len(t.split()) > 50]
    sh = {p: shingles(t) for p, t in texts}
    pairs = []
    for (p1, _), (p2, _) in itertools.combinations(texts, 2):
        pairs.append((jaccard(sh[p1], sh[p2]), p1, p2))
    pairs.sort(reverse=True)

    # For each page, its worst match: how close is it to the most similar page?
    # Computed over EVERY pair, not just the ones over the duplicate threshold.
    # The old version only kept pairs >= 0.30, so on a site where nothing is
    # that close every page's worst match was 0 and the median read 0% - a
    # metric that can never fall and hides the real distribution. The threshold
    # now only decides what counts as a *blocker*, not what gets measured.
    worst: dict[str, float] = {}
    for j, p1, p2 in pairs:
        worst[p1] = max(worst.get(p1, 0), j)
        worst[p2] = max(worst.get(p2, 0), j)

    dup = sorted(
        ((p, j) for p, j in worst.items() if j >= DUPLICATE),
        key=lambda x: -x[1],
    )
    ranked = sorted(worst.items(), key=lambda x: -x[1])
    return {
        "pages_measured": len(texts),
        "pages_with_a_near_duplicate": len(dup),
        "worst_pairs": [{"overlap": round(j, 3), "a": p1, "b": p2} for j, p1, p2 in pairs[:top]],
        "worst_pages": [{"page": p, "closest_overlap": round(j, 3)} for p, j in ranked[:top]],
        "median_overlap": round(
            sorted(worst.values())[len(worst) // 2], 3) if worst else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--live", action="store_true", help="measure the live site, not the build")
    ap.add_argument("--baseline", metavar="REF", default="",
                    help="also measure the built pages at a git ref (e.g. HEAD) for before/after")
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

    if args.baseline:
        base_pages = baseline_pages(args.baseline)
        base = report(base_pages, args.top) if base_pages else None
        if base:
            b, a = base["median_overlap"], data["median_overlap"]
            print(f"vs {args.baseline} (English body only):")
            print(f"  median overlap  {b:.0%} -> {a:.0%}   ({'DOWN' if a < b else 'no change' if a == b else 'UP'})")
            print(f"  worst page      {max(x['closest_overlap'] for x in base['worst_pages']):.0%}"
                  f" -> {max(x['closest_overlap'] for x in data['worst_pages']):.0%}")
            print(f"  near-duplicates {base['pages_with_a_near_duplicate']}"
                  f" -> {data['pages_with_a_near_duplicate']}")
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
