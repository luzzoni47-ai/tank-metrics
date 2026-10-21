#!/usr/bin/env python3
"""Tell the search engines about pages, through IndexNow.

Google Search Console needs a Google login, which only Sir has, so the agent
cannot drive it. IndexNow is the part that *is* automatable: one POST reaches
Bing, Yandex, Seznam and Naver, and Bing is what backs ChatGPT's search and
Copilot. For a site that wants to be found by AI answer engines as well as by
Google, that is the useful half.

The protocol needs a key file served from the site root, so the key lives in
`tools/indexnow_key.txt` and is copied to `public/<key>.txt` at run time. That
file MUST be live before submitting, or every engine answers 403.

    python3 tools/indexnow_submit.py                  # whole sitemap
    python3 tools/indexnow_submit.py /new-post /news  # just these paths
    python3 tools/indexnow_submit.py --file list.txt  # one URL/path per line
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "public" / "sitemap.xml"
KEY_FILE = ROOT / "tools" / "indexnow_key.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"
HOST = "tankmetrics.in"
BASE = f"https://{HOST}"
MAX_PER_REQUEST = 10000


def key() -> str:
    k = KEY_FILE.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[A-Za-z0-9-]{8,128}", k):
        raise SystemExit(f"bad IndexNow key in {KEY_FILE}")
    return k


def publish_key_file(k: str) -> None:
    (ROOT / "public" / f"{k}.txt").write_text(k + "\n", encoding="utf-8")


def sitemap_urls() -> list[str]:
    xml = SITEMAP.read_text(encoding="utf-8")
    return [u.strip() for u in re.findall(r"<loc>\s*(.*?)\s*</loc>", xml)]


def to_url(arg: str) -> str:
    if arg.startswith("http://") or arg.startswith("https://"):
        return arg
    return f"{BASE}/{arg.lstrip('/')}"


def collect(argv: list[str]) -> list[str]:
    if not argv:
        return sitemap_urls()
    if argv[0] == "--file":
        lines = Path(argv[1]).read_text(encoding="utf-8").splitlines()
        return [to_url(l.strip()) for l in lines if l.strip()]
    return [to_url(a) for a in argv]


def post(urls: list[str], k: str) -> int:
    body = json.dumps({
        "host": HOST,
        "key": k,
        "keyLocation": f"{BASE}/{k}.txt",
        "urlList": urls,
    }).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except urllib.error.URLError as e:
        print(f"  network error: {e.reason}")
        return 0


def main() -> int:
    k = key()
    publish_key_file(k)
    urls = collect(sys.argv[1:])
    if not urls:
        print("nothing to submit")
        return 1

    print(f"key file: public/{k}.txt")
    print(f"submitting {len(urls)} URL(s) to IndexNow")
    worst = 0
    for i in range(0, len(urls), MAX_PER_REQUEST):
        chunk = urls[i:i + MAX_PER_REQUEST]
        status = post(chunk, k)
        worst = max(worst, status)
        # 200 = accepted, 202 = accepted but key still being verified.
        note = {200: "accepted", 202: "accepted (key pending verification)",
                400: "bad request", 403: "key file not reachable - deploy first",
                422: "URLs do not belong to host", 429: "rate limited"}.get(status, "")
        print(f"  {len(chunk)} URL(s) -> HTTP {status} {note}")
    return 0 if worst in (200, 202) else 1


if __name__ == "__main__":
    sys.exit(main())
