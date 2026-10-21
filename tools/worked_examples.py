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


def realistic_inputs(calc: dict) -> dict[str, str]:
    """A believable set of numbers for one calculator.

    Amounts are in rupees and stay in the range a small Indian business would
    actually type, so the example reads like a real order rather than a
    round-number placeholder.
    """
    out: dict[str, str] = {}
    rupees = ["450000", "180000", "95000", "60000"]
    i = 0
    for inp in calc["inputs"]:
        key = inp["k"].lower()
        kind = inp.get("type", "number")
        unit = inp.get("u", "")
        if kind == "date":
            out[inp["k"]] = "1995-06-15"
        elif kind == "text":
            out[inp["k"]] = "Rahul"
        elif "%" in unit or any(w in key for w in ("pct", "rate", "margin", "roi", "disc", "comm", "rto")):
            out[inp["k"]] = "18"
        elif any(w in key for w in ("month", "tenure", "period")):
            out[inp["k"]] = "24"
        elif any(w in key for w in ("year", "yr")):
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
