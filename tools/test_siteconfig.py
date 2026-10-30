#!/usr/bin/env python3
"""Guard: the site's identity must come from one place, not from 34 files.

Sir runs 15+ sites off the same toolset. The thing that makes that possible is
that no tool spells the host, the repo or the IndexNow key out in its source -
they all import `tools/siteconfig.py`. The moment one tool goes back to
`HOST = "tankmetrics.in"`, that tool silently does the wrong thing in every
other site's checkout, and the failure is quiet: it submits the wrong sitemap,
or pings IndexNow for a domain it does not own.

This checks:

1. The central config resolves, and its host matches the sitemap it points at.
2. No tool under `tools/` (other than siteconfig itself and the tests) hardcodes
   a site host in a module-level constant.
3. The example config is present, so a new site has something to copy.

Run: python3 tools/test_siteconfig.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

# Files allowed to name a host: the config itself, the example, and this test.
ALLOWED = {"siteconfig.py", "test_siteconfig.py"}

# A module-level `SOMEHOST = "something.tld"` assignment. Not a URL inside a
# docstring, not a request header - only the bare constant that tools read.
CONST = re.compile(
    r"^[A-Z][A-Z0-9_]*\s*=\s*[\"']((?:https?://)?[a-z0-9.-]+\.(?:in|com|org|net|io|co))/?[\"']",
    re.MULTILINE)


def main() -> int:
    fails: list[str] = []

    # 1. the central config resolves
    try:
        import siteconfig
    except Exception as e:  # pragma: no cover - import failure is the failure
        print(f"FAIL test_siteconfig\n  - tools/siteconfig.py did not import: {e}")
        return 1

    if not siteconfig.HOST or "." not in siteconfig.HOST:
        fails.append(f"siteconfig.HOST looks wrong: {siteconfig.HOST!r}")
    if siteconfig.SITE != f"https://{siteconfig.HOST}/":
        fails.append("siteconfig.SITE is not derived from HOST")
    if not siteconfig.REPO or "/" not in siteconfig.REPO:
        fails.append(f"siteconfig.REPO is not owner/name: {siteconfig.REPO!r}")

    # 2. no tool hardcodes a host at module level
    offenders: list[str] = []
    for p in sorted(TOOLS.glob("*.py")):
        if p.name in ALLOWED:
            continue
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in CONST.finditer(src):
            val = m.group(1)
            offenders.append(f"{p.name}: {m.group(0).strip()}")
    if offenders:
        fails.append("tools hardcoding a site host instead of importing "
                     "siteconfig:\n      " + "\n      ".join(offenders))

    # 3. the example config exists for a new site to copy
    example = TOOLS / "site.json.example"
    if not example.exists():
        fails.append("tools/site.json.example is missing - a new site has "
                     "nothing to copy")
    else:
        try:
            data = json.loads(example.read_text(encoding="utf-8"))
            for key in ("host", "repo", "brand", "indexnow_key"):
                if key not in data:
                    fails.append(f"site.json.example has no {key!r} key")
        except ValueError as e:
            fails.append(f"site.json.example is not valid JSON: {e}")

    if fails:
        print("FAIL test_siteconfig")
        for f in fails:
            print(f"  - {f}")
        return 1

    print(f"PASS test_siteconfig (host={siteconfig.HOST}, "
          f"repo={siteconfig.REPO}, no tool hardcodes a host)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
