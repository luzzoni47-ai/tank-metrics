"""Guards the service-worker version stamp.

The service worker serves CSS/JS cache-first, so a stylesheet or script edit
only reaches a returning visitor if sw.js changes too. sw.js only re-installs
when its bytes change, and its VERSION must therefore track the shell assets,
not the sitemap. The bug this guards: a CSS-only fix (the pager restyle) never
reached a visitor because VERSION was derived from the sitemap, which had not
moved, so the old stylesheet was served from cache forever.

Checks:
  - sw.js carries a VERSION of the expected shape;
  - VERSION equals the hash of the shell assets (i.e. gen_updates.py was run);
  - sw.js is NOT itself part of that hash, or stamping it would never settle.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SW = ROOT / "public" / "sw.js"
SHELL_ASSETS = (
    "public/site/style.css",
    "public/site/pagination.js",
    "public/site/pwa.js",
    "public/site/manifest.webmanifest",
)


def expected_version() -> str:
    h = hashlib.sha256()
    for rel in SHELL_ASSETS:
        p = ROOT / rel
        if p.exists():
            h.update(p.read_bytes())
    return "tm-" + h.hexdigest()[:10]


def main() -> int:
    fails = []
    text = SW.read_text(encoding="utf-8")
    m = re.search(r'const VERSION = "([^"]*)";', text)
    if not m:
        print("FAIL: sw.js has no `const VERSION` line")
        return 1
    got = m.group(1)
    want = expected_version()
    if got != want:
        fails.append(
            f"sw.js VERSION is {got!r}, expected {want!r} "
            f"(run tools/gen_updates.py after changing a shell asset)"
        )
    if "sw.js" in "".join(SHELL_ASSETS):
        fails.append("sw.js must not be in SHELL_ASSETS (self-referential hash)")
    # The version must not be the sitemap digest any more: that was the bug.
    if not got.startswith("tm-"):
        fails.append(f"VERSION {got!r} does not look like a tm- asset stamp")

    if fails:
        for f in fails:
            print("FAIL:", f)
        return 1
    print(f"ALL PASS: sw.js VERSION {got} tracks the shell assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
