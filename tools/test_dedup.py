#!/usr/bin/env python3
"""Prove the de-duplication guards catch the defects they exist for.

A guard that never fires is not a guard. This injects each defect the de-dup
work is meant to prevent into a copy of the guide files, and fails if
validate_guides.py does not flag it. It also proves the two bugs found on
2026-10-29 stay fixed:

  - a literal `{desc}` shipped on live calculator pages because hand-written
    Hinglish guides are returned as-is, without the template substitution the
    category fallback does;
  - a guide keyed `savingsgoal` when the calculator's id is `savegoal`, so the
    hand-written copy was dead data and the page used the template anyway.

    python3 tools/test_dedup.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import validate_guides as V  # noqa: E402

CALCS = json.loads((TOOLS / "calcs.json").read_text(encoding="utf-8"))["calcs"]
IDS = {c["id"] for c in CALCS}
EN = json.loads((TOOLS / "tool_guides.json").read_text(encoding="utf-8"))
HI = json.loads((TOOLS / "tool_guides_hinglish.json").read_text(encoding="utf-8"))

failures: list[str] = []


def expect(label: str, condition: bool) -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        failures.append(label)
        print(f"  FAIL {label}")


def check_with(guides: dict, hguides: dict) -> list[str]:
    """Run the validator against patched files in a temp dir."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "calcs.json").write_text(json.dumps({"calcs": CALCS}), encoding="utf-8")
        (d / "tool_guides.json").write_text(json.dumps(guides), encoding="utf-8")
        (d / "tool_guides_hinglish.json").write_text(json.dumps(hguides), encoding="utf-8")
        orig = V.TOOLS
        V.TOOLS = d
        try:
            problems, _, _ = V.validate()
        finally:
            V.TOOLS = orig
    return problems


def deep_copy(x):
    return json.loads(json.dumps(x))


print("baseline: the real guide files pass")
expect("clean files pass", check_with(EN, HI) == [])

print("\ninjected defects are caught")
# A 'what' that is just the category template with the name swapped in.
g = deep_copy(EN)
emi_cat = next(c["cat"] for c in CALCS if c["id"] == "emi")
tmpl = EN["cats"][emi_cat]["what"]
g["calcs"]["emi"]["what"] = tmpl.replace("{name}", "Loan EMI Calculator").replace("{desc}", "x")
expect("template copy is caught", any("too close" in p for p in check_with(g, HI)))

# Too short.
g = deep_copy(EN)
g["calcs"]["emi"]["what"] = "The EMI is the monthly payment on a loan."
expect("short what is caught", any("what is" in p for p in check_with(g, HI)))

# A leftover placeholder.
g = deep_copy(HI)
g["calcs"]["emi"]["what"] = g["calcs"]["emi"]["what"] + " {desc}"
expect("leftover {desc} is caught", any("placeholder" in p for p in check_with(EN, g)))

# A dollar sign.
g = deep_copy(EN)
g["calcs"]["emi"]["mistakes"][0] = "Assuming the rate is $fixed."
expect("$ is caught", any("'$'" in p for p in check_with(g, HI)))

# A US-style figure.
g = deep_copy(EN)
g["calcs"]["emi"]["what"] = g["calcs"]["emi"]["what"] + " A flat costs 2 million here."
expect("figure in millions is caught", any("millions" in p for p in check_with(g, HI)))

# Devanagari in Hinglish.
g = deep_copy(HI)
g["calcs"]["emi"]["what"] = g["calcs"]["emi"]["what"] + " यह एक टूल है।"
expect("Devanagari is caught", any("Devanagari" in p for p in check_with(EN, g)))

# Too few mistake items.
g = deep_copy(EN)
g["calcs"]["emi"]["mistakes"] = g["calcs"]["emi"]["mistakes"][:1]
expect("short list is caught", any("'mistakes'" in p for p in check_with(g, HI)))

print("\nthe 2026-10-29 bugs stay fixed")
# No guide key is orphaned from the calculator list.
orphans = [k for k in EN["calcs"] if k not in IDS] + [k for k in HI["calcs"] if k not in IDS]
expect("no orphaned guide ids", orphans == [])
expect("savegoal has a hand-written guide", "savegoal" in EN["calcs"] and "savegoal" in HI["calcs"])
# No literal placeholder in any hand-written guide.
# Only the hand-written guides, not the category templates, which are SUPPOSED
# to carry {name}/{desc} for the fallback to substitute.
blob = json.dumps(EN["calcs"], ensure_ascii=False) + json.dumps(HI["calcs"], ensure_ascii=False)
expect("no {desc}/{name} in any hand-written guide",
       "{desc}" not in blob and "{name}" not in blob)

print("\nbuilt pages carry no literal placeholder")
bad = []
for p in (ROOT / "public" / "site" / "tools").glob("*.html"):
    txt = p.read_text(encoding="utf-8", errors="replace")
    if "{desc}" in txt or "{name}" in txt:
        bad.append(p.name)
expect("no built page shows a template placeholder", bad == [])

print("\nevery calculator has a guide of its own")
# 48 of the 101 pages once fell back to a shared per-CATEGORY text, which is
# what made them near-duplicates and left them unindexed. A new calculator
# added without a guide would silently reintroduce that. Require full coverage.
missing_en = sorted(IDS - set(EN["calcs"]))
missing_hi = sorted(IDS - set(HI["calcs"]))
expect(f"all {len(IDS)} calculators have an English guide", missing_en == [])
expect(f"all {len(IDS)} calculators have a Hinglish guide", missing_hi == [])
if missing_en:
    print(f"       missing EN: {missing_en}")
if missing_hi:
    print(f"       missing HI: {missing_hi}")

# And prove the guard fires: drop a guide and confirm the check would catch it.
g = deep_copy(EN)
del g["calcs"]["emi"]
expect("a calculator without a guide is caught",
       sorted(IDS - set(g["calcs"])) == ["emi"])

print()
if failures:
    print(f"FAILED: {len(failures)} check(s)")
    for f in failures:
        print(f"  - {f}")
    raise SystemExit(1)
print("all de-dup guards hold")
