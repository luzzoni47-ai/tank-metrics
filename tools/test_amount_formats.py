#!/usr/bin/env python3
"""Guards the number formats every calculator accepts.

Sir asked for "1 Crore", "5 Lakh", "10K", "1M" and "3 Million" to be accepted
everywhere a number is expected. Two things have to hold, and both have failed
silently before:

1. parseAmount() must map every format to the right value. It lives once, in
   tools/calcs.json under "helpers", and is copied into index.html and all 101
   tool pages, so a wrong entry ships to every calculator at once.
2. The amount fields must not be `type="number"`. A native number input refuses
   the letter that makes "1 Crore" mean anything, so the feature would be
   invisible even with parseAmount correct.

This runs the real helper through node and checks the generated markup.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
DATA = json.loads((ROOT / "tools" / "calcs.json").read_text(encoding="utf-8"))

CASES = {
    # Sir's own examples, verbatim.
    "1 Lakh": 100_000, "2 Lakh": 200_000, "5 Lakh": 500_000, "1K": 1_000,
    "10K": 10_000, "1 Crore": 10_000_000, "1 Million": 1_000_000,
    "10 Million": 10_000_000, "20 Million": 20_000_000,
    "Rs. 10000": 10_000, "10000": 10_000, "1000000": 1_000_000,
    # Spellings and separators people actually type.
    "1M": 1_000_000, "1 m": 1_000_000, "3 Million": 3_000_000,
    "1cr": 10_000_000, "2.5 lakh": 250_000, "1,00,000": 100_000,
    "10 k": 10_000, "1B": 1_000_000_000, "75000": 75_000,
    "1 thousand": 1_000, "-5K": -5_000, "12.5": 12.5, "2 CR": 20_000_000,
    "5 Lac": 500_000, "Rs 1 Lakh": 100_000, "INR 5 lakh": 500_000,
    "10000 rupees": 10_000, "1 Crore only": 10_000_000,
    "1 crore 50 lakh": 15_000_000, "1 crore 50 lakh rupees": 15_000_000,
    # Hinglish spellings of crore and lakh - Sir types "karod" and "lekh".
    "1 karod": 10_000_000, "1 kror": 10_000_000, "1 krod": 10_000_000,
    "5 karod": 50_000_000, "2.5 karod": 25_000_000, "1 cror": 10_000_000,
    "1 lekh": 100_000, "10 lekh": 1_000_000, "1 karod 50 lekh": 15_000_000,
    "1 arab": 1_000_000_000, "1 hazar": 1_000, "1 lack": 100_000,
    # A small spelling mistake must still give the right answer.
    "1 milian": 1_000_000, "1 milion": 1_000_000, "1 millon": 1_000_000,
    "1 milyon": 1_000_000, "1 milon": 1_000_000, "1 bilion": 1_000_000_000,
    "1 corer": 10_000_000, "1 laakh": 100_000, "1 lakhh": 100_000,
    "1 hazr": 1_000, "1 thousnd": 1_000, "1 CR": 10_000_000,
    # Nonsense must stay 0 rather than become a confidently wrong number.
    "0": 0, "": None, "abc": None, "12abc": None, "lakh": None,
    "xyz": None, "qwerty": None, "zzz": None,
}


def check_parse() -> list:
    """parseAmount must agree with the expected value for every case."""
    script = (
        "const d=JSON.parse(require('fs').readFileSync('tools/calcs.json','utf8'));"
        "const api=new Function(d.helpers+';return {parseAmount};')();"
        f"const cases={json.dumps(CASES)};"
        "const out={};"
        "for(const k of Object.keys(cases)){const v=api.parseAmount(k);"
        "out[k]=(typeof v==='number'&&!isNaN(v))?v:null;}"
        "console.log(JSON.stringify(out));"
    )
    res = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        return [f"node failed to load parseAmount: {res.stderr.strip()[:200]}"]
    got = json.loads(res.stdout)
    failures = []
    for k, want in CASES.items():
        if got.get(k) != want:
            failures.append(f"parseAmount({k!r}) gave {got.get(k)!r}, expected {want!r}")
    return failures


def check_fields() -> list:
    """No amount field may be a native number input, and every page must carry
    the same helper, so the feature cannot be half-shipped."""
    failures = []
    for page in [PUBLIC / "site" / "index.html", *sorted((PUBLIC / "site" / "tools").glob("*.html"))]:
        text = page.read_text(encoding="utf-8", errors="replace")
        if "parseAmount" not in text:
            failures.append(f"{page.relative_to(PUBLIC)} has no parseAmount helper")
        # type="number" is allowed for a percentage or a month count, but an
        # amount field must accept words. Every field that carries a rupee unit
        # is checked, because those are the ones users type amounts into.
        for m in re.finditer(r'<input[^>]*>', text):
            tag = m.group(0)
            if 'data-unit="\u20b9"' not in tag:
                continue
            if 'type="number"' in tag:
                failures.append(f"{page.relative_to(PUBLIC)} has a rupee field as type=number: {tag[:90]}")
            # inputmode="decimal" opens a digits-only keypad on a phone, so the
            # user cannot type the "Lakh" in "5 Lakh" at all. It must be absent
            # from an amount field, not just from the type attribute.
            if "inputmode=\"decimal\"" in tag:
                failures.append(f"{page.relative_to(PUBLIC)} rupee field has inputmode=decimal (letters untypable on mobile): {tag[:90]}")
    return failures


def main() -> int:
    failures = check_parse() + check_fields()
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures[:20]:
            print("  -", f)
        return 1
    print(f"ALL PASS: parseAmount handles {len(CASES)} formats and no rupee field is type=number")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
