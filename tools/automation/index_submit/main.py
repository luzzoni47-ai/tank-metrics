#!/usr/bin/env python3
"""Daily IndexNow sweep for tankmetrics.in.

Deterministic on purpose: no LLM, no secrets. IndexNow is the only search
channel an agent can drive (Google Search Console needs a Google login), and it
reaches Bing, Yandex, Seznam and Naver in one POST. Bing is what backs ChatGPT
search and Copilot, so this is also the AI-answer-engine channel.

It fingerprints every URL in the live sitemap and submits only the pages whose
content actually changed, so a new tool or blog post is announced the same day
without re-pinging 123 unchanged URLs. First run and every Sunday submit the
whole sitemap as a safety net.

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
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HOST = "tankmetrics.in"
BASE = f"https://{HOST}"
SITEMAP = f"{BASE}/sitemap.xml"
KEY = "91ac4c920695a74eec34342ceb18acbf"
KEY_URL = f"{BASE}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"
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
    # so compare its shape first and stop here when it has not. A weekly sweep
    # still fingerprints everything, which catches an edit that left the
    # sitemap untouched.
    sig = f"{len(urls)}|{newest}"
    if not DRY and not first_run and time.gmtime().tm_wday != 6 and state.get("_sig") == sig:
        print("sitemap unchanged since the last sweep; nothing to do")
        return {"urls": len(urls), "new": 0, "changed": 0, "gone": 0,
                "submitted": 0, "status": "sitemap unchanged"}

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

    if not DRY:
        current["_sig"] = sig
        save_state(current)
    return {
        "urls": len(urls),
        "new": len(new),
        "changed": len(changed),
        "gone": len(gone),
        "submitted": len(targets),
        "status": result,
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
