#!/usr/bin/env python3
"""Evaluate every calculator with realistic inputs and print the results.

The tool pages carry a worked example, and it has to agree with what the page
actually computes. Rather than hand-copy numbers, this runs the real COMPUTE
function out of tools/calcs.json through node and prints the rows.

Usage:
    python3 tools/worked_examples.py            # all calculators, JSON
    python3 tools/worked_examples.py emi sip    # just these ids
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "tools" / "calcs.json").read_text(encoding="utf-8"))
RUNNER = Path(__file__).parent / "worked_examples.js"


# Calculators where the generic rules produce a silly example (a 12-month home
# loan, an 18% FD). Each entry lists the exact inputs a person would type.
OVERRIDES: dict[str, dict[str, str]] = {
    # Round, easy-to-follow numbers. The point of an example is that a reader
    # can check the arithmetic in their head, so avoid anything that needs a
    # calculator to follow.
    "emi": {"p": "3000000", "r": "8", "m": "240"},
    "homeemi": {"loan": "3000000", "rate": "8", "years": "20"},
    "compint": {"p": "100000", "r": "10", "t": "5", "n": "1"},
    "simpleint": {"p": "100000", "r": "10", "t": "5"},
    "sip": {"monthly": "10000", "rate": "12", "years": "10"},
    "ppf": {"annual": "100000", "rate": "7", "years": "15"},
    "fd": {"principal": "100000", "rate": "7", "years": "5", "frequency": "1"},
    "rd": {"monthly": "5000", "rate": "7", "months": "24"},
    "nps": {"monthly": "5000", "rate": "10", "years": "20"},
    "epf": {"employee": "5000", "employer": "5000", "rate": "8", "years": "20"},
    "gratuity": {"salary": "50000", "years": "10"},
    "incometax": {"income": "1000000", "deductions": "100000"},
    "hra": {"hra": "20000", "rent": "20000", "salary": "60000", "metro": "1"},
    "takehome": {"ctc": "1200000", "ded": "100000"},
    "gst": {"amt": "10000", "rate": "18"},
    "gst_taxwealth": {"amt": "10000", "discount": "10", "rate": "18"},
    # ₹10,000 of market, ₹6,000 sold — 60%, checkable in your head.
    "marketplace": {"sp": "10000", "comm": "10", "ship": "500", "other": "500"},
    "landed": {"mfg": "500", "pack": "50", "ship": "100", "other": "50"},
    "codrto": {"orders": "1000", "rto": "20", "lossper": "200"},
    "discountimpact": {"sp": "1000", "cp": "700", "disc": "10"},
    "mrpreverse": {"mrp": "1000", "retmargin": "20", "distmargin": "10"},
    "distmargin": {"mfg": "500", "dist": "600", "mrp": "1000"},
    "importduty": {"value": "100000", "duty": "20", "igst": "18"},
    "cac": {"spend": "100000", "cust": "200"},
    "ltv": {"aov": "1000", "freq": "4", "life": "3", "gm": "50"},
    "aov": {"rev": "100000", "orders": "200"},
    "roas": {"rev": "100000", "spend": "20000"},
    "saas": {"mrev": "100000", "users": "200"},
    "burn": {"cash": "1000000", "burn": "100000"},
    "runrate": {"lm": "100000"},
    "breakeven": {"fixed": "100000", "sp": "1000", "vc": "600"},
    "roi": {"profit": "100000", "inv": "1000000"},
    "impval": {"amt": "1000000", "eq": "10"},
    "prepost": {"pre": "9000000", "amt": "1000000"},
    "dilution": {"before": "100", "offered": "10"},
    "bmi": {"weight": "70", "height": "175"},
    "split": {"total": "1000", "people": "4"},
    "tip": {"bill": "1000", "tip": "10"},
    "simpledisc": {"price": "1000", "disc": "20"},
    "savegoal": {"goal": "1000000", "have": "100000", "monthly": "10000"},
    # 1 crore market, 10% reachable, 10% winnable — round at every step.
    "tam": {"tam": "10000000", "sampct": "10", "sompct": "10"},
    "numwords": {"n": "100000"},
    "rentalyield": {"rent": "20000", "price": "5000000"},
    "stampduty": {"value": "5000000", "stamp": "6", "registration": "1"},
    "downpayment": {"price": "5000000", "ltv": "80"},
    "propertyvalue": {"area": "1000", "rate": "5000"},
    "propertyroi": {"purchase": "5000000", "sale": "6000000", "rent": "20000", "years": "5"},
    "ctc": {"gross": "50000", "pf": "1800", "benefits": "2000"},
    "freelance": {"income": "100000", "hours": "5", "weeks": "4"},
    # Market share is the example the user asked for: 10,000 in the market,
    # 6,000 sold, so 60%.
    "marketshare": {"market": "10000", "sold": "6000"},
    # Two different names, so the pairing tools do not compare Rahul with Rahul.
    "lovefun": {"name1": "Rahul", "name2": "Priya"},
    "compatibility": {"name1": "Rahul", "name2": "Priya"},
    "babyname": {"name": "Aarav"},
    "numerology": {"name": "Aarav", "dob": "2019-08-14"},
    "agefun": {"dob": "1995-06-15"},
    "zodiac": {"dob": "1995-06-15"},
    "rashi": {"dob": "1995-06-15"},
    "luckynumber": {"dob": "1995-06-15"},
    "daysbetween": {"start": "2026-04-01", "end": "2026-10-21"},
}


def realistic_inputs(calc: dict) -> dict[str, str]:
    """A believable set of numbers for one calculator.

    Amounts are in rupees and stay in the range a small Indian business would
    actually type, so the example reads like a real order rather than a
    round-number placeholder.
    """
    if calc["id"] in OVERRIDES:
        return dict(OVERRIDES[calc["id"]])
    out: dict[str, str] = {}
    rupees = ["450000", "180000", "95000", "60000"]
    i = 0
    for inp in calc["inputs"]:
        key = inp["k"].lower()
        label = inp["l"].lower()
        hay = key + " " + label
        kind = inp.get("type", "number")
        unit = inp.get("u", "")
        if kind == "date":
            out[inp["k"]] = "1995-06-15"
        elif kind == "text":
            out[inp["k"]] = "Rahul"
        elif "%" in unit or any(w in hay for w in ("pct", "percent", "rate", "interest", "margin", "roi", "disc", "comm", "rto", "tax")):
            out[inp["k"]] = "18"
        elif any(w in hay for w in ("month", "tenure", "period")):
            out[inp["k"]] = "24"
        elif any(w in hay for w in ("year", "yr")):
            out[inp["k"]] = "5"
        elif key in ("people", "cust", "clients", "users", "orders", "clicks", "leads", "conversions", "hours", "available", "billable", "start", "end", "new", "lost", "freq", "life", "frequency", "n"):
            out[inp["k"]] = "12"
        elif unit == "₹":
            out[inp["k"]] = rupees[i % len(rupees)]
            i += 1
        else:
            out[inp["k"]] = "12"
    return out


def evaluate(ids: list[str] | None) -> dict:
    calcs = DATA["calcs"]
    if ids:
        calcs = [c for c in calcs if c["id"] in ids]
    req = {c["id"]: {"inputs": realistic_inputs(c)} for c in calcs}
    proc = subprocess.run(
        ["node", str(RUNNER)], input=json.dumps(req), capture_output=True,
        text=True, cwd=str(ROOT), timeout=120,
    )
    if proc.returncode != 0:
        raise SystemExit(f"node failed: {proc.stderr[:400]}")
    return json.loads(proc.stdout)


def main() -> None:
    ids = sys.argv[1:] or None
    print(json.dumps(evaluate(ids), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
