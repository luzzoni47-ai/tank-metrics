#!/usr/bin/env python3
"""Find every public place that writes about "Tank Metrics".

Sir's ask: if anyone writes his brand name anywhere, he should be able to see
the result. This watches the free, no-login corners of the web for the brand and
for close variants, and writes one report.

The hard part is not finding hits, it is telling them apart. A search for
"tankmetrics" returns tankmetrics.com, BattleMetrics and a fuel-logging Chrome
extension - none of them us. A monitor that dumped those in one list would be
worse than useless, because Sir would think a stranger had written about him.
Every hit is therefore labelled:

    OURS     the link is on tankmetrics.in (or www)
    LINKED   another site, but it links to us - a real citation
    NAMESAKE another site that merely shares the words - not about us

Only OURS and LINKED are "someone wrote about us".

Sources, all free and login-free:
  - Hacker News (Algolia API) - developer and startup chatter
  - Bing RSS   - what Bing shows for the phrase
  - Google News RSS - press and blog coverage
  - DuckDuckGo HTML - the long tail Bing misses

Google Search itself is not used: Google blocks scripted queries and the whole
reason this exists is that Sir cannot log in.

Nothing here posts, replies or emails. It reads public pages and writes a file.

    python3 tools/brand_monitor.py             # scan, write the report
    python3 tools/brand_monitor.py --dry-run   # scan, print, write nothing
    python3 tools/brand_monitor.py --all       # list every hit, not just new
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "tools" / "reports"
STATE_FILE = Path("/tmp/tank_metrics_brand_state.json")

HOST = "tankmetrics.in"
UA = "Mozilla/5.0 (compatible; TankMetricsBrandMonitor/1.0; +https://tankmetrics.in)"

# The phrases worth watching. The quoted forms ask the engine for the exact
# phrase; the bare ones catch a casual mention in a sentence.
QUERIES = [
    '"tank metrics"',
    '"tankmetrics"',
    "tankmetrics.in",
]

_KV_TOKEN = os.environ.get("AUTOMATION_KV_TOKEN", "")
_KV_BASE = os.environ.get("AUTOMATION_API_URL", "").rstrip("/")
_STATE_KEY = "brand_monitor_seen"

# Accounts that are ours even though they live on someone else's domain. Listed
# so the report says "this is you" rather than filing Sir's own post as a
# stranger's mention, which would be the opposite of helpful.
OWN_ACCOUNTS = {
    "instagram.com/tankmetrics.in": "our own Instagram account",
}

# Domains that share the words but are somebody else. Kept explicit so the
# report can say "this is not you" instead of leaving Sir to work it out.
KNOWN_NAMESAKES = {
    "tankmetrics.com": "a different site on the .com",
    "battlemetrics.com": "game server stats, not us",
    "chromewebstore.google.com": "a fuel-logging browser extension",
    "chrome-stats.com": "a directory listing of that extension",
}


# --------------------------------------------------------------------------- #
# state
# --------------------------------------------------------------------------- #

def kv_available() -> bool:
    return bool(_KV_TOKEN and _KV_BASE)


def kv_get(key: str):
    if not kv_available():
        return None
    req = urllib.request.Request(
        f"{_KV_BASE}/v1/kv/{key}", headers={"Authorization": f"Bearer {_KV_TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read()).get("value")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def kv_set(key: str, value) -> None:
    if not kv_available():
        return
    req = urllib.request.Request(
        f"{_KV_BASE}/v1/kv/{key}", method="PUT",
        data=json.dumps({"value": value}).encode(),
        headers={"Authorization": f"Bearer {_KV_TOKEN}",
                 "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=20).read()


def load_seen() -> set[str]:
    """URLs already reported. KV in production, a temp file locally."""
    if kv_available():
        return set(kv_get(_STATE_KEY) or [])
    if STATE_FILE.exists():
        try:
            return set(json.loads(STATE_FILE.read_text()))
        except (ValueError, OSError):
            return set()
    return set()


def save_seen(seen: set[str]) -> None:
    if kv_available():
        kv_set(_STATE_KEY, sorted(seen))
        return
    STATE_FILE.write_text(json.dumps(sorted(seen)), encoding="utf-8")


# --------------------------------------------------------------------------- #
# sources
# --------------------------------------------------------------------------- #

def fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def from_hacker_news(query: str) -> list[dict]:
    url = ("https://hn.algolia.com/api/v1/search?hitsPerPage=20&query="
           + urllib.parse.quote(query))
    try:
        data = json.loads(fetch(url))
    except (urllib.error.URLError, ValueError, TimeoutError, OSError):
        return []
    out = []
    for h in data.get("hits", []):
        title = h.get("title") or h.get("story_title") or ""
        link = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        if title:
            out.append({"source": "Hacker News", "title": title,
                        "url": link, "found_by": query})
    return out


def from_rss(name: str, url: str, query: str) -> list[dict]:
    """Bing and Google News both answer in RSS, which needs no key and no login."""
    try:
        xml = fetch(url)
    except (urllib.error.URLError, TimeoutError, OSError):
        return []
    out = []
    for item in re.findall(r"<item>(.*?)</item>", xml, re.S):
        t = re.search(r"<title>(.*?)</title>", item, re.S)
        l = re.search(r"<link>(.*?)</link>", item, re.S)
        if not t or not l:
            continue
        title = strip_tags(t.group(1))
        link = strip_tags(l.group(1))
        if title:
            out.append({"source": name, "title": title, "url": link,
                        "found_by": query})
    return out


def from_duckduckgo(query: str) -> list[dict]:
    """DuckDuckGo lite over POST.

    A GET to the html/lite endpoints answers with an "anomaly" block page, which
    parses to zero results - a silent failure that would make the report claim a
    source was checked when it was not. POST works, so the query travels in the
    body. The lite page marks each result with class="result-link".
    """
    body = urllib.parse.urlencode({"q": query}).encode()
    req = urllib.request.Request(
        "https://lite.duckduckgo.com/lite/", data=body,
        headers={"User-Agent": UA,
                 "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            page = r.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return []
    out = []
    # The lite page writes class='result-link' in SINGLE quotes with href before
    # it. Match the whole anchor, then pull href out, so quote style and
    # attribute order do not matter.
    for m in re.finditer(
            r"<a[^>]*class=['\"]result-link['\"][^>]*>(.*?)</a>", page, re.S):
        tag = m.group(0)
        hm = re.search(r"href=['\"]([^'\"]+)['\"]", tag)
        title = strip_tags(m.group(1))
        if not (hm and title):
            continue
        raw = hm.group(1)
        link = urllib.parse.unquote(
            urllib.parse.parse_qs(urllib.parse.urlparse(raw).query)
            .get("uddg", [raw])[0]) if "uddg=" in raw else raw
        out.append({"source": "DuckDuckGo", "title": title, "url": link,
                    "found_by": query})
    return out


def scan(queries: list[str]) -> list[dict]:
    hits: list[dict] = []
    for q in queries:
        hits += from_hacker_news(q)
        hits += from_rss("Bing", "https://www.bing.com/search?q="
                         + urllib.parse.quote(q) + "&format=rss", q)
        hits += from_rss("Google News", "https://news.google.com/rss/search?q="
                         + urllib.parse.quote(q), q)
        hits += from_duckduckgo(q)
    return hits


# --------------------------------------------------------------------------- #
# classification - the part that makes the report worth reading
# --------------------------------------------------------------------------- #

def domain_of(url: str) -> str:
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def is_ours(url: str) -> bool:
    """Our own site, or an account we run on another platform."""
    d = domain_of(url)
    if d == HOST:
        return True
    path = urllib.parse.urlparse(url).path.strip("/").lower()
    return f"{d}/{path}" in OWN_ACCOUNTS


def classify(hit: dict) -> str:
    """OURS, LINKED, or NAMESAKE.

    LINKED is the interesting middle: a stranger's page that points at us is a
    citation, and that is worth knowing about even though the page is not ours.
    """
    url = hit.get("url", "")
    if is_ours(url):
        return "OURS"
    if domain_of(url) in KNOWN_NAMESAKES:
        return "NAMESAKE"
    # A result that merely mentions the domain in its title or snippet is
    # pointing at us, so treat it as a citation.
    blob = (hit.get("title", "") + " " + url).lower()
    if HOST in blob:
        return "LINKED"
    return "NAMESAKE"


def namesake_note(url: str) -> str:
    d = domain_of(url)
    path = urllib.parse.urlparse(url).path.strip("/").lower()
    return OWN_ACCOUNTS.get(f"{d}/{path}") or KNOWN_NAMESAKES.get(d, "")


def dedupe(hits: list[dict]) -> list[dict]:
    """One row per URL, keeping the first source that found it."""
    seen, out = set(), []
    for h in hits:
        key = h.get("url", "").rstrip("/")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out


def brand_mentioned(hit: dict) -> bool:
    """Only keep hits that really contain the brand, not engine noise.

    A search for "tank metrics" on Bing answers with tankmetrics.com and
    BattleMetrics. Those are genuine namesakes and worth reporting once, but a
    result for, say, "battlemetrics schedule" is just noise.
    """
    blob = (hit.get("title", "") + " " + hit.get("url", "")).lower()
    return bool(re.search(r"tank\s*metrics|tankmetrics", blob))


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #

def render(all_hits: list[dict], new_urls: set[str], show_all: bool) -> str:
    rows = all_hits if show_all else [h for h in all_hits if h["url"] in new_urls]
    lines = [f"# Brand mentions - {date.today().isoformat()}", ""]

    ours = [h for h in rows if h["kind"] == "OURS"]
    linked = [h for h in rows if h["kind"] == "LINKED"]
    names = [h for h in rows if h["kind"] == "NAMESAKE"]

    # Does the site itself surface for its own name? Asked every run, because a
    # brand that does not rank for itself is the thing worth acting on.
    self_hits = self_presence(all_hits)

    lines += [
        f"Sources checked: Hacker News, Bing, Google News, DuckDuckGo.",
        f"Queries: {', '.join(QUERIES)}.",
        "",
        f"- Our own pages or accounts showing: {len(self_hits)}",
        f"- Someone writing about us (our own pages, new): {len(ours)}",
        f"- Someone else linking to us (a real citation): {len(linked)}",
        f"- Namesakes - not us: {len(names)}",
        "",
    ]

    if self_hits:
        lines.append("## Our own pages and accounts in search")
        lines.append("")
        for h in self_hits:
            note = namesake_note(h["url"])
            lines.append(f"- [{h['title']}]({h['url']}) - {h['source']}"
                         + (f" - {note}" if note else ""))
        lines.append("")
    else:
        lines += [
            "## Our own pages and accounts in search",
            "",
            "None of these sources returned a tankmetrics.in page for the brand "
            "queries. Bing and Google News have not surfaced the site for its own "
            "name yet. IndexNow keeps Bing fed; the fix is inbound links and time.",
            "",
        ]

    if not rows:
        lines += ["Nothing new to report since the last run.", ""]
        return "\n".join(lines)

    def block(title: str, items: list[dict]) -> None:
        if not items:
            return
        lines.append(f"## {title}")
        lines.append("")
        for h in items:
            note = namesake_note(h["url"])
            lines.append(f"- [{h['title']}]({h['url']})")
            lines.append(f"  - {h['source']}, found by {h['found_by']}"
                         + (f" - {note}" if note else ""))
        lines.append("")

    block("About us", ours)
    block("Others linking to us", linked)
    block("Namesakes (not us)", names)
    return "\n".join(lines)


def self_presence(hits: list[dict]) -> list[dict]:
    """Every result that is a page of ours, whether or not it is new.

    The question "does my own site show up when someone types my name" deserves
    an answer every run, not only on the run that first found it.
    """
    return [h for h in hits if is_ours(h.get("url", ""))]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="write nothing")
    ap.add_argument("--all", action="store_true", help="list every hit, not only new")
    args = ap.parse_args()

    print(f"queries: {len(QUERIES)}")
    raw = scan(QUERIES)
    hits = [h for h in dedupe(raw) if brand_mentioned(h)]
    for h in hits:
        h["kind"] = classify(h)
    hits.sort(key=lambda h: (h["kind"] != "OURS", h["kind"] != "LINKED", h["url"]))

    print(f"raw results: {len(raw)}  brand-relevant: {len(hits)}")
    for h in hits:
        print(f"  {h['kind']:8} {h['title'][:64]}")

    seen = load_seen()
    new_urls = {h["url"] for h in hits if h["url"] not in seen}
    print(f"new since last run: {len(new_urls)}")

    if args.dry_run:
        return 0

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "brand-latest.md"
    out.write_text(render(hits, new_urls, args.all), encoding="utf-8")
    print(f"report: {out.relative_to(ROOT)}")

    if new_urls:
        save_seen(seen | {h["url"] for h in hits})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
