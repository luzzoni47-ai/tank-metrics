#!/usr/bin/env python3
"""Reject a weak per-calculator guide before it can ship.

The de-duplication work only counts if the replacement copy is genuinely
different from the category template. A guide that is a paraphrase of the
template, or two sentences long, moves the overlap number and fools nobody -
Google still sees a near-duplicate. This checks the guide the moment it is
written, so the daily run cannot quietly add filler.

Rules, per guide in tool_guides.json:

  - has the four required fields: what, formula, when, mistakes
  - `what` is at least 220 characters (a real paragraph, not a caption)
  - `formula` is at least 80 characters
  - `when` and `mistakes` each hold at least 3 items
  - no `{name}` / `{desc}` placeholder left in a hand-written guide (those belong
    to the category template; in a guide they mean the text was not customised)
  - no `$` anywhere, and no "million" - the site is ₹ Lakhs and Crores only
  - the `what` text is at least 40% different (by 5-word shingles) from the
    category template it is replacing, so a light edit does not pass

The same fields are checked in tool_guides_hinglish.json, plus: no Devanagari
(the Hinglish house style is romanised) and no `$`.

Exit code is 1 if any guide fails, so it can gate a run. Missing guides are a
warning, not a failure - there are 86 to write and the count is reported.

    python3 tools/validate_guides.py          # report + gate
    python3 tools/validate_guides.py --ids a,b  # only these calcs
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"

WHAT_MIN = 220
FORMULA_MIN = 80
ITEMS_MIN = 3
MIN_DISTINCT = 0.40  # 1 - jaccard must be at least this
SHINGLE = 5
DEVANAGARI = re.compile(r"[\u0900-\u097F]")


def shingles(text: str) -> set[str]:
    w = text.split()
    return {" ".join(w[i:i + SHINGLE]) for i in range(max(0, len(w) - SHINGLE + 1))}


def similarity(a: str, b: str) -> float:
    sa, sb = shingles(a), shingles(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def cat_field(guides: dict, cat: str, field: str) -> str:
    c = guides["cats"].get(cat, {})
    return str(c.get(field, "")).replace("{name}", "").replace("{desc}", "")


def check_guide(cid: str, g: dict, cat: str, guides: dict, hinglish: bool) -> list[str]:
    bad: list[str] = []
    label = "HI" if hinglish else "EN"
    for field in ("what", "formula", "when", "mistakes"):
        if field not in g:
            bad.append(f"{cid} [{label}]: missing '{field}'")
    what = str(g.get("what", ""))
    formula = str(g.get("formula", ""))
    if len(what) < WHAT_MIN:
        bad.append(f"{cid} [{label}]: what is {len(what)} chars (need {WHAT_MIN}+)")
    if len(formula) < FORMULA_MIN:
        bad.append(f"{cid} [{label}]: formula is {len(formula)} chars (need {FORMULA_MIN}+)")
    for field in ("when", "mistakes"):
        items = g.get(field)
        if not isinstance(items, list) or len(items) < ITEMS_MIN:
            bad.append(f"{cid} [{label}]: '{field}' needs {ITEMS_MIN}+ items")
    joined = json.dumps(g, ensure_ascii=False)
    if "{name}" in joined or "{desc}" in joined:
        bad.append(f"{cid} [{label}]: placeholder left in a hand-written guide")
    if "$" in joined:
        bad.append(f"{cid} [{label}]: contains '$' (₹ only)")
    # "million" is fine as a contrast ("lakh, not million"); a figure like
    # "5 million" is the US style this site does not use.
    if not hinglish and re.search(r"\b\d[\d,.]*\s*million", joined, re.I):
        bad.append(f"{cid} [{label}]: quotes a figure in millions (use lakh/crore)")
    if hinglish and DEVANAGARI.search(joined):
        bad.append(f"{cid} [{label}]: Devanagari found (Hinglish is romanised)")
    # Must not be a light edit of the template it replaces. Compare like with
    # like: 'what' against the template's 'what', not against what+formula, or
    # the extra field dilutes the ratio and a copy slips through.
    for field, value in (("what", what), ("formula", formula)):
        tmpl = cat_field(guides, cat, field)
        if value and tmpl and similarity(value, tmpl) > (1 - MIN_DISTINCT):
            bad.append(f"{cid} [{label}]: {field} is too close to the {cat} template")
    return bad


def validate(ids: set[str] | None = None) -> tuple[list[str], int, int]:
    guides = json.loads((TOOLS / "tool_guides.json").read_text(encoding="utf-8"))
    hguides = json.loads((TOOLS / "tool_guides_hinglish.json").read_text(encoding="utf-8"))
    calcs = json.loads((TOOLS / "calcs.json").read_text(encoding="utf-8"))["calcs"]
    cat_of = {c["id"]: c["cat"] for c in calcs}

    problems: list[str] = []
    for cid, g in guides["calcs"].items():
        if ids and cid not in ids:
            continue
        problems += check_guide(cid, g, cat_of.get(cid, ""), guides, hinglish=False)
    for cid, g in hguides["calcs"].items():
        if ids and cid not in ids:
            continue
        problems += check_guide(cid, g, cat_of.get(cid, ""), hguides, hinglish=True)

    have_en = len(guides["calcs"])
    have_hi = len(hguides["calcs"])
    return problems, have_en, have_hi


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default="", help="comma-separated calc ids to check")
    args = ap.parse_args()
    ids = {x.strip() for x in args.ids.split(",") if x.strip()} or None

    problems, have_en, have_hi = validate(ids)
    total = len(json.loads((TOOLS / "calcs.json").read_text(encoding="utf-8"))["calcs"])
    print(f"hand-written guides: {have_en} EN, {have_hi} Hinglish, of {total} calculators")
    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("OK: every hand-written guide is complete and distinct")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
