#!/usr/bin/env python3
"""Daily search-engine sweep for tankmetrics.in: IndexNow + Bing Webmaster.

Deterministic on purpose: no LLM. Two channels, because they do different jobs:

1. **IndexNow** reaches Bing, Yandex, Seznam and Naver in one POST. It is the
   cheap announcement, but on its own it does NOT make Bing crawl a brand-new
   domain: Bing leans far harder on inbound links than Google does, and with no
   citations yet the site sat at "crawled: 0" for weeks with a clean robots.txt
   and an accepted sitemap.

2. **Bing Webmaster** is the channel that actually forces a crawl. `SubmitFeed`
   hands Bing the sitemap (free, no quota) and `SubmitUrlbatch` asks for an
   on-demand crawl of specific URLs (100/day). That is the piece that was
   missing - it was never run, which is why Bing had crawled nothing.

Both channels share one state file. The run is best-effort per channel: if
`BING_API_KEY` is absent the Bing half is skipped with a note and IndexNow still
runs, so a missing key never fails the sweep.

    python3 main.py            # real run
    python3 main.py --dry-run  # check only; no submit, no state written
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

HOST = "tankmetrics.in"
SITE = f"https://{HOST}/"
BASE = f"https://{HOST}"
SITEMAP = f"{BASE}/sitemap.xml"
KEY = "91ac4c920695a74eec34342ceb18acbf"
KEY_URL = f"{BASE}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"
BING_API = "https://ssl.bing.com/webmaster/api.svc/json"
BING_QUOTA = 100  # SubmitUrlbatch URLs per day
UA = "TankMetrics-IndexNow/1.0 (+https://tankmetrics.in)"
DRY = "--dry-run" in sys.argv

_KV_TOKEN = os.environ.get("AUTOMATION_KV_TOKEN", "")
_KV_BASE = os.environ.get("AUTOMATION_API_URL", "").rstrip("/")
_STATE_KEY = "page_hashes"
_STATE_FILE = Path("/tmp/tank_metrics_indexnow_state.json")


def kv_available() -> bool:
    return bool(_KV_TOKEN and _KV_BASE)


def kv_get(key: str):
    req = urllib.request.Request(
        f"{_KV_BASE}/v1/kv/{key}", headers={"Authorization": f"Bearer {_KV_TOKEN}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())["value"]
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def kv_set(key: str, value) -> None:
    req = urllib.request.Request(
        f"{_KV_BASE}/v1/kv/{key}",
        data=json.dumps(value).encode(),
        headers={"Authorization": f"Bearer {_KV_TOKEN}", "Content-Type": "application/json"},
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        r.read()


def load_state() -> dict:
    if kv_available():
        try:
            return kv_get(_STATE_KEY) or {}
        except Exception as e:
            print(f"KV read failed, using local file: {e}")
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_state(state: dict) -> None:
    if kv_available():
        try:
            kv_set(_STATE_KEY, state)
            return
        except Exception as e:
            print(f"KV write failed, using local file: {e}")
    try:
        _STATE_FILE.write_text(json.dumps(state))
    except Exception as e:
        print(f"state save failed: {e}")


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


def get(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def sitemap_urls() -> tuple[list[str], str]:
    _, body = get(SITEMAP)
    xml = body.decode("utf-8", "replace")
    urls = [u.strip() for u in re.findall(r"<loc>\s*(.*?)\s*</loc>", xml)]
    lastmods = re.findall(r"<lastmod>\s*(\d{4}-\d{2}-\d{2})", xml)
    return urls, (max(lastmods) if lastmods else "unknown")


def fingerprint(url: str) -> str | None:
    """Hash the page body so a real content change is what triggers a submit."""
    try:
        status, body = get(url)
        if status != 200:
            return None
        return hashlib.sha256(body).hexdigest()[:16]
    except Exception:
        return None


def submit(urls: list[str]):
    payload = {"host": HOST, "key": KEY, "keyLocation": KEY_URL, "urlList": urls}
    for attempt in range(3):
        req = urllib.request.Request(
            ENDPOINT,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": UA},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status
        except urllib.error.HTTPError as e:
            # 202 means the key is still being verified; give it a moment.
            if e.code == 202 and attempt < 2:
                time.sleep(45)
                continue
            return e.code
        except Exception as e:
            if attempt < 2:
                time.sleep(10)
                continue
            return f"error: {e}"
    return "unreachable"


def bing_key() -> str:
    """The Bing Webmaster API key, from the environment or the secret store.

    Tries the canonical name and the owner's own name for it, because the key
    was registered as `Bing_apy_key`. Returns "" when there is no key anywhere,
    so the caller can skip the Bing half instead of failing the whole sweep.
    """
    for name in ("BING_API_KEY", "Bing_apy_key"):
        if os.environ.get(name, "").strip():
            return os.environ[name].strip()
    url = os.environ.get("AGENT_SERVER_URL", "").rstrip("/")
    key = os.environ.get("SESSION_API_KEY") or os.environ.get("OH_SESSION_API_KEYS_0", "")
    for name in ("BING_API_KEY", "Bing_apy_key"):
        try:
            if url:  # local Agent Canvas
                endpoint = f"{url}/api/settings/secrets/{name}"
            else:  # OpenHands Cloud / Enterprise
                api = os.environ["OPENHANDS_CLOUD_API_URL"].rstrip("/")
                endpoint = f"{api}/api/v1/sandboxes/{os.environ['SANDBOX_ID']}/settings/secrets/{name}"
            with urllib.request.urlopen(
                urllib.request.Request(endpoint, headers={"X-Session-API-Key": key}), timeout=20
            ) as r:
                value = r.read().decode().strip()
                if value:
                    return value
        except Exception:
            continue
    return ""


def bing_call(method: str, *, params: dict | None = None, body: dict | None = None):
    """One Bing Webmaster API call. The key goes in the query string, as Bing wants."""
    url = f"{BING_API}/{method}?apikey={bing_key()}"
    for k, v in (params or {}).items():
        url += f"&{k}={urllib.parse.quote(str(v))}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read().decode("utf-8", "replace")
    return json.loads(raw).get("d") if raw.strip() else None


def bing_push(state: dict, targets: list[str]) -> dict:
    """Register the sitemap and force a crawl of the day's URLs.

    This is the half that was missing. `SubmitFeed` costs no quota and is
    idempotent, so it runs every time. `SubmitUrlbatch` spends the 100/day
    quota on URLs not sent in the last 30 days. Returns a small report; never
    raises - a Bing failure must not take the IndexNow sweep down with it.
    """
    if not bing_key():
        return {"skipped": "no BING_API_KEY"}
    report: dict = {}
    today = date.today().isoformat()

    # Prefer the pages that just changed, then top up from the rest of the
    # sitemap, so a fresh post is crawled first.
    cutoff = (date.today() - timedelta(days=30)).isoformat()
    fresh = [u for u in targets if state.get(u, "") < cutoff]
    rest = [u for u in sitemap_urls()[0]
            if u not in fresh and state.get(f"bing:{u}", "") < cutoff]
    todo = (fresh + rest)[:BING_QUOTA]
    if DRY:
        report["feed"] = "dry run"
        report["submit"] = f"dry run, would submit {len(todo)}"
        return report

    try:
        bing_call("SubmitFeed", body={"siteUrl": SITE, "feedUrl": f"{BASE}/sitemap.xml"})
        report["feed"] = "submitted sitemap.xml"
    except urllib.error.HTTPError as e:
        report["feed"] = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:120]}"
    except Exception as e:
        report["feed"] = f"error: {e}"

    # The quota is per UTC day and this automation runs four times a day, so
    # only the first run of the day spends it. Without this guard runs 2-4
    # would each ask for the next 100 URLs and hit the spent quota every time.
    if state.get("_bing_day") == today:
        report["submit"] = "quota already spent today"
        return report
    if not todo:
        report["submit"] = "nothing due"
        return report
    try:
        bing_call("SubmitUrlbatch", body={"siteUrl": SITE, "urlList": todo})
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:120]
        report["submit"] = f"HTTP {e.code}: {detail}"
        if "quota" in detail.lower():
            # Mark the day spent so the remaining runs do not retry into the
            # same error; the next UTC day picks up where this stopped.
            state["_bing_day"] = today
        return report
    except Exception as e:
        report["submit"] = f"error: {e}"
        return report
    for u in todo:
        state[f"bing:{u}"] = today
    state["_bing_day"] = today
    report["submit"] = f"submitted {len(todo)} urls for crawl"
    return report


def main() -> dict:
    print(f"IndexNow sweep for {HOST} at {time.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    try:
        status, _ = get(KEY_URL)
        if status != 200:
            raise RuntimeError(f"{KEY_URL} -> {status}")
    except Exception as e:
        raise RuntimeError(f"IndexNow key file not reachable ({e}); deploy first, then rerun")
    print(f"key file live: {KEY_URL}")

    urls, newest = sitemap_urls()
    if not urls:
        raise RuntimeError("sitemap returned no URLs")
    print(f"sitemap: {len(urls)} URL(s), newest lastmod {newest}")
    if newest != "unknown":
        age_days = (time.time() - time.mktime(time.strptime(newest, "%Y-%m-%d"))) / 86400
        if age_days > 7:
            print(f"WARNING: sitemap looks stale ({age_days:.0f} days old) - check the generator")

    state = load_state()
    first_run = not state

    # Running this often is only affordable if the common case costs one
    # request. A page can only be new or changed if the sitemap itself moved,
    # so compare its shape first and skip the per-page fingerprinting when it
    # has not. A weekly sweep still fingerprints everything, which catches an
    # edit that left the sitemap untouched.
    #
    # NOTE: the Bing half is NOT skipped here. Its SubmitUrlbatch quota is
    # 100/day and independent of content changes - the sitemap is 186 URLs, so
    # it needs two days to cover them and would never finish if it only ran on
    # a changed sitemap. That is exactly how Bing ended up with 0 crawled pages.
    sig = f"{len(urls)}|{newest}"
    unchanged = (not DRY and not first_run and time.gmtime().tm_wday != 6
                 and state.get("_sig") == sig)
    if unchanged:
        print("sitemap unchanged since the last sweep; IndexNow skipped, Bing quota still spent")
        bing = bing_push(state, [])
        print(f"Bing -> {json.dumps(bing)}")
        if not DRY:
            # bing_push mutated `state` in place with its "bing:*" marks and
            # the per-day flag; just stamp the signature and persist.
            state["_sig"] = sig
            save_state(state)
        return {"urls": len(urls), "new": 0, "changed": 0, "gone": 0,
                "submitted": 0, "status": "sitemap unchanged", "bing": bing}

    with ThreadPoolExecutor(max_workers=8) as pool:
        prints = list(pool.map(fingerprint, urls))

    current: dict[str, str] = {}
    for u, fp in zip(urls, prints):
        if fp is not None:
            current[u] = fp
    previous = {k: v for k, v in state.items() if not k.startswith("_")}

    changed = [u for u, fp in current.items() if previous.get(u) != fp]
    new = [u for u in current if u not in previous]
    gone = [u for u in previous if u not in current]

    weekly = time.gmtime().tm_wday == 6
    if first_run or weekly:
        targets = list(current)
        why = "first run" if first_run else "weekly full sweep"
    else:
        targets = changed
        why = "content changed"

    print(f"new {len(new)} | changed {len(changed)} | gone {len(gone)} | submitting {len(targets)} ({why})")

    result = "nothing changed, nothing submitted"
    if targets:
        if DRY:
            result = f"dry run, would submit {len(targets)}"
        else:
            result = str(submit(targets))
            print(f"IndexNow -> {result} for {len(targets)} URL(s)")

    # The Bing Webmaster half: register the sitemap and force a crawl of the
    # day's URLs. This is the piece that was missing, and the reason Bing had
    # crawled nothing despite an accepted sitemap.
    bing = bing_push(state, targets)
    print(f"Bing -> {json.dumps(bing)}")

    if not DRY:
        current["_sig"] = sig
        # bing_push wrote its own "bing:<url>" marks and the per-day quota flag
        # into `state`; fold them in so the next run does not re-spend the
        # 100/day quota on the same URLs.
        for k, v in state.items():
            if k.startswith("bing:") or k == "_bing_day":
                current[k] = v
        save_state(current)
    return {
        "urls": len(urls),
        "new": len(new),
        "changed": len(changed),
        "gone": len(gone),
        "submitted": len(targets),
        "status": result,
        "bing": bing,
    }


if __name__ == "__main__":
    try:
        report = main()
        print(f"DONE: {json.dumps(report)}")
        fire_callback("COMPLETED")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        fire_callback("FAILED", str(e))
        sys.exit(1)
