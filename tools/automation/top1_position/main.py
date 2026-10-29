#!/usr/bin/env python3
"""Every-6-hours Top-1 push for tankmetrics.in - self-contained automation.

Runs inside the automation sandbox with no LLM and no clone of the repo: it
reads the GSC refresh token from the automation secret store, pulls Search
Console data over HTTPS, and reads page titles straight off the live site. That
keeps it independent of the build, so a broken build cannot silently stop the
rank tracking.

Why every 6 hours: Search Console position data lags about a day, so a faster
loop re-reads the same numbers and burns quota. Four reads a day catches a move
the day it lands.

Each run:
  1. Pulls queries + pages from the Search Console API.
  2. Buckets each query by what it needs to reach #1:
       TITLE FIX - ranks <=10, zero clicks: the title does not say what was typed.
       PUSH      - position 11-30: needs depth and one internal link.
       BUILD     - impressions, no page in the top 30: write it.
       WATCH     - too little data.
  3. Diffs positions against the last run and reports anything that moved.
  4. Stores the position snapshot in the automation KV store.
  5. Opens (or updates) one GitHub issue with the report, so a move to page 1 is
     visible without anyone opening the repo.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HOST = "tankmetrics.in"
BASE = f"https://{HOST}"
REPO = "luzzoni47-ai/tank-metrics"
ISSUE_TITLE = "Top-1 push: title fixes and position moves"
DAYS = 28
UA = "TankMetrics-Top1/1.0 (+https://tankmetrics.in)"
DRY = "--dry-run" in sys.argv

STOP = {
    "a", "an", "the", "in", "of", "for", "to", "and", "or", "is", "are", "what",
    "how", "calculator", "calculate", "free", "online", "india", "indian", "ka",
    "ki", "kitna", "kitne", "hoga", "hota", "hai", "me", "mein", "vs", "with",
}


# ------------------------------------------------------------------- plumbing

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
        urllib.request.urlopen(urllib.request.Request(
            url, data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get('AUTOMATION_CALLBACK_API_KEY', '')}",
            }), timeout=20)
    except Exception as e:
        print(f"callback error: {e}")


_KV_TOKEN = os.environ.get("AUTOMATION_KV_TOKEN", "")
_KV_BASE = os.environ.get("AUTOMATION_API_URL", "").rstrip("/")
_STATE_KEY = "top1_positions"


def kv_available() -> bool:
    return bool(_KV_TOKEN and _KV_BASE)


def load_state() -> dict:
    if not kv_available():
        return {}
    try:
        req = urllib.request.Request(
            f"{_KV_BASE}/kv/{_STATE_KEY}",
            headers={"Authorization": f"Bearer {_KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            v = json.loads(r.read().decode())
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def save_state(state: dict) -> None:
    if DRY or not kv_available():
        return
    try:
        req = urllib.request.Request(
            f"{_KV_BASE}/kv/{_STATE_KEY}",
            data=json.dumps({"value": state}).encode(),
            method="PUT",
            headers={"Authorization": f"Bearer {_KV_TOKEN}",
                     "Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20).read()
    except Exception as e:
        print(f"kv save error: {e}")


# ------------------------------------------------------------------ gsc access

def access_token() -> str:
    """Refresh the OAuth token from the stored refresh token. Stdlib only."""
    raw = os.environ.get("GSC_OAUTH_JSON") or get_secret("GSC_OAUTH_JSON")
    creds = json.loads(raw)
    body = urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())["access_token"]


def gsc_query(token: str, site: str, dim: str, days: int) -> list[dict]:
    end = time.strftime("%Y-%m-%d")
    start = time.strftime("%Y-%m-%d", time.localtime(time.time() - days * 86400))
    payload = {"startDate": start, "endDate": end, "dimensions": [dim], "rowLimit": 500}
    req = urllib.request.Request(
        f"https://www.googleapis.com/webmasters/v3/sites/"
        f"{urllib.parse.quote(site, safe='')}/searchAnalytics/query",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode()).get("rows", [])


def resolve_site(token: str) -> str:
    req = urllib.request.Request(
        "https://www.googleapis.com/webmasters/v3/sites",
        headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        entries = json.loads(r.read().decode()).get("siteEntry", [])
    for e in entries:
        if e.get("siteUrl", "").endswith(HOST):
            return e["siteUrl"]
    return f"sc-domain:{HOST}"


# --------------------------------------------------------------- page reading

def toks(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9\u0900-\u097f]+", text.lower())
    return {w for w in words if w not in STOP and len(w) > 1}


def fetch_title(clean: str) -> str:
    """Read a live page's <title>. 30 pages is plenty to match a query."""
    try:
        req = urllib.request.Request(BASE + clean, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            text = r.read(200_000).decode("utf-8", "ignore")
        m = re.search(r"<title>([^<]*)</title>", text)
        return m.group(1) if m else ""
    except Exception:
        return ""


def titles_for(paths: list[str]) -> dict[str, str]:
    with ThreadPoolExecutor(max_workers=12) as ex:
        return dict(zip(paths, ex.map(fetch_title, paths)))


# ------------------------------------------------------------------- analysis

def bucketise(queries: list[dict], pages: list[dict], titles: dict[str, str]) -> dict:
    ptoks = {c: toks(t) for c, t in titles.items()}
    out: dict[str, list[dict]] = {"TITLE FIX": [], "PUSH": [], "BUILD": [], "WATCH": []}
    for r in queries:
        q = r["keys"][0]
        pos, imp, clicks = r["position"], r["impressions"], r["clicks"]
        qt = toks(q)
        need = 0.6 if len(qt) <= 3 else 0.4
        best, best_ov = None, 0.0
        for p in pages:
            clean = p["keys"][0].replace(BASE, "")
            pt = ptoks.get(clean, set())
            if not pt or not qt:
                continue
            ov = len(qt & pt) / len(qt)
            if ov > best_ov:
                best_ov, best = ov, clean
        rec = {"query": q, "position": round(pos, 1), "impressions": imp, "clicks": clicks}
        if best and best_ov >= need:
            rec["page"] = best
        if pos <= 10 and clicks == 0 and imp >= 3 and best_ov >= need:
            out["TITLE FIX"].append(rec)
        elif 10 < pos <= 30 and imp >= 2:
            out["PUSH"].append(rec)
        elif best_ov < need and imp >= 3:
            out["BUILD"].append(rec)
        else:
            out["WATCH"].append(rec)
    for k in out:
        out[k].sort(key=lambda r: (r["position"], -r["impressions"]))
    return out


def render(buckets: dict, moved: list[dict], n_q: int, n_p: int) -> str:
    L = [f"Automated run {time.strftime('%Y-%m-%d %H:%M UTC')}",
         f"Queries: {n_q} | pages: {n_p} | window: {DAYS} days", "",
         f"- TITLE FIX: {len(buckets['TITLE FIX'])} (rank <=10, 0 clicks - rewrite the title in the query's words)",
         f"- PUSH: {len(buckets['PUSH'])} (position 11-30 - add depth + one internal link)",
         f"- BUILD: {len(buckets['BUILD'])} (no page in the top 30 - write it)",
         f"- WATCH: {len(buckets['WATCH'])}", ""]
    for key, head in (("TITLE FIX", "Title fixes - do these first"),
                      ("PUSH", "Striking distance"), ("BUILD", "Content gaps")):
        rows = buckets[key][:20]
        L += [f"## {head}", ""]
        if not rows:
            L += ["None.", ""]
            continue
        for r in rows:
            L.append(f"- `{r['query']}` pos {r['position']} / {r['impressions']} impressions"
                     f" -> `{r.get('page', '-')}`")
        L.append("")
    L += ["## Position moves since last run", ""]
    if moved:
        for m in moved[:30]:
            L.append(f"- `{m['query']}` {m['was']} -> {m['now']} ({m['impressions']} impressions)")
    else:
        L.append("No move of 1.0 or more.")
    return "\n".join(L)


# ------------------------------------------------------------------ gh issue

def gh(method: str, path: str, payload=None, token: str = "") -> dict | list:
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": UA,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
    return json.loads(body) if body.strip() else {}


def upsert_issue(body: str, token: str) -> str:
    issues = gh("GET", f"/repos/{REPO}/issues?state=open&per_page=100", token=token)
    if isinstance(issues, list):
        for it in issues:
            if it.get("title") == ISSUE_TITLE and "pull_request" not in it:
                gh("POST", f"/repos/{REPO}/issues/{it['number']}/comments",
                   {"body": body}, token)
                return f"commented on #{it['number']}"
    out = gh("POST", f"/repos/{REPO}/issues",
             {"title": ISSUE_TITLE, "body": body}, token)
    return f"opened #{out.get('number')}"


# ----------------------------------------------------------------------- main

def main() -> None:
    print(f"top1 run {time.strftime('%Y-%m-%d %H:%M')} (dry={DRY})")
    token = access_token()
    site = resolve_site(token)
    queries = gsc_query(token, site, "query", DAYS)
    pages = gsc_query(token, site, "page", DAYS)
    print(f"  gsc: {len(queries)} queries, {len(pages)} pages from {site}")

    paths = sorted({p["keys"][0].replace(BASE, "") for p in pages
                    if p["keys"][0].startswith(BASE)})
    titles = titles_for(paths)
    buckets = bucketise(queries, pages, titles)

    state = load_state()
    prev = state.get("positions", {})
    moved = []
    for r in queries:
        was = prev.get(r["keys"][0])
        if was is not None and abs(was - r["position"]) >= 1.0:
            moved.append({"query": r["keys"][0], "was": round(was, 1),
                          "now": round(r["position"], 1), "impressions": r["impressions"]})
    moved.sort(key=lambda m: m["now"])
    if not DRY:
        state["positions"] = {r["keys"][0]: round(r["position"], 1) for r in queries}
        state["updated"] = time.strftime("%Y-%m-%dT%H:%M")
        save_state(state)

    body = render(buckets, moved, len(queries), len(pages))
    print(body)
    if not DRY:
        try:
            print("  github:", upsert_issue(body, get_secret("GITHUB_TOKEN")))
        except Exception as e:
            print(f"  github error: {e}")


if __name__ == "__main__":
    try:
        main()
        fire_callback("COMPLETED")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        fire_callback("FAILED", str(e))
        sys.exit(1)
