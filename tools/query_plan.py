#!/usr/bin/env python3
"""Turn Search Console queries into a per-query content plan.

Sir asked, in Hinglish: "top queries kya aa rahi hai, use par kya logon likhna
hai, aur kya training search ho raha hai, use par kya karna hai". This is that
answer, computed from Google's own data instead of guessed.

For every query GSC returns it decides which of four jobs the query needs:

  FIX CTR    - a page already ranks on page 1 (position <= 20) and still gets no
               clicks. The page is fine; the title/description does not match the
               words people typed. Cheapest traffic on the site.
  PUSH       - position 11-30 (page 2-3). Google likes the page but not enough.
               Needs content depth and internal links, not a new page.
  NEW PAGE   - a query with real impressions and no page of ours ranking for it.
               That is a content gap - write the page.
  WATCH      - too few impressions to act on yet. Record, do not spend time.

Reads the cached tools/gsc_inspection.json + a fresh analytics pull. Writes
tools/reports/query-plan.md (for Sir) and tools/query_plan.json (for the daily
run to consume).

    python3 tools/query_plan.py [days]
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import gsc  # noqa: E402

REPORT = ROOT / "tools" / "reports" / "query-plan.md"
OUT = ROOT / "tools" / "query_plan.json"

# Words that carry no topic - stripped before matching a query to a page.
STOP = {
    "a", "an", "the", "in", "of", "for", "to", "and", "or", "is", "are", "what",
    "how", "calculator", "calculate", "free", "online", "india", "indian", "ka",
    "ki", "kitna", "kitne", "hoga", "hota", "hai", "me", "mein", "vs", "with",
}


def tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9\u0900-\u097f]+", text.lower())
    return {w for w in words if w not in STOP and len(w) > 1}


def fetch(days: int) -> tuple[list[dict], list[dict]]:
    token = gsc.access_token_oauth()
    site = gsc.resolve_site(token)
    end = time.strftime("%Y-%m-%d")
    start = time.strftime("%Y-%m-%d", time.localtime(time.time() - days * 86400))

    def q(dim: str) -> list[dict]:
        payload = {
            "startDate": start,
            "endDate": end,
            "dimensions": [dim],
            "rowLimit": 500,
        }
        data = gsc.call(
            f"{gsc.API}/sites/{urllib.parse.quote(site, safe='')}/searchAnalytics/query",
            token,
            method="POST",
            payload=payload,
        )
        return data.get("rows", [])

    return q("query"), q("page")


def page_titles() -> dict[str, str]:
    """clean URL -> <title>, read from the built site via url-map.

    GSC reports pages by their public clean URL (/epf-calculator); the files on
    disk are /site/tools/epf-calculator.html. tools/url-map.json is the bridge -
    without it every query matched no page and the whole plan read "write a new
    page".
    """
    out: dict[str, str] = {}
    um = json.loads((ROOT / "tools" / "url-map.json").read_text(encoding="utf-8"))
    for clean, rel in um.items():
        f = ROOT / "public" / rel.lstrip("/")
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"<title>([^<]*)</title>", text)
        out[clean] = m.group(1) if m else ""
    return out


def classify(queries: list[dict], pages: list[dict]) -> dict[str, list[dict]]:
    titles = page_titles()
    buckets: dict[str, list[dict]] = {"FIX CTR": [], "PUSH": [], "NEW PAGE": [], "WATCH": []}
    page_tokens = {p["keys"][0]: tokens(titles.get(p["keys"][0].replace("https://tankmetrics.in", ""), ""))
                   for p in pages}

    for r in queries:
        q = r["keys"][0]
        pos, imp, clicks = r["position"], r["impressions"], r["clicks"]
        qt = tokens(q)

        # A page matches the query only when it shares most of the query's topic
        # words. A flat 0.4 was too loose: "home appraisal calculator" shares
        # "home" with /salary-take-home-estimator (0.5) and was reported as a
        # CTR fix on the wrong page. Short queries need a tighter bar because a
        # single shared word is a large fraction of them.
        need = 0.6 if len(qt) <= 3 else 0.4
        best = None
        best_overlap = 0.0
        for p in pages:
            pt = page_tokens.get(p["keys"][0], set())
            if not pt or not qt:
                continue
            overlap = len(qt & pt) / len(qt)
            if overlap > best_overlap:
                best_overlap, best = overlap, p

        rec = {"query": q, "position": round(pos, 1), "impressions": imp, "clicks": clicks}
        if best and best_overlap >= need:
            rec["page"] = best["keys"][0].replace("https://tankmetrics.in", "")
            rec["page_position"] = round(best["position"], 1)

        if pos <= 20 and clicks == 0 and imp >= 3 and best_overlap >= need:
            rec["action"] = "Rewrite the title and meta description to use these exact words"
            buckets["FIX CTR"].append(rec)
        elif 20 < pos <= 30 and imp >= 2:
            rec["action"] = "Add depth (FAQ, worked example, comparison) and an internal link from a stronger page"
            buckets["PUSH"].append(rec)
        elif best_overlap < 0.4 and imp >= 3:
            rec["action"] = "No page covers this - write it, with the query in the H1"
            buckets["NEW PAGE"].append(rec)
        else:
            rec["action"] = "Too few impressions to act on - keep watching"
            buckets["WATCH"].append(rec)

    for k in buckets:
        buckets[k].sort(key=lambda r: (-r["impressions"], r["position"]))
    return buckets


def write_report(buckets: dict[str, list[dict]], days: int) -> None:
    lines = [f"# Query plan - last {days} days", "",
             "Generated by `tools/query_plan.py` from Search Console. Nothing here is guessed.",
             ""]
    heads = {
        "FIX CTR": "Fix CTR - already on page 1, earning nothing (do these first)",
        "NEW PAGE": "Content gaps - people search this, we have no page",
        "PUSH": "Striking distance - page 2-3, needs depth",
        "WATCH": "Watch list - too little data yet",
    }
    for key in ("FIX CTR", "NEW PAGE", "PUSH", "WATCH"):
        rows = buckets[key]
        lines += [f"## {heads[key]}", ""]
        if not rows:
            lines += ["_None._", ""]
            continue
        lines += ["| Query | Pos | Impr | Clicks | Page | Action |",
                  "|---|---|---|---|---|---|"]
        for r in rows[:40]:
            lines.append(
                f"| {r['query']} | {r['position']} | {r['impressions']} | "
                f"{r['clicks']} | `{r.get('page', '-')}` | {r['action']} |"
            )
        lines.append("")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 28
    queries, pages = fetch(days)
    buckets = classify(queries, pages)
    OUT.write_text(json.dumps(buckets, indent=1, ensure_ascii=False), encoding="utf-8")
    write_report(buckets, days)
    for k, v in buckets.items():
        print(f"{k:<10} {len(v)}")
    print(f"\nwrote {REPORT.relative_to(ROOT)} and {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
