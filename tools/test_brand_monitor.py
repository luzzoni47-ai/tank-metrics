#!/usr/bin/env python3
"""Guard the brand monitor.

The danger here is not a missed mention, it is a false one. If the classifier
ever calls tankmetrics.com or BattleMetrics "about us", Sir reads the report and
believes a stranger wrote about him. These checks pin that behaviour down.

    python3 tools/test_brand_monitor.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "brand_monitor", ROOT / "tools" / "brand_monitor.py")
bm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bm)

FAILURES: list[str] = []


def check(name: str, got, want) -> None:
    if got != want:
        FAILURES.append(f"{name}: got {got!r}, want {want!r}")


# --- classification: the whole point of the report --------------------------

check("our own page is OURS",
      bm.classify({"url": "https://tankmetrics.in/blog"}),
      "OURS")

check("a namesake sharing the word is NAMESAKE",
      bm.classify({"url": "https://tankmetrics.com/"}),
      "NAMESAKE")

check("BattleMetrics is NAMESAKE, never OURS",
      bm.classify({"url": "https://www.battlemetrics.com/"}),
      "NAMESAKE")

check("a stranger linking to us is LINKED",
      bm.classify({"url": "https://someblog.example/post",
                   "title": "Best calculators - see tankmetrics.in"}),
      "LINKED")

check("www of our own host is still OURS",
      bm.classify({"url": "https://www.tankmetrics.in/news"}),
      "OURS")

check("our own Instagram account is OURS, not a stranger",
      bm.classify({"url": "https://www.instagram.com/tankmetrics.in/"}),
      "OURS")

check("a different Instagram account is not ours",
      bm.classify({"url": "https://www.instagram.com/someoneelse/"}),
      "NAMESAKE")

# --- the noise filter -------------------------------------------------------

check("an unrelated engine result is dropped",
      bm.brand_mentioned({"url": "https://www.nba.com/schedule",
                          "title": "NBA Schedule"}),
      False)

check("a real namesake survives the filter",
      bm.brand_mentioned({"url": "https://tankmetrics.com/",
                          "title": "TankMetrics"}),
      True)

check("a phrase mention survives the filter",
      bm.brand_mentioned({"url": "https://blog.example/x",
                          "title": "I tried Tank Metrics for GST"}),
      True)

# --- dedupe keeps one row per URL ------------------------------------------

deduped = bm.dedupe([
    {"url": "https://tankmetrics.in/", "title": "a", "source": "Bing"},
    {"url": "https://tankmetrics.in/", "title": "a", "source": "DuckDuckGo"},
    {"url": "https://tankmetrics.com/", "title": "b", "source": "Bing"},
])
check("duplicate URLs collapse", len(deduped), 2)

# --- the report must never claim a namesake is about us ---------------------

report = bm.render(
    [{"url": "https://tankmetrics.com/", "title": "TankMetrics",
      "source": "Bing", "found_by": '"tankmetrics"', "kind": "NAMESAKE"},
     {"url": "https://tankmetrics.in/", "title": "Tank Metrics",
      "source": "Bing", "found_by": '"tankmetrics"', "kind": "OURS"}],
    {"https://tankmetrics.com/", "https://tankmetrics.in/"}, show_all=True)

# The "does our own site rank for its name" question must be answered even when
# every mention is old, so it reads the full hit list, not the new-only slice.
quiet = bm.render(
    [{"url": "https://tankmetrics.in/blog", "title": "Tank Metrics Blog",
      "source": "Bing", "found_by": '"tank metrics"', "kind": "OURS"}],
    set(), show_all=False)
if "Our own pages and accounts in search" not in quiet:
    FAILURES.append("the report does not answer whether our own site appears")
if "tankmetrics.in/blog" not in quiet:
    FAILURES.append("a known self-hit is missing from the self-presence list")
if "None of these sources returned a tankmetrics.in page" not in bm.render(
        [{"url": "https://tankmetrics.com/", "title": "TankMetrics",
          "source": "Bing", "found_by": '"tankmetrics"', "kind": "NAMESAKE"}],
        {"https://tankmetrics.com/"}, show_all=False):
    FAILURES.append("a run with no self-hits must say so plainly")

if "Namesakes (not us)" not in report:
    FAILURES.append("the report does not separate namesakes")
# The namesake must sit under the namesake heading, not under About us.
if "## About us" not in report:
    FAILURES.append("the report has no 'About us' section")
else:
    about = report.split("## About us", 1)[1]
    for stop in ("## Others linking to us", "## Namesakes (not us)"):
        about = about.split(stop, 1)[0]
    if "tankmetrics.com" in about:
        FAILURES.append("a namesake is listed under 'About us'")

# --- it must never post anywhere -------------------------------------------

src = (ROOT / "tools" / "brand_monitor.py").read_text(encoding="utf-8")
for bad in ("chat.postMessage", "api/comment", "submit_post", "smtplib",
            "sendmail", "/api/v1/comments", "oauth"):
    if bad in src:
        FAILURES.append(f"brand_monitor.py contains {bad!r} - it must only read")

if FAILURES:
    print(f"FAIL: {len(FAILURES)} problem(s)")
    for f in FAILURES:
        print("  " + f)
    sys.exit(1)

print("ALL PASS: our pages, real citations and namesakes are told apart, "
      "and the monitor never posts")
