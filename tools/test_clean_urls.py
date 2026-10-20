#!/usr/bin/env python3
"""Verify the clean-URL contract against a running server.

Every clean path must answer 200 and every legacy .html path must answer a
permanent redirect to it. Run with a base URL:

    python3 tools/test_clean_urls.py http://localhost:8932
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP = json.loads((Path(__file__).parent / "url-map.json").read_text(encoding="utf-8"))


def status(base: str, path: str) -> tuple[int, str]:
    req = urllib.request.Request(base + path, method="GET")
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=20) as r:
            return r.status, r.headers.get("location", "")
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("location", "")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8932").rstrip("/")
    bad = []
    for clean, file in MAP.items():
        code, loc = status(base, clean)
        if code != 200:
            bad.append(f"{clean} -> {code} (expected 200)")
        code, loc = status(base, file)
        if code not in (301, 308):
            bad.append(f"{file} -> {code} (expected 301/308)")
        elif not loc.endswith(clean):
            bad.append(f"{file} -> {loc} (expected ...{clean})")

    print(f"clean paths checked: {len(MAP)}")
    if bad:
        print(f"FAIL: {len(bad)} problem(s)")
        for b in bad[:15]:
            print("  " + b)
        return 1
    print("ALL PASS: every clean URL serves 200 and every .html URL redirects to it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
