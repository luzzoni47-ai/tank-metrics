#!/usr/bin/env python3
"""List the calculator pages that still share a category template, worst first.

`content_uniqueness.py` measures the overlap; this says what to DO about it. 83
of 101 calculators have no guide of their own in `tool_guides.json`, so
`gen_tool_pages.py` renders the shared per-CATEGORY template for them and every
page in a category reads nearly the same. Google indexes one per cluster and
leaves the rest as "Crawled - currently not indexed". That is the indexing
blocker, and this is the worklist that clears it.

Ordering, highest impact first:

  1. Category size. One guide fixes a whole page, but working a big category
     first takes more pages out of one duplicate cluster.
  2. Whether the Hinglish guide already exists. A calc that has one is half
     written; finishing it is cheaper than starting from nothing.
  3. The page's own measured overlap, when `content_uniqueness.json` is present.

Output is a human report plus `tools/dedup_worklist.json`, which the daily
automation reads to pick its batch. Run it after `gen_tool_pages.py`, so the
overlap numbers are current.

    python3 tools/dedup_worklist.py            # report + write the worklist
    python3 tools/dedup_worklist.py --limit 12 # show only the next 12
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"

# A calculator with a guide shorter than this is treated as still templated: the
# category fallback and a real guide are easy to tell apart by length.
MIN_GUIDE_CHARS = 120


def load(name: str) -> dict:
    p = TOOLS / name
    if not p.exists():
        sys.exit(f"missing {p} - run tools/rebuild.sh first")
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="show only the first N")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    calcs = load("calcs.json")["calcs"]
    guides = load("tool_guides.json")["calcs"]
    hguides = load("tool_guides_hinglish.json")["calcs"]

    # Overlap per page, if the uniqueness run has happened.
    overlap: dict[str, float] = {}
    cu = TOOLS / "content_uniqueness.json"
    if cu.exists():
        data = json.loads(cu.read_text(encoding="utf-8"))
        for row in data.get("worst_pages", []):
            overlap[row["page"].rstrip("/").rsplit("/", 1)[-1]] = row["closest_overlap"]

    by_cat: dict[str, list[dict]] = collections.defaultdict(list)
    for c in calcs:
        by_cat[c["cat"]].append(c)

    # Category size is the first sort key, so a big cluster is worked first.
    cat_size = {cat: len(cs) for cat, cs in by_cat.items()}

    todo = []
    for c in calcs:
        g = guides.get(c["id"])
        hg = hguides.get(c["id"])
        has_en = bool(g) and len(json.dumps(g, ensure_ascii=False)) >= MIN_GUIDE_CHARS
        has_hi = bool(hg) and len(json.dumps(hg, ensure_ascii=False)) >= MIN_GUIDE_CHARS
        if has_en and has_hi:
            continue
        todo.append({
            "id": c["id"],
            "name": c["name"],
            "cat": c["cat"],
            "cat_size": cat_size[c["cat"]],
            "has_en": has_en,
            "has_hi": has_hi,
            "overlap": overlap.get(c["id"]),
        })

    # Sort: biggest category, then half-done pages, then measured overlap.
    todo.sort(key=lambda r: (-r["cat_size"], -int(r["has_hi"]), -(r["overlap"] or 0), r["id"]))

    done = len(calcs) - len(todo)
    data = {
        "total": len(calcs),
        "with_both_guides": done,
        "remaining": len(todo),
        "remaining_by_cat": dict(sorted(
            collections.Counter(r["cat"] for r in todo).items(),
            key=lambda kv: -kv[1])),
        "next": todo[:args.limit] if args.limit else todo,
    }
    (TOOLS / "dedup_worklist.json").write_text(
        json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")

    if args.quiet:
        print(f"remaining: {len(todo)} of {len(calcs)}")
        return 0

    print(f"calculators with a full guide (EN + Hinglish): {done} of {len(calcs)}")
    print(f"still on the category template: {len(todo)}")
    print()
    print("remaining by category:")
    for cat, n in data["remaining_by_cat"].items():
        print(f"  {n:>3}  {cat}  ({cat_size[cat]} total)")
    print()
    show = data["next"][:args.limit or 12]
    print(f"next up ({len(show)} of {len(todo)}):")
    for r in show:
        flags = []
        if r["has_en"]:
            flags.append("EN done")
        if r["has_hi"]:
            flags.append("HI done")
        ov = f"  overlap {r['overlap']:.0%}" if r["overlap"] else ""
        tail = f"  [{', '.join(flags)}]" if flags else ""
        print(f"  {r['id']:<22} {r['name']:<34} {r['cat']}{ov}{tail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
