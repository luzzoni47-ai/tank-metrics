#!/usr/bin/env python3
"""Copy the shared calculator helpers from calcs.json into public/site/index.html.

The home page is hand-maintained, but its helpers must stay identical to the
block tools/calcs.json injects into the 101 tool pages. Keeping one source stops
the two from drifting, which is how a fixed parser could ship to the tool pages
while the home page silently kept the old one.

Usage: python3 tools/sync_helpers.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HELPERS = json.loads((ROOT / "tools" / "calcs.json").read_text(encoding="utf-8"))["helpers"]
INDEX = ROOT / "public" / "site" / "index.html"

START = "function parseAmount(v){"
VAL = "function val(e,t){"
VAL_END = "return isNaN(a)?0:a}"

block = HELPERS[HELPERS.find(START):HELPERS.find("function inr(e){")]
assert block.startswith(START) and len(block) > 100, "helpers block not found in calcs.json"

text = INDEX.read_text(encoding="utf-8")
i = text.find(START)
v = text.find(VAL, i)
v_end = text.find(VAL_END, v) + len(VAL_END)
assert 0 < i < v < v_end, "could not locate the helper block in index.html"
INDEX.write_text(text[:i] + block + text[v_end:])
print(f"synced {len(block)} bytes of helpers into index.html")
