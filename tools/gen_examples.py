#!/usr/bin/env python3
"""Build the worked example for every calculator page.

The numbers are not typed by hand — they come from running each calculator's
real COMPUTE function (see worked_examples.py), so a page can never quote a
figure the tool would not produce. This script only adds the human framing
around those numbers, then caches the result in tools/tool_examples.json, which
gen_tool_pages.py reads.

Re-run it whenever tools/calcs.json changes:
    python3 tools/gen_examples.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from worked_examples import DATA, evaluate, realistic_inputs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "tool_examples.json"

# Per-tool wording for the worked example. The category text assumes the tool at
# the centre of that category, which is wrong for a few tools that sit there for
# navigation (TAM/SAM/SOM is not an investment-return tool, for instance).
GUIDES = json.loads((ROOT / "tools" / "tool_guides.json").read_text(encoding="utf-8"))

# The worked-example framing is built per calculator, from that calculator's own
# inputs, description and formula. A shared per-category sentence repeated the
# same prose on every sibling page, which is the near-duplicate text Google drops.
# A guide may still override the framing with its own intro/outro.

# Hinglish ("hi") copy is generated here too so gen_tool_pages.py has something
# to render under the Hinglish tab. guides["hi"] holds the twin guide text.
HI_GUIDES = json.loads((ROOT / "tools" / "tool_guides_hinglish.json").read_text(encoding="utf-8"))


def _lead_sentence(text: str) -> str:
    """First sentence of a formula, trimmed — the specific hook for this tool."""
    text = (text or "").strip()
    if not text:
        return ""
    return text.split(". ")[0].rstrip(". ").strip()


def intro_for(c: dict, guides: dict) -> str:
    g = guides["calcs"].get(c["id"], {})
    if g.get("intro"):
        return g["intro"]
    return f"A realistic {c['name']} example, filled in below."


def outro_for(c: dict, guides: dict) -> str:
    g = guides["calcs"].get(c["id"], {})
    if g.get("outro"):
        return g["outro"]
    lead = _lead_sentence(g.get("formula"))
    if lead:
        return f"{c['name']} settles it with {lead}. Edit any input above."
    return f"{c['name']} recomputes as you type. Edit any input above."


def hi_intro_for(c: dict) -> str:
    hg = HI_GUIDES["calcs"].get(c["id"], {})
    if hg.get("hi_intro"):
        return hg["hi_intro"]
    return f"Ek realistic {c['name']} example, neeche bhara hua."


def hi_outro_for(c: dict) -> str:
    hg = HI_GUIDES["calcs"].get(c["id"], {})
    if hg.get("hi_outro"):
        return hg["hi_outro"]
    lead = _lead_sentence(hg.get("formula"))
    if lead:
        return f"{c['name']} ka formula: {lead}. Koi bhi field badlo."
    return f"{c['name']} type karte hi update ho jaata hai. Koi bhi field badlo."


def main() -> None:
    results = evaluate(None)
    calcs = {c["id"]: c for c in DATA["calcs"]}
    out: dict[str, dict] = {}

    for cid, res in results.items():
        c = calcs[cid]
        rows = res.get("rows") or []
        if not rows or res.get("error"):
            continue
        inputs = realistic_inputs(c)
        labels = {i["k"]: i for i in c["inputs"]}
        shown_inputs = {}
        for key, val in inputs.items():
            label = labels[key]["l"]
            unit = labels[key].get("u", "")
            shown_inputs[label] = f"{val} {unit}".strip()
        out[cid] = {
            "inputs": shown_inputs,
            "rows": [{"l": r["l"], "v": r["v"]} for r in rows],
            "intro": intro_for(c, GUIDES),
            "outro": outro_for(c, GUIDES),
            "hi_intro": hi_intro_for(c),
            "hi_outro": hi_outro_for(c),
        }

    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(out)} worked examples to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
