#!/usr/bin/env python3
"""Say, page by page, why Google has not indexed it - and what to do.

Search Console shows "59 not indexed" as a number. This turns it into a list:
every sitemap URL, its exact coverage state, its last crawl, its near-duplicate
overlap, and the one action that fixes that specific state. Run it after a
`gsc.py` inspection; it caches the inspection so repeat runs are fast.

The four states and what each means:

  PASS                              indexed - nothing to do.
  URL is unknown to Google          never seen. New, or orphaned (no internal
                                    link from an indexed page). Fix: link to it.
  Discovered - currently not indexed
                                    known but not crawled. Google spent its
                                    crawl budget on the near-duplicate cluster.
                                    Fix: unique copy + internal links.
  Crawled - currently not indexed   crawled and rejected as low value. The
                                    near-duplicate verdict. Fix: dedup rewrite.

Also flags pages whose user canonical disagrees with Google's, which is a
separate fault with a separate fix.

    python3 tools/gsc_triage.py                 # use the cache, refresh if stale
    python3 tools/gsc_triage.py --refresh       # re-inspect every URL now (slow)
    python3 tools/gsc_triage.py --bucket crawled
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
PUBLIC = ROOT / "public"
CACHE = TOOLS / "gsc_inspection.json"
OUT = TOOLS / "gsc_triage.json"
STALE_DAYS = 7


def load_gsc():
    spec = importlib.util.spec_from_file_location("gsc", TOOLS / "gsc.py")
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    return g


def sitemap_urls() -> list[str]:
    xml = (PUBLIC / "sitemap.xml").read_text(encoding="utf-8")
    return [u.strip() for u in re.findall(r"<loc>\s*(.*?)\s*</loc>", xml)]


def refresh() -> list[dict]:
    g = load_gsc()
    tok = g.access_token_oauth()
    site = g.resolve_site(tok)
    urls = sitemap_urls()
    print(f"inspecting {len(urls)} URLs (this takes ~25 min) ...", file=sys.stderr)
    out = []
    for i, u in enumerate(urls, 1):
        try:
            d = g.call(g.INSPECT_API, tok, method="POST",
                       payload={"inspectionUrl": u, "siteUrl": site})
            r = d.get("inspectionResult", {}).get("indexStatusResult", {})
            out.append({
                "url": u, "verdict": r.get("verdict"),
                "coverage": r.get("coverageState"),
                "crawl": r.get("lastCrawlTime"),
                "gcanon": r.get("googleCanonical"),
                "ucanon": r.get("userCanonical"),
            })
        except SystemExit as e:
            out.append({"url": u, "verdict": "ERR", "coverage": str(e)[:120]})
        if i % 20 == 0:
            print(f"  {i}/{len(urls)}", file=sys.stderr)
            CACHE.write_text(json.dumps(out, indent=1), encoding="utf-8")
    CACHE.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def cached_or_refresh(force: bool) -> list[dict]:
    if not force and CACHE.exists():
        age = (time.time() - CACHE.stat().st_mtime) / 86400
        if age <= STALE_DAYS:
            return json.loads(CACHE.read_text(encoding="utf-8"))
    return refresh()


# State -> (bucket key, plain-English cause, the one action that fixes it).
BUCKETS = {
    "Submitted and indexed": ("indexed", "Indexed.", None),
    "URL is unknown to Google": (
        "not-seen",
        "Google has never seen this URL - it is new, or nothing indexed links to it.",
        "Add 2-3 internal links from already-indexed pages, re-submit the sitemap, "
        "and Request Indexing for it in the GSC UI."),
    "Discovered - currently not indexed": (
        "discovered",
        "Google knows the URL but has not crawled it - crawl budget is going to "
        "the near-duplicate cluster instead.",
        "Give the page unique per-tool copy, link it from indexed pages, then "
        "re-submit the sitemap."),
    "Crawled - currently not indexed": (
        "crawled",
        "Google crawled it and chose not to index it - the near-duplicate verdict.",
        "Rewrite with unique copy (the dedup worklist) and link it from indexed "
        "pages; then Request Indexing."),
    "Duplicate, Google chose different canonical than user": (
        "canonical",
        "Google picked a different canonical - two URLs are serving the same page.",
        "Point one URL at the other with a canonical, and remove the duplicate "
        "from the sitemap."),
    "Duplicate without user-selected canonical": (
        "canonical",
        "A duplicate with no canonical declared.",
        "Add a canonical to this page."),
    "Alternate page with proper canonical tag": (
        "canonical", "A duplicate that correctly points at its canonical.",
        "No action - this is the intended behaviour."),
}


def load_url_map() -> dict:
    p = TOOLS / "url-map.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def page_type(url: str, url_map: dict) -> str:
    """What kind of page this is, from url-map (the source of truth)."""
    u = url.replace("https://tankmetrics.in", "") or "/"
    built = url_map.get(u, "")
    if u.startswith("/keyword-"):
        return "keyword"
    if built.startswith("/site/tools/"):
        return "calculator"
    if built.startswith("/site/news-"):
        return "news"
    if built.startswith("/site/blog-"):
        return "guide"
    return "static"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-inspect every URL now")
    ap.add_argument("--bucket", default="", help="show only this bucket")
    args = ap.parse_args()

    rows = cached_or_refresh(args.refresh)
    url_map = load_url_map()
    overlap = {}
    cu = TOOLS / "content_uniqueness.json"
    if cu.exists():
        for r in json.loads(cu.read_text(encoding="utf-8")).get("worst_pages", []):
            overlap[r["page"].rstrip("/").rsplit("/", 1)[-1]] = r["closest_overlap"]

    triaged = []
    for r in rows:
        cov = r.get("coverage") or "?"
        key, cause, action = BUCKETS.get(cov, ("other", f"Unexpected state: {cov}", "Inspect manually."))
        slug = r["url"].replace("https://tankmetrics.in", "").strip("/") or "/"
        triaged.append({
            "url": r["url"], "slug": "/" + slug, "type": page_type(r["url"], url_map),
            "bucket": key, "coverage": cov, "cause": cause, "action": action,
            "last_crawl": r.get("crawl"),
            "overlap": overlap.get(slug),
            "canonical_ok": r.get("gcanon") in (None, r["url"]) or r.get("gcanon") == r.get("ucanon"),
        })

    counts = collections.Counter(t["bucket"] for t in triaged)
    print(f"triaged {len(triaged)} URLs (inspection cache: {CACHE.name})")
    print()
    for k, n in counts.most_common():
        print(f"  {n:>4}  {k}")
    print()
    order = ["crawled", "discovered", "not-seen", "canonical", "other"]
    for bucket in order:
        items = [t for t in triaged if t["bucket"] == bucket]
        if not items or (args.bucket and args.bucket != bucket):
            continue
        sample = BUCKETS.get(next((c for c, v in BUCKETS.items() if v[0] == bucket), ""), None)
        print(f"===== {bucket} ({len(items)}) =====")
        if sample:
            print(f"  cause : {sample[1]}")
            print(f"  fix   : {sample[2]}")
        for t in items[:25]:
            ov = f"  dup {t['overlap']:.0%}" if t["overlap"] else ""
            print(f"    {t['slug']:<52} {t['type']:<10}{ov}")
        if len(items) > 25:
            print(f"    ... and {len(items) - 25} more")
        print()

    OUT.write_text(json.dumps({"counts": dict(counts), "pages": triaged},
                              indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
