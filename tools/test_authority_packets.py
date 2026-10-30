#!/usr/bin/env python3
"""Guard the authority packets: every venue must get its own copy.

The defect this exists for: `listing_packet()` used to return one generic blob
for every directory, so the Product Hunt, AlternativeTo and Show HN packets were
byte-identical. That is the single clearest tell of an automated submission, and
for Show HN it is wrong twice over - HN wants a plain technical sentence, not a
marketing tagline.

Two checks:

1. No two packets for the same day are byte-identical (excluding the header
   lines that name the prospect).
2. Every `submit`-kind prospect has a VENUE entry, so a new directory cannot be
   added to PROSPECTS and quietly inherit the generic fallback.

Run: python3 tools/test_authority_packets.py
"""
import hashlib
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "tools" / "automation" / "site_authority" / "main.py"


def load():
    spec = importlib.util.spec_from_file_location("authority_main", MAIN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def body(text: str) -> str:
    """The packet minus everything that is *meant* to differ per prospect.

    The H1 names the prospect, so it has to go too - otherwise every packet
    looks unique for the wrong reason and the guard passes on the exact defect
    it exists to catch.
    """
    keep = []
    for line in text.splitlines():
        if line.startswith("# "):
            continue
        if re.match(r"^\s*-\s*(prospect|kind|why this is legitimate|how to submit):", line):
            continue
        if re.match(r"^\s*(Name|URL|Title|Product|Vendor|Organization|Entity)\b", line):
            continue
        keep.append(line.strip())
    return "\n".join(l for l in keep if l)


def main() -> int:
    mod = load()
    fails: list[str] = []

    # 1. every submit-kind prospect must have a venue entry
    missing = [p["name"] for p in mod.PROSPECTS
               if p["kind"] == "submit" and p["name"] not in mod.VENUE]
    if missing:
        fails.append("submit prospects with no VENUE entry (would get the generic "
                     f"fallback): {', '.join(missing)}")

    # 2. no two same-day packets may be byte-identical in their body
    day = "2026-10-30"
    seen: dict[str, str] = {}
    dupes: list[str] = []
    for p in mod.PROSPECTS:
        if p["kind"] != "submit" or p["name"] not in mod.VENUE:
            continue
        path, content = mod.build_packet(p, mod.LINK_TARGETS[0], day)
        if not path:
            continue
        h = hashlib.sha256(body(content).encode()).hexdigest()[:12]
        if h in seen:
            dupes.append(f"{p['name']} is identical to {seen[h]}")
        else:
            seen[h] = p["name"]
    if dupes:
        fails.append("identical copy across venues: " + "; ".join(dupes))

    # 3. the Show HN packet must not read like a marketing tagline
    hn = next((p for p in mod.PROSPECTS if p["name"] == "Hacker News Show HN"), None)
    if hn:
        _, c = mod.build_packet(hn, mod.LINK_TARGETS[0], day)
        if "Show HN:" not in c:
            fails.append("the Show HN packet has no 'Show HN:' title")
        for banned in ("Tagline", "Best ", "#1 ", "revolutionary", "game-changing"):
            if banned in c:
                fails.append(f"the Show HN packet contains marketing language: {banned!r}")

    if fails:
        print("FAIL test_authority_packets")
        for f in fails:
            print(f"  - {f}")
        return 1

    print(f"PASS test_authority_packets "
          f"({len(mod.VENUE)} venues, all distinct, Show HN copy is technical)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
