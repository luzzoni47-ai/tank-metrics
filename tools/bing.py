#!/usr/bin/env python3
"""Bing Webmaster API — verify, submit, and read back what Bing actually serves.

Why this exists next to the IndexNow sweep: IndexNow announces a URL, but it
does not tell you whether Bing indexed it, and it has no query data at all. The
Bing Webmaster API does, and Bing is the index behind DuckDuckGo, Yahoo, Ecosia,
Qwant, Swisscows, Copilot and ChatGPT search — so this is the only search
channel where an agent can both push and read without a Google login.

The API allows **100 submitted URLs per day**, per account. That is why state is
kept on disk: a 176-page sitemap takes two days, and without the record the
second run would re-spend the quota on the first 100 pages and the tail would
never be announced.

The key is read from `BING_API_KEY` and never written to a file, because this
repository is public.

    export BING_API_KEY="..."
    python3 tools/bing.py sites
    python3 tools/bing.py quota
    python3 tools/bing.py feed             # hand Bing the sitemap (no quota cost)
    python3 tools/bing.py submit           # up to 100 fresh URLs
    python3 tools/bing.py indexnow         # all fresh URLs, no 100/day cap
    python3 tools/bing.py submit --dry-run
    python3 tools/bing.py stats 28         # top queries, last 28 days
    python3 tools/bing.py pages 28         # per-page impressions and clicks
    python3 tools/bing.py crawl            # what Bing's crawler has been doing
    python3 tools/bing.py issues           # crawl errors Bing found
    python3 tools/bing.py url <url>        # is this URL indexed, and when crawled
    python3 tools/bing.py keywords "gst calculator"   # Bing's own search volume
    python3 tools/bing.py links            # inbound link counts
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "tankmetrics.in"
SITE = f"https://{HOST}/"
SITEMAP = ROOT / "public" / "sitemap.xml"
STATE = ROOT / ".openhands" / "bing_submitted.json"
API = "https://ssl.bing.com/webmaster/api.svc/json"
UA = "TankMetrics-Bing/1.0 (+https://tankmetrics.in)"

# Re-announce a page after this many days even if nothing changed, so a page
# that Bing dropped gets another chance without re-spending quota every run.
RESUBMIT_DAYS = 30
DAILY_QUOTA = 100

DRY = "--dry-run" in sys.argv

_KV_TOKEN = os.environ.get("AUTOMATION_KV_TOKEN", "")
_KV_BASE = os.environ.get("AUTOMATION_API_URL", "").rstrip("/")
_STATE_KEY = "bing_submitted"


def kv_available() -> bool:
    return bool(_KV_TOKEN and _KV_BASE)


def kv_get():
    req = urllib.request.Request(
        f"{_KV_BASE}/v1/kv/{_STATE_KEY}",
        headers={"Authorization": f"Bearer {_KV_TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())["value"]
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def kv_set(value) -> None:
    req = urllib.request.Request(
        f"{_KV_BASE}/v1/kv/{_STATE_KEY}",
        data=json.dumps(value).encode(),
        headers={"Authorization": f"Bearer {_KV_TOKEN}",
                 "Content-Type": "application/json"},
        method="PUT")
    with urllib.request.urlopen(req, timeout=20) as r:
        r.read()


def key() -> str:
    k = os.environ.get("BING_API_KEY", "").strip()
    if not k:
        sys.exit("Set BING_API_KEY first (Bing Webmaster Tools -> Settings -> API Access).")
    return k


def call(method: str, *, params: dict | None = None, body: dict | None = None):
    url = f"{API}/{method}?apikey={key()}"
    for k, v in (params or {}).items():
        url += f"&{k}={urllib.parse.quote(str(v))}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read().decode("utf-8", "replace")
    return json.loads(raw).get("d") if raw.strip() else None


def sitemap_urls() -> list[str]:
    return re.findall(r"<loc>([^<]+)</loc>", SITEMAP.read_text(encoding="utf-8"))


def load_state() -> dict:
    """Read the submitted-URL record.

    The automation runs in a fresh container, so the local file would be lost
    between runs and the quota would be re-spent on the same first 100 URLs
    every day - the tail of the sitemap would never be announced. The KV store
    is the real home; the file is only the local-development fallback, the same
    arrangement `tools/automation/index_submit/main.py` uses.
    """
    if kv_available():
        try:
            return kv_get() or {}
        except Exception as e:
            print(f"  KV read failed, using local file: {e}")
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(st: dict) -> None:
    if kv_available():
        try:
            kv_set(st)
            return
        except Exception as e:
            print(f"  KV write failed, using local file: {e}")
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=2, sort_keys=True), encoding="utf-8")


def cmd_sites() -> None:
    sites = call("GetUserSites") or []
    if not sites:
        sys.exit("No sites on this account — add and verify the site first.")
    for s in sites:
        mark = "verified" if s.get("IsVerified") else "NOT VERIFIED"
        print(f"  {s.get('Url')}  [{mark}]")


def cmd_quota() -> None:
    q = call("GetUrlSubmissionQuota", params={"siteUrl": SITE})
    if q is None:
        print("  quota: (no answer)")
        return
    print(f"  daily quota: {q.get('DailyQuota')}  used: {q.get('MonthlyQuota')}")


def cmd_submit() -> None:
    st = load_state()
    today = date.today().isoformat()
    cutoff = (date.today() - timedelta(days=RESUBMIT_DAYS)).isoformat()

    urls = sitemap_urls()
    # `/` first: it is the page that carries the brand and the internal links,
    # so it is the one worth spending the first slot of the quota on.
    urls.sort(key=lambda u: (u.rstrip("/") != SITE.rstrip("/"), u))

    fresh = [u for u in urls if st.get(u, "") < cutoff]
    todo = fresh[:DAILY_QUOTA]

    print(f"  sitemap: {len(urls)} urls | never/old: {len(fresh)} | sending: {len(todo)}")
    if not todo:
        print("  nothing to submit")
        return
    if DRY:
        for u in todo[:5]:
            print(f"    would submit {u}")
        print(f"    ...and {max(0, len(todo) - 5)} more")
        return

    try:
        call("SubmitUrlbatch", body={"siteUrl": SITE, "urlList": todo})
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        # A spent quota is a normal end to the day, not a failure: the record is
        # deliberately left untouched so tomorrow's run starts where this one
        # stopped instead of re-spending the quota on the same URLs.
        if "quota" in detail.lower():
            print(f"  daily quota is spent - {len(todo)} url(s) stay queued for tomorrow")
            return
        sys.exit(f"  submit failed: HTTP {e.code} {detail}")

    for u in todo:
        st[u] = today
    save_state(st)
    print(f"  submitted {len(todo)} urls; {len(urls) - len(todo) - (len(urls) - len(fresh))} left for tomorrow")


def _window(days: int) -> tuple[str, str]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def cmd_stats(days: int = 28) -> None:
    a, b = _window(days)
    rows = call("GetQueryStats", params={"siteUrl": SITE, "startDate": a, "endDate": b}) or []
    if not rows:
        print(f"  no query data for the last {days} days yet")
        return
    rows.sort(key=lambda r: -(r.get("Impressions") or 0))
    print(f"  {'query':<42} {'imp':>7} {'clicks':>7} {'pos':>6}")
    for r in rows[:25]:
        q = (r.get("Query") or "")[:41]
        print(f"  {q:<42} {r.get('Impressions', 0):>7} {r.get('Clicks', 0):>7} "
              f"{round(r.get('AvgImpressionPosition') or 0, 1):>6}")


def cmd_pages(days: int = 28) -> None:
    a, b = _window(days)
    rows = call("GetPageStats", params={"siteUrl": SITE, "startDate": a, "endDate": b}) or []
    if not rows:
        print(f"  no page data for the last {days} days yet")
        return
    rows.sort(key=lambda r: -(r.get("Impressions") or 0))
    print(f"  {'page':<58} {'imp':>7} {'clicks':>7}")
    for r in rows[:30]:
        p = (r.get("Query") or r.get("Page") or "")[:57]
        print(f"  {p:<58} {r.get('Impressions', 0):>7} {r.get('Clicks', 0):>7}")


def _ms_date(v) -> str:
    """Bing returns dates as `/Date(ms)/`; a negative epoch means "never"."""
    m = re.search(r"\((-?\d+)", str(v or ""))
    if not m:
        return "?"
    ms = int(m.group(1))
    if ms < 0:
        return "never"
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d")


def cmd_feed() -> None:
    """Register the sitemap so Bing crawls it on its own.

    This costs no quota, unlike SubmitUrl, so it is the first thing to do and the
    thing to redo after a big rebuild. The site must be verified for Bing to
    accept it.
    """
    if DRY:
        print(f"  would submit feed {SITE}sitemap.xml")
        return
    call("SubmitFeed", body={"siteUrl": SITE, "feedUrl": f"{SITE}sitemap.xml"})
    print(f"  submitted {SITE}sitemap.xml")
    for f in call("GetFeeds", params={"siteUrl": SITE}) or []:
        print(f"    {f.get('Url')}  [{f.get('Status')}]  submitted {_ms_date(f.get('Submitted'))}")


def cmd_crawl() -> None:
    rows = call("GetCrawlStats", params={"siteUrl": SITE}) or []
    if not rows:
        print("  Bing has not crawled the site yet")
        return
    print(f"  {'date':<12} {'crawled':>8} {'errors':>7} {'in index':>9}")
    for r in rows[-14:]:
        print(f"  {_ms_date(r.get('Date')):<12} {r.get('CrawledPages', 0):>8} "
              f"{r.get('CrawlErrors', 0):>7} {r.get('InIndex', 0):>9}")


def cmd_issues() -> None:
    rows = call("GetCrawlIssues", params={"siteUrl": SITE}) or []
    if not rows:
        print("  no crawl issues")
        return
    print(f"  {'url':<56} {'code':>5}  issue")
    for r in rows[:40]:
        print(f"  {(r.get('Url') or '')[:55]:<56} {r.get('HttpCode', 0):>5}  "
              f"{r.get('IssueType', '')}")


def cmd_url(url: str) -> None:
    """The indexing verdict for one page - the closest thing to Inspect URL here."""
    info = call("GetUrlInfo", params={"siteUrl": SITE, "url": url}) or {}
    traffic = call("GetUrlTrafficInfo", params={"siteUrl": SITE, "url": url}) or {}
    print(f"  url:        {info.get('Url', url)}")
    print(f"  http:       {info.get('HttpStatus', 0)}")
    print(f"  discovered: {_ms_date(info.get('DiscoveryDate'))}")
    print(f"  crawled:    {_ms_date(info.get('LastCrawledDate'))}")
    print(f"  anchors:    {info.get('AnchorCount', 0)}")
    print(f"  impressions:{traffic.get('Impressions', 0)}  clicks: {traffic.get('Clicks', 0)}")


def cmd_keywords(query: str) -> None:
    """Bing's own impression estimate for a query - no login, no AdWords.

    Only the `Query` variant needs no paid tier; `GetRelatedKeywords` answers
    empty on a standard account.
    """
    rows = call("GetKeywordStats", params={"siteUrl": SITE, "q": query}) or []
    if not rows:
        print(f"  no data for {query!r}")
        return
    last = rows[-1]
    print(f"  {query!r}: {last.get('Impressions', 0)} impressions, "
          f"{last.get('BroadImpressions', 0)} broad (week of {_ms_date(last.get('Date'))})")
    print(f"  ({len(rows)} weeks of history)")


def cmd_links() -> None:
    d = call("GetLinkCounts", params={"siteUrl": SITE}) or {}
    links = d.get("Links") or []
    print(f"  pages with inbound links: {d.get('TotalPages', 0)}")
    for l in links[:20]:
        print(f"    {l.get('Url')}: {l.get('Count', 0)}")


INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
INDEXNOW_KEY = "91ac4c920695a74eec34342ceb18acbf"


def cmd_indexnow() -> None:
    """Push every fresh URL through IndexNow, which has no 100/day cap.

    This is the escape hatch from the SubmitUrl quota: IndexNow reaches Bing,
    Yandex, Seznam and Naver in one POST and answers 200/202 on acceptance, so a
    176-URL sitemap clears in a single call instead of two days. It shares the
    same submitted-URL record as `submit`, so the two never fight: whichever runs
    first marks the URL, and the other then sees nothing to do.
    """
    st = load_state()
    cutoff = (date.today() - timedelta(days=RESUBMIT_DAYS)).isoformat()
    urls = sitemap_urls()
    todo = [u for u in urls if st.get(u, "") < cutoff]

    print(f"  sitemap: {len(urls)} urls | never/old: {len(todo)}")
    if not todo:
        print("  nothing to submit")
        return
    if DRY:
        print(f"    would send {len(todo)} urls to IndexNow")
        return

    body = {"host": HOST, "key": INDEXNOW_KEY,
            "keyLocation": f"https://{HOST}/{INDEXNOW_KEY}.txt", "urlList": todo}
    req = urllib.request.Request(
        INDEXNOW_ENDPOINT, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        sys.exit(f"  IndexNow failed: HTTP {e.code} {e.read().decode()[:200]}")

    today = date.today().isoformat()
    for u in todo:
        st[u] = today
    save_state(st)
    print(f"  IndexNow accepted {len(todo)} url(s) (HTTP {code})")


def cmd_blocked() -> None:
    rows = call("GetBlockedUrls", params={"siteUrl": SITE}) or []
    if not rows:
        print("  nothing blocked from Bing")
        return
    for r in rows[:40]:
        print(f"    {r.get('Url') if isinstance(r, dict) else r}")


def cmd_report() -> None:
    """The whole Bing picture in one call - what the daily run prints.

    Order matters: the crawler state explains why the query tables are empty, so
    printing "no impressions" without "Bing has not crawled yet" would read as a
    problem when it is only a new property warming up.
    """
    print("-- verification")
    for s in call("GetUserSites") or []:
        print(f"  {s.get('Url')}  [{'verified' if s.get('IsVerified') else 'NOT VERIFIED'}]")

    print("-- crawler")
    cmd_crawl()

    print("-- sitemap feeds")
    feeds = call("GetFeeds", params={"siteUrl": SITE}) or []
    if not feeds:
        print("  no feed registered - run `bing.py feed`")
    for f in feeds:
        print(f"  {f.get('Url')}  [{f.get('Status')}]  submitted {_ms_date(f.get('Submitted'))}")

    print("-- index")
    a, b = _window(28)
    rows = call("GetPageStats", params={"siteUrl": SITE, "startDate": a, "endDate": b}) or []
    print(f"  pages with impressions (28d): {len(rows)}")
    rows.sort(key=lambda r: -(r.get("Impressions") or 0))
    for r in rows[:10]:
        print(f"    {(r.get('Query') or '')[:50]:<52} {r.get('Impressions', 0):>6} imp "
              f"{r.get('Clicks', 0):>4} clicks")

    print("-- crawl issues")
    cmd_issues()

    print("-- inbound links")
    cmd_links()


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    cmd = args[0] if args else ""
    if cmd == "sites":
        cmd_sites()
    elif cmd == "quota":
        cmd_quota()
    elif cmd == "feed":
        cmd_feed()
    elif cmd == "submit":
        cmd_submit()
    elif cmd == "indexnow":
        cmd_indexnow()
    elif cmd == "stats":
        cmd_stats(int(args[1]) if len(args) > 1 else 28)
    elif cmd == "pages":
        cmd_pages(int(args[1]) if len(args) > 1 else 28)
    elif cmd == "crawl":
        cmd_crawl()
    elif cmd == "issues":
        cmd_issues()
    elif cmd == "blocked":
        cmd_blocked()
    elif cmd == "report":
        cmd_report()
    elif cmd == "url":
        if len(args) < 2:
            sys.exit("usage: bing.py url <url>")
        cmd_url(args[1])
    elif cmd == "keywords":
        if len(args) < 2:
            sys.exit('usage: bing.py keywords "some query"')
        cmd_keywords(args[1])
    elif cmd == "links":
        cmd_links()
    else:
        sys.exit(__doc__.strip().splitlines()[-1].strip() + "\n  (see the docstring for the full list)")


if __name__ == "__main__":
    main()
