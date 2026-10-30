#!/usr/bin/env python3
"""One place that knows which site this checkout is.

Every tool in `tools/` was written for tankmetrics.in, and 34 of them spell the
host out in the source. That is fine for one site and fatal for fifteen: the
same crawler, the same IndexNow ping, the same Search Console client and the
same authority worker all have to run against a different domain, a different
repo and a different sitemap without being edited.

So the site's identity moves into `.openhands/site.json` (gitignored - a repo
does not need to publish its own host, and the IndexNow key is a credential).
The constants below keep tankmetrics.in as the fallback, so this module can be
introduced without changing the behaviour of anything that already works.

Copy `tools/site.json.example` to `.openhands/site.json` in a new site's repo
and every tool that imports this module follows.

    from siteconfig import HOST, SITE, REPO, INDEXNOW_KEY
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / ".openhands" / "site.json"

# tankmetrics.in - the values every tool used before this module existed.
_DEFAULT = {
    "host": "tankmetrics.in",
    "repo": "luzzoni47-ai/tank-metrics",
    "indexnow_key": "91ac4c920695a74eec34342ceb18acbf",
    "brand": "Tank Metrics",
    "bing_user_agent": "TankMetrics-Bing/1.0",
}


def _load() -> dict:
    """site.json merged over the defaults. A malformed file is not fatal - it
    falls back, because a typo in a config should not stop a scheduled run."""
    cfg = dict(_DEFAULT)
    try:
        if CONFIG.exists():
            data = json.loads(CONFIG.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                cfg.update({k: v for k, v in data.items() if v})
    except (OSError, ValueError):
        pass
    # An env var wins over the file: a scheduler can run the same checkout
    # against a staging host without editing a tracked file.
    cfg["host"] = os.environ.get("SITE_HOST", "").strip() or cfg["host"]
    cfg["repo"] = os.environ.get("SITE_REPO", "").strip() or cfg["repo"]
    return cfg


_cfg = _load()

HOST: str = _cfg["host"]
SITE: str = f"https://{HOST}/"
BASE: str = f"https://{HOST}"
REPO: str = _cfg["repo"]
BRAND: str = _cfg["brand"]
INDEXNOW_KEY: str = _cfg["indexnow_key"]
UA: str = f"{_cfg['bing_user_agent']} (+{BASE})"
SITEMAP: Path = ROOT / "public" / "sitemap.xml"


if __name__ == "__main__":
    print(f"config: {CONFIG}{'' if CONFIG.exists() else '  (absent - using defaults)'}")
    print(f"  host    {HOST}")
    print(f"  site    {SITE}")
    print(f"  repo    {REPO}")
    print(f"  brand   {BRAND}")
    print(f"  indexnow key set: {bool(INDEXNOW_KEY)}")
    print(f"  sitemap {SITEMAP} ({'present' if SITEMAP.exists() else 'MISSING'})")
