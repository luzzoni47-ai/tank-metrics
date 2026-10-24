#!/usr/bin/env python3
"""Live SEO health check for the public site.

Search Console cannot be logged into by the agent, but every condition that
makes Google drop a page is observable from outside: a non-200, a noindex, a
canonical pointing somewhere else, a missing description, a blocked path. This
walks the sitemap, checks each page for those, and records the result so the
trend is visible day over day.

    python3 tools/seo_monitor.py [base_url]

Writes tools/reports/seo-latest.md (human report) and seo-history.json (one
row per run). Exits 1 when any check fails, so a scheduled run can flag it.
"""
from __future__ import annotations

import json
import html
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = Path(__file__).resolve().parent / "reports"
DEFAULT_BASE = "https://tankmetrics.in"
URL_MAP = Path(__file__).resolve().parent / "url-map.json"
PUBLIC = Path(__file__).resolve().parent.parent / "public"
UA = "TankMetrics-SEO-Monitor/1.0"
TIMEOUT = 25
WORKERS = 8

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
# A description may contain an apostrophe (month's, you'd) inside a
# double-quoted attribute, so the quote pairs have to be matched, not mixed.
_ATTR = r"""(?:"([^"]*)"|'([^']*)')"""
DESC_RE = re.compile(r'<meta[^>]+name=["\']description["\'][^>]*content=' + _ATTR, re.I)
DESC_RE2 = re.compile(r'<meta[^>]+content=' + _ATTR + r'[^>]*name=["\']description["\']', re.I)
CANON_RE = re.compile(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', re.I)
ROBOTS_RE = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']*)["\']', re.I)
LD_RE = re.compile(r'application/ld\+json', re.I)
OG_RE = re.compile(r'<meta[^>]+property=["\'](og:[a-z:]+)["\'][^>]*content=' + _ATTR, re.I)
H1_RE = re.compile(r"<h1[\s>]", re.I)

TITLE_MIN, TITLE_MAX = 10, 65
DESC_MIN, DESC_MAX = 50, 165


def get(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""


def head(url: str) -> tuple[int, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {})
    except Exception:
        return 0, {}


def sitemap_urls(base: str) -> list[str]:
    """Read the sitemap and re-point every entry at `base`.

    The sitemap always names the production origin, so checking a local server
    would silently test the live site instead. Rewriting the origin keeps the
    check honest whichever base was asked for.
    """
    code, body = get(f"{base}/sitemap.xml")
    if code != 200:
        return []
    root = ET.fromstring(body)
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    out = []
    for e in root.iter(f"{ns}loc"):
        if not e.text:
            continue
        path = re.sub(r"^https?://[^/]+", "", e.text.strip())
        out.append(base + (path or "/"))
    return out


def check_page(url: str, body: str | None = None) -> dict:
    if body is None:
        code, body = get(url)
    else:
        code = 200
    page = {"url": url, "status": code, "problems": []}
    if code != 200:
        page["problems"].append(f"HTTP {code}")
        return page

    title = (TITLE_RE.search(body) or [None, ""])[1].strip()
    # Entities must be decoded before measuring: "&#x27;" is one rendered
    # character, not six, so a raw count reports titles as too long.
    title = html.unescape(title)
    if not title:
        page["problems"].append("no <title>")
    elif not (TITLE_MIN <= len(title) <= TITLE_MAX):
        page["problems"].append(f"title length {len(title)}")

    desc = ""
    for rx in (DESC_RE, DESC_RE2):
        m = rx.search(body)
        if m:
            desc = html.unescape((m.group(1) or m.group(2) or "").strip())
            break
    if not desc:
        page["problems"].append("no meta description")
    elif not (DESC_MIN <= len(desc) <= DESC_MAX):
        page["problems"].append(f"description length {len(desc)}")

    canon = (CANON_RE.search(body) or [None, ""])[1].strip()
    if not canon:
        page["problems"].append("no canonical")
    else:
        # Compare the path, not the origin: the canonical is always the
        # production URL, which is correct even when a local server is probed.
        want = re.sub(r"^https?://[^/]+", "", url).rstrip("/")
        got = re.sub(r"^https?://[^/]+", "", canon).rstrip("/")
        if got != want:
            page["problems"].append(f"canonical -> {canon}")

    robots = (ROBOTS_RE.search(body) or [None, ""])[1].lower()
    if "noindex" in robots:
        page["problems"].append("noindex")

    if not H1_RE.search(body):
        page["problems"].append("no <h1>")
    if not LD_RE.search(body):
        page["problems"].append("no JSON-LD")

    # Social preview tags. A shared link is how most of this site's traffic
    # arrives, and without these the card is blank or generic.
    og = {m.group(1).lower(): html.unescape((m.group(2) or m.group(3) or "").strip())
          for m in OG_RE.finditer(body)}
    for tag in ("og:title", "og:description", "og:url", "og:type"):
        if not og.get(tag):
            page["problems"].append(f"no {tag}")
    if og.get("og:title") and title and og["og:title"] != title:
        page["problems"].append("og:title differs from <title>")

    page["title"] = title
    page["description"] = desc
    return page


def local_pages(base: str) -> list[tuple[str, str]]:
    """Read the built pages straight off disk, so the check runs before deploy.

    The url-map is the same table next.config.mjs rewrites from, so a clean path
    here is exactly what a visitor would hit. Reading files avoids needing a
    server, which is the whole point: the daily run can catch a bad title before
    it is published instead of after.
    """
    mapping = json.loads(URL_MAP.read_text(encoding="utf-8"))
    # The home page is not in url-map: next.config.mjs rewrites "/" on its own,
    # so add it here or the check would skip the one page everyone lands on.
    mapping = {"/": "/site/index.html", **mapping}
    out = []
    for clean, backing in mapping.items():
        path = PUBLIC / backing.lstrip("/")
        if not path.exists():
            out.append((base + clean, ""))
            continue
        out.append((base + clean, path.read_text(encoding="utf-8", errors="replace")))
    return out


def finish(label: str, urls: list[str], pages: list[dict],
           problems: list[str], now: datetime) -> int:
    titles: dict[str, list[str]] = {}
    descs: dict[str, list[str]] = {}
    for pg in pages:
        if pg.get("title"):
            titles.setdefault(pg["title"], []).append(pg["url"])
        if pg.get("description"):
            descs.setdefault(pg["description"], []).append(pg["url"])
    for ti, us in titles.items():
        if len(us) > 1:
            problems.append(f"duplicate title on {len(us)} pages: {ti[:50]}")
    for de, us in descs.items():
        if len(us) > 1:
            problems.append(f"duplicate description on {len(us)} pages: {de[:50]}")

    stamp = now.strftime("%Y-%m-%d")
    REPORTS.mkdir(exist_ok=True)
    lines = [
        f"# SEO check ({label}) - {stamp}",
        "",
        f"Pages checked: **{len(urls)}**",
        f"All 200: **{'yes' if all(pg['status'] == 200 for pg in pages) else 'no'}**",
        f"Problems: **{len(problems)}**",
        "",
    ]
    if problems:
        lines.append("## Problems")
        lines += [f"- {pr}" for pr in problems]
    else:
        lines.append("No problems. Every page is fine.")
    lines.append("")
    (REPORTS / f"seo-{'local' if label == 'local' else 'latest'}.md").write_text(
        "\n".join(lines), encoding="utf-8")

    hist_path = REPORTS / "seo-history.json"
    history = json.loads(hist_path.read_text()) if hist_path.exists() else []
    history = [h for h in history if h.get("date") != stamp]
    history.append({"date": stamp, "pages": len(urls),
                    "problems": len(problems), "mode": label})
    history.sort(key=lambda h: h["date"])
    hist_path.write_text(json.dumps(history[-90:], indent=1), encoding="utf-8")

    print(f"[{label}] pages: {len(urls)} | problems: {len(problems)}")
    for pr in problems[:15]:
        print(f"  - {pr}")
    return 1 if problems else 0


def run_local(base: str, now: datetime, problems: list[str]) -> int:
    """Check the built files before anything is deployed."""
    robots = PUBLIC / "robots.txt"
    if not robots.exists():
        problems.append("public/robots.txt missing")
    elif "sitemap:" not in robots.read_text(encoding="utf-8").lower():
        problems.append("robots.txt has no Sitemap: line")

    sm = PUBLIC / "sitemap.xml"
    if not sm.exists():
        problems.append("public/sitemap.xml missing")
        return finish("local", [], [], problems, now)

    root = ET.fromstring(sm.read_text(encoding="utf-8"))
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    sm_paths = [re.sub(r"^https?://[^/]+", "", e.text.strip()) or "/"
                for e in root.iter(f"{ns}loc") if e.text]

    # A page listed twice is a duplicate for the crawler just as it is live, and
    # the live branch below flags it. Checking it here too means a duplicate is
    # caught before the deploy rather than after, which is the whole point of
    # running the monitor locally.
    for path in {p for p in sm_paths if sm_paths.count(p) > 1}:
        problems.append(f"duplicate sitemap entry {base}{path}")

    pairs = local_pages(base)
    known = {u.replace(base, "") or "/" for u, _ in pairs}
    for path in sm_paths:
        if path not in known:
            problems.append(f"sitemap lists {path} but url-map has no such page")
    for path in known:
        if path not in sm_paths:
            problems.append(f"url-map has {path} but the sitemap does not")

    pages = [check_page(url, body) for url, body in pairs]
    for pg in pages:
        for prob in pg["problems"]:
            problems.append(f"{pg['url'].replace(base, '') or '/'}: {prob}")
    return finish("local", [u for u, _ in pairs], pages, problems, now)


def main() -> int:
    argv = sys.argv[1:]
    local = "--local" in argv
    argv = [a for a in argv if a != "--local"]
    base = (argv[0] if argv else
            ("http://localhost" if local else DEFAULT_BASE)).rstrip("/")
    # A filesystem path carries no scheme, so it can only mean "check the built
    # files". The daily runbooks call it as `seo_monitor.py .`; without this the
    # path is treated as a host and urllib raises "unknown url type".
    if base and "://" not in base:
        local = True
        base = ""
    now = datetime.now(timezone.utc)
    problems: list[str] = []

    if local:
        return run_local(base, now, problems)

    code, body = get(f"{base}/robots.txt")
    if code != 200:
        problems.append(f"robots.txt -> HTTP {code}")
    elif "sitemap:" not in body.lower():
        problems.append("robots.txt has no Sitemap: line")

    home_code, home_headers = head(base + "/")
    if home_code != 200:
        problems.append(f"home -> HTTP {home_code}")
    for h in ("Content-Security-Policy", "X-Frame-Options",
              "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy"):
        if h not in home_headers:
            problems.append(f"missing header {h}")

    urls = sitemap_urls(base)
    if not urls:
        problems.append("sitemap.xml unreadable or empty")
    for d in {u for u in urls if urls.count(u) > 1}:
        problems.append(f"duplicate sitemap entry {d}")

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        pages = list(pool.map(check_page, urls))

    for pg in pages:
        for prob in pg["problems"]:
            problems.append(f"{pg['url'].replace(base, '') or '/'}: {prob}")

    return finish("live", urls, pages, problems, now)


if __name__ == "__main__":
    sys.exit(main())
