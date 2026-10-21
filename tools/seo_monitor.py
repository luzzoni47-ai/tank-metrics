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


def check_page(url: str) -> dict:
    code, body = get(url)
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

    page["title"] = title
    page["description"] = desc
    return page


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE).rstrip("/")
    now = datetime.now(timezone.utc)
    problems: list[str] = []

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
    dupes = {u for u in urls if urls.count(u) > 1}
    for d in dupes:
        problems.append(f"duplicate sitemap entry {d}")

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        pages = list(pool.map(check_page, urls))

    for p in pages:
        for prob in p["problems"]:
            problems.append(f"{p['url'].replace(base, '') or '/'}: {prob}")

    titles: dict[str, list[str]] = {}
    descs: dict[str, list[str]] = {}
    for p in pages:
        if p.get("title"):
            titles.setdefault(p["title"], []).append(p["url"])
        if p.get("description"):
            descs.setdefault(p["description"], []).append(p["url"])
    for t, us in titles.items():
        if len(us) > 1:
            problems.append(f"duplicate title on {len(us)} pages: {t[:50]}")
    for d, us in descs.items():
        if len(us) > 1:
            problems.append(f"duplicate description on {len(us)} pages: {d[:50]}")

    stamp = now.strftime("%Y-%m-%d")
    REPORTS.mkdir(exist_ok=True)
    lines = [
        f"# SEO check — {stamp}",
        "",
        f"Sitemap me pages: **{len(urls)}**",
        f"Sabhi 200: **{'haan' if all(p['status'] == 200 for p in pages) else 'nahi'}**",
        f"Problems: **{len(problems)}**",
        "",
    ]
    if problems:
        lines.append("## Problems")
        lines += [f"- {p}" for p in problems]
    else:
        lines.append("Koi problem nahi. Sab pages theek hain.")
    lines.append("")
    (REPORTS / "seo-latest.md").write_text("\n".join(lines), encoding="utf-8")

    hist_path = REPORTS / "seo-history.json"
    history = json.loads(hist_path.read_text()) if hist_path.exists() else []
    history = [h for h in history if h.get("date") != stamp]
    history.append({"date": stamp, "pages": len(urls), "problems": len(problems)})
    history.sort(key=lambda h: h["date"])
    hist_path.write_text(json.dumps(history[-90:], indent=1), encoding="utf-8")

    print(f"pages: {len(urls)} | problems: {len(problems)}")
    for p in problems[:15]:
        print(f"  - {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
