#!/usr/bin/env python3
"""Find what people actually search for, so the daily runs pick real topics.

Sir cannot log into Search Console (the account is behind an MFA loop he cannot
clear), so the site has no query report to work from. Google's autocomplete
endpoint is the closest public substitute: it returns the phrases real users
type, ranked by how often they are typed, and it is free and needs no key.

This asks autocomplete a set of seed phrases that match the site's own subject
matter, plus the titles of the calculators and guides already published, then
scores every suggestion:

  * demand    - how many of the seeds returned it, and how early in the list
  * gap       - a phrase the site has no page for scores higher than one it
                already covers, because the point is to find the next page
  * fit       - phrases in the site's own lane (Indian money, business, tax)
                rank above a stray celebrity query autocomplete likes to mix in

The result is written to `tools/keywords.json`. The daily guide and news runs
read that file and pick from the top of the list instead of guessing, which is
the whole point: a topic chosen from real query data is a topic with traffic
behind it.

Usage:
    python3 tools/keyword_radar.py              # refresh tools/keywords.json
    python3 tools/keyword_radar.py --top 25     # print the ranked list
    python3 tools/keyword_radar.py --offline    # skip the network, use seeds only
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
SITE = ROOT.parent / "public" / "site"
OUT = ROOT / "keywords.json"

SUGGEST = "http://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl=in&q="

# Seeds in the site's own lane. Broad enough to reach the long tail, specific
# enough that autocomplete stays on money and business rather than drifting to
# whatever is trending.
SEEDS = [
    "gst calculator", "loan emi calculator", "income tax calculator",
    "sip calculator", "break even point", "ebitda", "ltv cac ratio",
    "burn rate", "runway", "gross margin", "net profit margin",
    "markup vs margin", "roi calculator", "cagr calculator",
    "savings goal", "fd calculator", "ppf calculator", "nps calculator",
    "hra exemption", "gratuity calculator", "startup valuation",
    "pre money post money", "dilution calculator", "cap table",
    "revenue multiple", "ebitda multiple", "customer acquisition cost",
    "average order value", "churn rate", "working capital",
    "cash conversion cycle", "stamp duty", "rental yield",
    "property valuation", "distributor margin", "landed cost",
    "marketplace fees", "cod rto", "freelancer hourly rate",
    "franchise roi", "tam sam som", "roas calculator", "cpm to cpc",
    "employee utilisation", "salary take home", "small business tax india",
    "msme loan", "working capital loan", "shop profit margin",
]

# Phrases that mark a suggestion as being in the site's lane.
LANE = (
    "calculator", "calculate", "formula", "margin", "profit", "gst", "tax",
    "emi", "loan", "interest", "valuation", "startup", "business", "revenue",
    "cost", "price", "rate", "roi", "cagr", "sip", "fd", "ppf", "nps",
    "salary", "churn", "cac", "ltv", "ebitda", "runway", "burn", "break even",
    "dilution", "equity", "yield", "rental", "property", "msme", "inventory",
    "cash flow", "working capital", "marketplace", "seller", "msme",
    "money", "income", "saving", "investment", "share market", "mutual fund",
    "india", "small business", "shop", "shopkeeper", "dukan", "dukaan",
)

# Autocomplete mixes in noise: song lyrics, sports, film names, and brands.
# Drop anything that carries one of these unless it also carries a lane word.
NOISE = (
    "song", "lyrics", "movie", "film", "actor", "actress", "cricket",
    "match", "ipl", "game", "download", "apk", "whatsapp", "status",
    "video", "youtube", "instagram", "tiktok", "recipe", "hotel", "flight",
    "train", "job vacancy", "govt job", "result", "admit card", "lottery",
    # Brands and companies autocomplete offers when a seed looks like a name.
    "sebby", "zoho", "jollibee", "blinkit", "swiggy", "zomato", "paytm",
    "groww", "zerodha", "upstox", "angel one", "phonepe", "razorpay",
    "shopify", "amazon", "flipkart", "meesho", "nykaa", "cred",
    # "runway" is also an AI company, and "exit velocity" is a baseball stat.
    "runway ml", "runway ai", "runway gen", "exit velocity",
    # A US state that matches "india" as a substring, plus the usual others.
    "indiana", "california", "texas", "florida", "new york", "canada",
    "australia", "uk", "usa", "irs", "401k", "dollar",
    # Words autocomplete attaches to our seeds but that mean something else.
    "pupil", "coca", "cola", "pepsi", "nike", "adidas", "netflix",
)


def suggest(seed: str, timeout: float = 8.0) -> list[str]:
    url = SUGGEST + urllib.parse.quote(seed)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        payload = json.loads(r.read().decode("utf-8", "replace"))
    return [str(x).strip().lower() for x in (payload[1] if len(payload) > 1 else [])]


def normalise(text: str) -> str:
    t = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    t = re.sub(r"\s+", " ", t).strip()
    # Fold the -ise/-ize and -isation/-ization pairs. Indian English uses the
    # "s" spelling ("utilisation") while the site's own copy uses the "z" one,
    # so without this the radar reports a covered topic as an open gap.
    return re.sub(r"i[sz]ation\b", "isation", t).replace("ize", "ise").replace("izing", "ising")


def published_pages() -> set[str]:
    """Normalised titles and slugs of everything already on the site."""
    seen = set()
    for path in list(SITE.glob("*.html")) + list((SITE / "tools").glob("*.html")):
        text = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"<title>(.*?)</title>", text, re.S)
        if m:
            seen.add(normalise(m.group(1).split("|")[0]))
        seen.add(normalise(path.stem.replace("-", " ")))
    return seen


# Words that carry no topic on their own. A query is judged on what is left
# after these are removed: "cagr calculator" is the same topic as "cagr", and
# "ebitda means" is the same topic as "ebitda".
GENERIC = {
    "calculator", "calculate", "calculation", "formula", "online", "app",
    "india", "indian", "in", "of", "the", "how", "to", "what", "is", "are",
    "rate", "rates", "means", "meaning", "definition", "define", "example",
    "examples", "explained", "explain", "guide", "full", "form", "best",
    "top", "list", "free", "use", "used", "uses", "work", "works", "working",
    "and", "for", "with", "vs", "or", "a", "an", "on", "at", "my", "your",
}


def covered(query: str, pages: set[str]) -> bool:
    """True when the site already has a page that answers this query.

    Judged on the topic words only, so "cagr calculator" is seen as covered by
    the CAGR tool. A query that adds a real qualifier the site has no page for
    ("fd calculator sbi", "msme loan interest rate") stays uncovered, which is
    what the daily runs should be looking at.
    """
    q = normalise(query)
    if not q:
        return False
    for page in pages:
        if q in page or page in q:
            return True
    core = [w for w in q.split() if w not in GENERIC and len(w) > 1]
    if not core:
        return False
    return all(any(w in page for page in pages) for w in core)


# Match on word boundaries, not substrings: "indiana" must not match the lane
# word "india", and "apps" must not match "app".
LANE_RE = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in LANE) + r")\b")
NOISE_RE = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in NOISE) + r")\b")


def in_lane(query: str) -> bool:
    return bool(LANE_RE.search(query))


def noisy(query: str) -> bool:
    """A noise word disqualifies the phrase even when a lane word is present.

    Autocomplete happily returns "ask sebby calculator" and "jollibee franchise
    roi": both carry a lane word, so an "and not in_lane" test let them through
    and they crowded the top of the list. Word-boundary matching is what makes
    this safe to apply unconditionally - "indiana" no longer matches "india".
    """
    return bool(NOISE_RE.search(query))


def collect(offline: bool = False) -> dict:
    pages = published_pages()
    scores: dict[str, dict] = {}
    seeds = list(SEEDS)
    for path in sorted((SITE / "tools").glob("*.html")):
        seeds.append(path.stem.replace("-", " "))

    if offline:
        for s in seeds:
            scores.setdefault(normalise(s), {"seeds": [], "rank": 0})
        suggestions = {}
    else:
        suggestions = {}
        for i, seed in enumerate(seeds):
            try:
                suggestions[seed] = suggest(seed)
            except (urllib.error.URLError, TimeoutError, OSError, ValueError):
                continue
            # Be a polite client: this is a public endpoint and we are not in a
            # hurry. 40 seeds with a small gap is well inside normal use.
            if i % 5 == 4:
                time.sleep(0.4)

    for seed, items in suggestions.items():
        for rank, q in enumerate(items):
            if len(q) < 4 or noisy(q):
                continue
            rec = scores.setdefault(q, {"seeds": [], "rank": 0})
            if seed not in rec["seeds"]:
                rec["seeds"].append(seed)
            # Earlier in the list means typed more often.
            rec["rank"] = max(rec["rank"], max(1, 10 - rank))

    ranked = []
    for q, rec in scores.items():
        if not in_lane(q):
            continue
        demand = len(rec["seeds"]) * 3 + rec["rank"]
        gap = 1.6 if not covered(q, pages) else 0.6
        length = 1.15 if 2 <= len(q.split()) <= 5 else 0.9
        ranked.append({
            "query": q,
            "demand": demand,
            "covered": covered(q, pages),
            "score": round(demand * gap * length, 2),
            "from": rec["seeds"][:4],
        })

    ranked.sort(key=lambda x: (-x["score"], x["query"]))
    # Keep the file small enough to sit in git without noise; the daily runs
    # only ever read the top of the list.
    ranked = ranked[:400]
    return {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "seed_count": len(seeds),
        "suggestion_count": len(scores),
        "keywords": ranked,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=0, help="print the top N and exit")
    ap.add_argument("--offline", action="store_true", help="no network calls")
    args = ap.parse_args()

    data = collect(offline=args.offline)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    print(f"keywords.json: {len(data['keywords'])} ranked phrases "
          f"from {data['seed_count']} seeds")

    top = data["keywords"][: args.top or 15]
    for i, k in enumerate(top, 1):
        mark = " " if k["covered"] else "+"
        print(f"{mark} {i:2d}. {k['score']:6.1f}  {k['query']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
