#!/usr/bin/env python3
"""Weekly health audit for tankmetrics.in.

Indexing is only worth chasing while the site is clean: a single 404 in the
sitemap, a stray noindex, or a page that lost its canonical quietly costs
rankings. This walks the live sitemap and checks the things that actually block
or dilute indexing:

  * every sitemap URL answers 200
  * every page still carries a title, a canonical and a description
  * no page says noindex
  * no internal link on the sampled pages points at a 404

Deterministic and LLM-free. When it finds a problem it opens (or updates) one
GitHub issue so the failure is visible instead of silent.

    python3 main.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html import unescape

HOST = "tankmetrics.in"
BASE = f"https://{HOST}"
SITEMAP = f"{BASE}/sitemap.xml"
UA = "TankMetrics-HealthCheck/1.0 (+https://tankmetrics.in)"
REPO = "luzzoni47-ai/tank-metrics"
ISSUE_TITLE = "Site health audit found problems"
DRY = "--dry-run" in sys.argv
# Favicon/stylesheet references are assets, not pages; a missing one is a
# separate concern and would otherwise drown the page-level findings.
ASSET_RE = re.compile(r"\.(css|js|png|jpe?g|svg|ico|webp|woff2?|xml|txt)$", re.I)


def get_secret(name: str) -> str:
    url = os.environ.get("AGENT_SERVER_URL", "").rstrip("/")
    key = os.environ.get("SESSION_API_KEY") or os.environ.get("OH_SESSION_API_KEYS_0", "")
    if url:
        url = f"{url}/api/settings/secrets/{name}"
    else:
        api = os.environ["OPENHANDS_CLOUD_API_URL"].rstrip("/")
        url = f"{api}/api/v1/sandboxes/{os.environ['SANDBOX_ID']}/settings/secrets/{name}"
    with urllib.request.urlopen(
        urllib.request.Request(url, headers={"X-Session-API-Key": key}), timeout=20
    ) as r:
        return r.read().decode().strip()


def fire_callback(status: str = "COMPLETED", error: str | None = None) -> None:
    url = os.environ.get("AUTOMATION_CALLBACK_URL", "")
    if not url:
        return
    body = {"status": status, "run_id": os.environ.get("AUTOMATION_RUN_ID", "")}
    if error:
        body["error"] = error
    try:
        urllib.request.urlopen(
            urllib.request.Request(
                url,
                data=json.dumps(body).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.environ.get('AUTOMATION_CALLBACK_API_KEY', '')}",
                },
            ),
            timeout=20,
        )
    except Exception as e:
        print(f"Callback error: {e}")


def fetch(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return f"error: {e}", ""


def sitemap_urls() -> list[str]:
    status, xml = fetch(SITEMAP)
    if status != 200:
        raise RuntimeError(f"sitemap {SITEMAP} -> {status}")
    return [u.strip() for u in re.findall(r"<loc>\s*(.*?)\s*</loc>", xml)]


def check_page(url: str) -> tuple[str, list[str], set[str]]:
    """Return (url, problems, internal paths found on the page)."""
    problems: list[str] = []
    status, html = fetch(url)
    if status != 200:
        return url, [f"HTTP {status} (expected 200)"], set()

    if not re.search(r"<title[^>]*>\s*\S", html, re.I):
        problems.append("no <title>")
    if not re.search(r'<link[^>]+rel=["\']canonical["\']', html, re.I):
        problems.append("no canonical")
    if not re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']\s*\S', html, re.I):
        problems.append("no meta description")
    if re.search(r'<meta[^>]+name=["\']robots["\'][^>]*noindex', html, re.I):
        problems.append("has noindex")

    links = set()
    for href in re.findall(r'<a\s[^>]*href=["\'](/[^"\'#?]*)', html, re.I):
        href = unescape(href)
        if not href or ASSET_RE.search(href):
            continue
        links.add(href.split("#")[0])
    return url, problems, links


def github_issue(token: str, body: str) -> str:
    api = f"https://api.github.com/repos/{REPO}/issues"
    hdrs = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": UA,
    }
    # Update the existing issue when one is already open, so a weekly run cannot
    # bury the alert under duplicates.
    req = urllib.request.Request(f"{api}?state=open&per_page=50", headers=hdrs)
    with urllib.request.urlopen(req, timeout=25) as r:
        existing = json.loads(r.read())
    for iss in existing:
        if iss.get("title") == ISSUE_TITLE:
            req = urllib.request.Request(
                f"{api}/{iss['number']}",
                data=json.dumps({"body": body}).encode(),
                headers={**hdrs, "Content-Type": "application/json"},
                method="PATCH",
            )
            with urllib.request.urlopen(req, timeout=25) as r:
                return f"updated issue #{iss['number']}"
    req = urllib.request.Request(
        f"{api}",
        data=json.dumps({"title": ISSUE_TITLE, "body": body}).encode(),
        headers={**hdrs, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return f"opened issue #{json.loads(r.read())['number']}"


def main() -> dict:
    print(f"Health audit of {HOST}")

    urls = sitemap_urls()
    print(f"sitemap: {len(urls)} URL(s)")
    if not urls:
        raise RuntimeError("sitemap returned no URLs")

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check_page, urls))

    broken = []
    page_problems = []
    all_links: set[str] = set()
    for url, problems, links in results:
        if problems and any(p.startswith("HTTP") or p.startswith("error") for p in problems):
            broken.append((url, problems[0]))
        elif problems:
            page_problems.append((url, problems))
        all_links |= links

    # Verify every distinct internal link once, not once per referring page.
    known = set(urls)
    to_check = sorted(
        f"{BASE}{p}" if not p.startswith("http") else p
        for p in all_links
        if f"{BASE}{p}" not in known and p not in known
    )
    dead_links = []
    if to_check:
        with ThreadPoolExecutor(max_workers=8) as pool:
            for u, (status, _) in zip(to_check, pool.map(lambda x: fetch(x, timeout=15), to_check)):
                if status != 200:
                    dead_links.append((u, status))

    print(f"broken sitemap URLs: {len(broken)}")
    print(f"pages missing meta/canonical: {len(page_problems)}")
    print(f"internal links checked: {len(to_check)}, dead: {len(dead_links)}")

    total = len(broken) + len(page_problems) + len(dead_links)
    report = {
        "urls": len(urls),
        "broken": len(broken),
        "page_problems": len(page_problems),
        "dead_links": len(dead_links),
    }

    if total == 0:
        print("DONE: site is clean")
        return report

    lines = [
        f"Automated health audit of https://{HOST} found {total} problem(s).",
        "",
        f"- sitemap URLs checked: {len(urls)}",
        f"- non-200 sitemap URLs: {len(broken)}",
        f"- pages missing title/canonical/description or carrying noindex: {len(page_problems)}",
        f"- dead internal links: {len(dead_links)}",
        "",
    ]
    if broken:
        lines += ["### Non-200 sitemap URLs", ""]
        lines += [f"- `{u}` -> {s}" for u, s in broken[:40]]
        lines += [""]
    if page_problems:
        lines += ["### Page metadata problems", ""]
        lines += [f"- `{u}`: {', '.join(p)}" for u, p in page_problems[:40]]
        lines += [""]
    if dead_links:
        lines += ["### Dead internal links", ""]
        lines += [f"- `{u}` -> {s}" for u, s in dead_links[:40]]
        lines += [""]
    lines += [
        "---",
        "_This issue was opened automatically by the Tank Metrics weekly health "
        "audit (an AI agent on behalf of the site owner). It is updated in place "
        "on each run and is not duplicated._",
    ]
    body = "\n".join(lines)

    if DRY:
        print("dry run - would file an issue:")
        print(body[:1500])
        return report

    try:
        token = get_secret("GITHUB_TOKEN")
        print(github_issue(token, body))
    except Exception as e:
        print(f"could not file the issue ({e}); problems above are still real")
    return report


if __name__ == "__main__":
    try:
        report = main()
        print(f"DONE: {json.dumps(report)}")
        fire_callback("COMPLETED")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        fire_callback("FAILED", str(e))
        sys.exit(1)
