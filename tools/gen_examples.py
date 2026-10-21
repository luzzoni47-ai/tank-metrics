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

# How to introduce the example, per category. {name} is the calculator name.
INTRO = {
    "everyday": "Say you want a quick answer without opening a spreadsheet. Here is the same calculation the tool does above, with one set of numbers.",
    "profit": "Take a business with a year of trading behind it. Here is what {name} reports for those figures.",
    "val": "Imagine a founder and an investor talking numbers. Here is what this deal looks like once {name} works it through.",
    "cust": "Consider a small online business spending on ads. Here is what {name} says about the customers that spend brings in.",
    "growth": "Picture a business six months into trading. Here is what {name} shows about where it is heading.",
    "pricing": "Take one product with one price. Here is what {name} shows once every cost is counted.",
    "ops": "Consider one hire or one freelancer. Here is what {name} says that really costs.",
    "investor": "Take an investment held for a few years. Here is what {name} reports at the end.",
    "bonus": "Put a real pitch into the check. Here is how the numbers score.",
    "agency": "Take an agency running a campaign for a client. Here is what {name} shows.",
    "realestate": "Take one property. Here is what {name} works out for it.",
    "taxwealth": "Take one investment or one salary. Here is what {name} projects.",
    "dailyfun": "Enter a normal set of details. Here is what {name} returns.",
}

# What the result means, per category. {first} is the first result label.
OUTRO = {
    "everyday": "Change any input above and the answer updates as you type. Nothing is sent anywhere — the arithmetic happens in your browser.",
    "profit": "The margin is the number to watch. A high revenue with a thin margin leaves little room for a bad month, a discount war or a late payment.",
    "val": "Read the valuation together with the stake, never on its own. A big valuation with a big stake given away can leave a founder with less than a smaller deal would have.",
    "cust": "These are the numbers investors ask about first. If the cost of winning a customer is close to what that customer is worth, growth burns cash instead of creating it.",
    "growth": "Growth figures are only useful next to a cash figure. A business can grow quickly and still run out of money, which is what the runway number is there to catch.",
    "pricing": "The selling price is a decision, not a fact. Work backwards from the margin you need rather than adding costs on top of a price you already picked.",
    "ops": "The salary is never the whole cost of a hire. Budget for the full figure, not the number you agreed in the interview.",
    "investor": "Compare the multiple against the years it took. A 3x return over ten years is a very different outcome from a 3x return over three.",
    "bonus": "Treat the score as a list of questions, not a verdict. Each weak number is something an investor will ask about, so have an answer ready.",
    "agency": "Agency economics turn on utilisation and churn. A full team on low-value work and a steady leak of clients will undo a healthy-looking margin.",
    "realestate": "Property numbers move with the local market, so treat this as a starting point and check the rate for your own city and locality.",
    "taxwealth": "These are estimates, not guarantees. Rates change, returns vary, and tax treatment depends on your own situation — confirm anything large with a professional.",
    "dailyfun": "This one is for fun. Enjoy the answer, and do not make any real decision on the strength of it.",
}

# Categories whose example numbers need a different, non-rupee framing.
SKIP_AMOUNT_CATEGORIES = {"dailyfun"}


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
        g = GUIDES["calcs"].get(cid, {})
        out[cid] = {
            "inputs": shown_inputs,
            "rows": [{"l": r["l"], "v": r["v"]} for r in rows],
            "intro": g.get("intro") or INTRO.get(c["cat"], INTRO["everyday"]).replace("{name}", c["name"]),
            "outro": g.get("outro") or OUTRO.get(c["cat"], OUTRO["everyday"]),
        }

    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(out)} worked examples to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
