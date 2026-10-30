#!/usr/bin/env python3
"""Daily Bing Webmaster run: spend the day's submission quota, then report.

The Bing API allows 100 submitted URLs per day. The sitemap is 176 URLs and
grows, so one run cannot cover it; this automation runs daily and `tools/bing.py`
keeps the record of what has already gone, which is why it converges instead of
re-sending the same first 100 pages forever.

IndexNow already announces changed pages, so this run is not a duplicate: it is
the only channel that also READS back what Bing did with them (`stats`, `pages`).

Needs BING_API_KEY in the environment. The key is never written to disk - this
repository is public.

    python3 main.py            # submit the day's quota, then report
    python3 main.py --dry-run  # report only
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BING = ROOT / "tools" / "bing.py"
DRY = "--dry-run" in sys.argv


def fire_callback(status: str, error: str | None = None) -> None:
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


def run(*args: str) -> str:
    out = subprocess.run([sys.executable, str(BING), *args],
                         capture_output=True, text=True, timeout=600)
    if out.returncode != 0:
        raise RuntimeError(f"bing.py {' '.join(args)} failed: {out.stderr.strip()[:300]}")
    return out.stdout.strip()


def main() -> dict:
    if not os.environ.get("BING_API_KEY", "").strip():
        raise RuntimeError("BING_API_KEY is not set")

    sites = run("sites")
    if "verified" not in sites:
        raise RuntimeError(f"tankmetrics.in is not verified on Bing: {sites}")

    report: dict = {"site": "tankmetrics.in", "verified": True}

    if DRY:
        report["feed"] = "dry run"
        report["submit"] = "dry run"
    else:
        # The feed costs no quota and is what makes Bing crawl on its own, so it
        # goes first and is redone every run - it is idempotent.
        report["feed"] = run("feed").replace("\n", " | ")
        report["submit"] = run("submit").replace("\n", " | ")

    # Query data only exists once Bing has served impressions, so an empty
    # answer is the normal state for a new property and not an error.
    try:
        report["queries"] = run("stats", "28").replace("\n", " | ")
    except RuntimeError as e:
        report["queries"] = f"unavailable: {e}"
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
