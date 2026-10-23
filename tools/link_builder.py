#!/usr/bin/env python3
"""Prepare real backlink opportunities, honestly.

Sir asked for link building and "serious posting". The hard limit is the same
one that runs through this repo: an agent cannot hold a Quora, Reddit, Medium,
LinkedIn or Gmail account, and Sir cannot log into Google at all. So this tool
does the half an agent can do well and skips the half that would be spam.

Why there is no auto-scraper for prospects: I tried one. Bing's HTML results
answer "best business calculator tools" with a dictionary entry for the word
"best", and its RSS feed answers "free online gst calculator india" with Poki
games. Scraped prospect lists are noise, and emailing noise is what gets a
domain penalised. So the prospect list is CURATED - real places that publish
resource lists, accept a free tool submission, or take a directory listing.

What this does each run:

  1. Walk the curated list of real prospects (Indian startup/business
     directories, tool directories, resource pages that accept submissions).
  2. Check each one is live and reachable, so a dead prospect is dropped rather
     than emailed.
  3. Write submission-ready content per prospect: the title, the description,
     the URL and the tags each one asks for.
  4. Write the outreach email, and for the forum-shaped ones a draft post.
  5. Remember in the KV store which prospects were already prepared, so a daily
     run never repeats one.

Everything lands in tools/outreach/. Nothing is ever sent or submitted by the
agent - Sir submits or sends from his own accounts. An automation posting to
these on his behalf is spam, and the whole point is to NOT be spam.

    python3 tools/link_builder.py              # prepare the next batch
    python3 tools/link_builder.py --dry-run    # list, write nothing
    python3 tools/link_builder.py --top 3      # prepare the next 3
    python3 tools/link_builder.py --check      # just verify the prospects are live
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTREACH = ROOT / "tools" / "outreach"
HOST = "tankmetrics.in"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

_KV_TOKEN = os.environ.get("AUTOMATION_KV_TOKEN", "")
_KV_BASE = os.environ.get("AUTOMATION_API_URL", "").rstrip("/")
_STATE_KEY = "link_builder_prepared"

# One line each: why the site is a legitimate place to earn a link. "submit" is
# a free tool/product listing it accepts; "resource" is a page that lists tools
# and takes suggestions; "email" means an editor to write to and a post to draft.
# Anything that requires paying for a link is not here on purpose - paid links
# are a penalty risk, not a shortcut.
PROSPECTS: list[dict] = [
    {"name": "AlternativeTo", "url": "https://alternativeto.net/",
     "kind": "submit", "note": "Free crowd-sourced software alternatives directory; a web calculator can be listed."},
    {"name": "Product Hunt", "url": "https://www.producthunt.com/",
     "kind": "submit", "note": "Launch day listing; the one-time launch is where a tools site picks up its first real links."},
    {"name": "Hacker News Show HN", "url": "https://news.ycombinator.com/show",
     "kind": "submit", "note": "Show HN post for a free tool; technical audience, genuine links if the tool is good."},
    {"name": "BetaList", "url": "https://betalist.com/",
     "kind": "submit", "note": "Free listing for new web products."},
    {"name": "Indie Hackers", "url": "https://www.indiehackers.com/",
     "kind": "submit", "note": "Products section lists small tools; the community links out to useful free ones."},
    {"name": "Crunchbase", "url": "https://www.crunchbase.com/",
     "kind": "submit", "note": "Company profile; a legitimate nofollow brand link and a real signal of existence."},
    {"name": "Startup India", "url": "https://www.startupindia.gov.in/",
     "kind": "submit", "note": "Government startup registry, free to register; an Indian-audience brand link."},
    {"name": "IndiaMART", "url": "https://www.indiamart.com/",
     "kind": "submit", "note": "Indian business listing; useful for brand presence in Indian search."},
    {"name": "Wikipedia external links", "url": "https://en.wikipedia.org/wiki/Calculator",
     "kind": "resource", "note": "Only if a genuine article cites the tool as a source - never spam it, it will be reverted."},
    {"name": "Indian personal finance blogs", "url": "https://www.google.com/search?q=indian+personal+finance+blog+guest+post",
     "kind": "email", "note": "Indian finance blogs that take guest posts or tool suggestions; write to the editor, do not mass-mail."},
    {"name": "Quora answers", "url": "https://www.quora.com/",
     "kind": "email", "note": "Agent drafts the answer, Sir posts it. Links here are nofollow but they send real readers."},
    {"name": "Reddit IndiaInvestments", "url": "https://www.reddit.com/r/IndiaInvestments/",
     "kind": "email", "note": "Draft only. Self-promotion rules are strict, so the answer must be useful on its own."},
]


def kv_available() -> bool:
    return bool(_KV_TOKEN and _KV_BASE)


def kv_get(key: str):
    if not kv_available():
        return None
    req = urllib.request.Request(
        f"{_KV_BASE}/v1/kv/{key}", headers={"Authorization": f"Bearer {_KV_TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read()).get("value")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def kv_set(key: str, value) -> None:
    if not kv_available():
        return
    req = urllib.request.Request(
        f"{_KV_BASE}/v1/kv/{key}", method="PUT",
        data=json.dumps({"value": value}).encode(),
        headers={"Authorization": f"Bearer {_KV_TOKEN}",
                 "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=20).read()


def reachable(url: str) -> str:
    """'live', 'blocked' or 'dead'.

    A 403 is not a dead prospect: AlternativeTo and Product Hunt block a plain
    scripted GET while working fine in a browser. Dropping them would quietly
    shrink the list to whatever does not have a bot filter. Only a DNS failure,
    a 404 or a 5xx means the prospect is really gone.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
        with urllib.request.urlopen(req, timeout=15) as r:
            return "live" if r.status < 400 else "blocked"
    except urllib.error.HTTPError as e:
        if e.code in (403, 405, 429):
            return "blocked"
        if e.code == 404 or e.code >= 500:
            return "dead"
        return "blocked"
    except Exception:
        return "dead"


def listing_content(p: dict) -> str:
    """Submission-ready copy, in the shape a directory form asks for."""
    return f"""# {p['name']} — submission content
# kind: {p['kind']}   url: {p['url']}
# {p['note']}

Name:        Tank Metrics
URL:         https://{HOST}
Tagline:     Free Indian business calculators — GST, EMI, margin, payroll and 100 more
Short desc:  Tank Metrics is a free set of 100+ calculators for Indian small
             businesses and founders. GST, loan EMI, profit margin, break-even,
             payroll, valuation multiples and more. No sign-up, runs in the
             browser, and every page shows the formula it uses.
Long desc:   Tank Metrics covers the numbers an Indian small business actually
             runs on: GST with and without tax, loan EMI and total interest,
             profit and operating margin, break-even, CAC and LTV, burn rate and
             runway, valuation multiples and payroll. Each calculator is a single
             page, works on a phone, needs no account, and states the formula so
             the answer can be checked by hand. It is free and ad-light.
Category:    Business Tools / Finance / Calculators
Tags:        calculator, gst, emi, finance, small business, india, free tool
Language:    English and Hinglish

---
AGENT-PREPARED — review and submit it yourself from your own account.
"""


def outreach_email(p: dict) -> str:
    return f"""To: editor at {p['name']} ({p['url']})
Subject: A free calculator tool for your readers

Hi,

I run Tank Metrics (https://{HOST}) — 100+ free calculators for Indian small
businesses: GST, loan EMI, profit margin, break-even, CAC/LTV, valuation
multiples. No sign-up, no paywall, and each page shows the formula it uses.

I thought it might fit {p['name']}: {p['note'].lower()}

Two pages that could be useful to your readers:
  - https://{HOST}/gst-calculator-tax-and-wealth-toolkit
  - https://{HOST}/loan-emi-calculator

If it is a fit, a link would be welcome. If not, no problem — and tell me if you
would rather not hear from me again and I will not.

Thanks,
<your name>
Tank Metrics

---
AGENT DRAFT — Sir sends this from his own address. An automation sending it
would be a mail blast, which is spam and puts the domain at risk.
"""


def post_draft(p: dict) -> str:
    return f"""# Draft post for {p['name']}
# kind: {p['kind']}   url: {p['url']}
# {p['note']}

# Rules this draft follows: the post must be useful with the link removed.
# Reddit and Quora both remove self-promotion that is only a link, so the answer
# below stands on its own and the link is one line at the end, not the point.

Title: How to work out GST on a price without a calculator app

Body:

The part that trips people up is which direction you are going.

If the price already includes GST and you want the tax inside it, divide by
(1 + rate). At 18%, a Rs 1,180 bill carries Rs 1,180 / 1.18 = Rs 1,000 of value
and Rs 180 of GST. If the price excludes GST and you want the tax on top,
multiply: Rs 1,000 x 0.18 = Rs 180.

The mistake is doing both. "Add GST" and "remove GST" are different operations,
and applying the wrong one to a bill-inclusive figure overstates the tax.

Two more that catch people out:
  - The rate applies to the taxable value, not the final amount. Once you have
    added tax, the tax is no longer 18% of the number you are looking at.
  - A 12% and an 18% line on one invoice must be worked out separately; you
    cannot average the rate and apply it once.

If you just want the number, I keep a free one at
https://{HOST}/gst-calculator-tax-and-wealth-toolkit — it does both directions and
shows the split.

---
AGENT DRAFT — Sir posts this himself from his own account.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true", help="only verify prospects are live")
    args = ap.parse_args()

    print(f"curated prospects: {len(PROSPECTS)}")

    if args.check:
        for p in PROSPECTS:
            print(f"  {reachable(p['url']).upper():7} {p['name']:40} {p['url']}")
        return 0

    prepared = set()
    if kv_available():
        prepared = set(kv_get(_STATE_KEY) or [])
    print(f"prepared in earlier runs: {len(prepared)}")

    todo = [p for p in PROSPECTS if p["name"] not in prepared][:args.top]
    print(f"this run: {len(todo)}")
    for p in todo:
        print(f"  [{p['kind']}] {p['name']}")

    if args.dry_run:
        return 0

    OUTREACH.mkdir(parents=True, exist_ok=True)
    written = []
    for p in todo:
        state = reachable(p["url"])
        if state == "dead":
            print(f"  skipped {p['name']}: dead")
            continue
        safe = re.sub(r"[^a-z0-9]+", "-", p["name"].lower()).strip("-")
        if p["kind"] == "submit":
            (OUTREACH / f"listing-{safe}.md").write_text(listing_content(p), encoding="utf-8")
            written.append(f"listing-{safe}.md")
        elif p["kind"] == "email":
            (OUTREACH / f"email-{safe}.md").write_text(outreach_email(p), encoding="utf-8")
            (OUTREACH / f"post-{safe}.md").write_text(post_draft(p), encoding="utf-8")
            written.append(f"email-{safe}.md + post-{safe}.md")
        else:  # resource
            (OUTREACH / f"email-{safe}.md").write_text(outreach_email(p), encoding="utf-8")
            written.append(f"email-{safe}.md")

    if written:
        kv_set(_STATE_KEY, sorted(prepared | {p["name"] for p in todo}))
    print(f"files written: {len(written)}")
    for w in written:
        print(f"  tools/outreach/{w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
