#!/usr/bin/env python3
"""Site authority worker for tankmetrics.in - deterministic, no LLM.

Sir asked for an automation that builds 1,000 links, 1,000 guest posts, 1,000
site submissions and 1,000 blog submissions a day, 24 hours a day, to reach
DA 90 and site authority 80+.

The honest answer is that no automation can do that, and an automation that
tried would destroy the site. Three reasons, and they are not opinions:

  1. There is no such thing as "1,000 site submissions a day". The free,
     legitimate directories that accept a listing number in the dozens, and
     each one takes a human review. Beyond those, "submission services" are
     link farms, and Google's spam policies name them explicitly.
  2. 1,000 guest posts a day does not exist at any price. A real guest post is
     an editor accepting a written article. The Indian finance blogs that take
     them publish a few posts a week.
  3. 1,000 links a day from a site with ~170 pages is the single clearest
     footprint Google's link-spam systems look for. The outcome is a manual
     action and deindexing, not authority. That is the opposite of the goal.

DA (Moz) and DR (Ahrefs) are third-party scores. They are not a Google ranking
factor, they cannot be bought legitimately, and they move over months, not
days. A DA 90 site is a decade-old site with tens of thousands of referring
domains. The only real path is: unique indexable content, genuine citations
earned one at a time, and time.

So this automation does the part that is real, and does it every run:

  1. Walks a curated registry of genuinely free, login-free places that accept
     a tool submission or a resource suggestion, and checks each is still live.
     A dead prospect is dropped, not emailed.
  2. Prepares submission packets up to a daily quota - a listing copy, an editor
     pitch, or a community answer, written for one real prospect and one real
     page on the site. Packets are committed to the repo so they persist, and a
     prospect is never prepared twice.
  3. Checks the citation profile: does anyone link to tankmetrics.in yet? It
     searches the free, login-free corners of the web and classifies each hit,
     because "tankmetrics.com" and BattleMetrics are not us.
  4. Reports what moved: packets prepared, citations found, prospects live.

It never posts, submits, emails or pays for a link. Sir sends and submits from
his own accounts. That is not a limitation of the automation, it is the whole
reason the links it finds are worth having.

    python3 main.py              # real run
    python3 main.py --dry-run    # report only, commit nothing
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date

HOST = "tankmetrics.in"
BASE = f"https://{HOST}"
REPO = "luzzoni47-ai/tank-metrics"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
DRY = "--dry-run" in sys.argv
DAILY_QUOTA = 3           # packets per day. Not 1,000: see the docstring.
LEDGER_PATH = "tools/outreach/authority/ledger.json"


# ------------------------------------------------------------------- plumbing

def get_secret(name: str) -> str:
    """A custom secret from the run environment or the automation secret store."""
    if os.environ.get(name):
        return os.environ[name].strip()
    url = os.environ.get("AGENT_SERVER_URL", "").rstrip("/")
    key = os.environ.get("SESSION_API_KEY") or os.environ.get("OH_SESSION_API_KEYS_0", "")
    if url:
        url = f"{url}/api/settings/secrets/{name}"
    else:
        api = os.environ["OPENHANDS_CLOUD_API_URL"].rstrip("/")
        url = f"{api}/api/v1/sandboxes/{os.environ['SANDBOX_ID']}/settings/secrets/{name}"
    with urllib.request.urlopen(
        urllib.request.Request(url, headers={"X-Session-API-Key": key}), timeout=20
    ) as r:
        return r.read().decode().strip()


def fire_callback(status: str = "COMPLETED", error: str | None = None) -> None:
    url = os.environ.get("AUTOMATION_CALLBACK_URL", "")
    if not url:
        return
    body = {"status": status, "run_id": os.environ.get("AUTOMATION_RUN_ID", "")}
    if error:
        body["error"] = error
    try:
        urllib.request.urlopen(urllib.request.Request(
            url, data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get('AUTOMATION_CALLBACK_API_KEY', '')}",
            }), timeout=20)
    except Exception as e:
        print(f"callback error: {e}")


_KV_TOKEN = os.environ.get("AUTOMATION_KV_TOKEN", "")
_KV_BASE = os.environ.get("AUTOMATION_API_URL", "").rstrip("/")
_STATE_KEY = "authority_state"


def kv_available() -> bool:
    return bool(_KV_TOKEN and _KV_BASE)


def _unwrap(v):
    """The KV API wraps every value in {"value": ...}; peel it off."""
    seen = 0
    while isinstance(v, dict) and set(v) == {"value"} and seen < 5:
        v = v["value"]
        seen += 1
    return v


def kv_get(key: str):
    if not kv_available():
        return None
    try:
        req = urllib.request.Request(
            f"{_KV_BASE}/v1/kv/{key}",
            headers={"Authorization": f"Bearer {_KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return _unwrap(json.loads(r.read()))
    except Exception:
        return None


def kv_set(key: str, value) -> None:
    if DRY or not kv_available():
        return
    try:
        req = urllib.request.Request(
            f"{_KV_BASE}/v1/kv/{key}", method="PUT",
            data=json.dumps(value).encode(),
            headers={"Authorization": f"Bearer {_KV_TOKEN}",
                     "Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20).read()
    except Exception as e:
        print(f"kv error: {e}")


# --------------------------------------------------------------- prospect set

# Real, free, login-free places that accept a tool listing or a resource
# suggestion. Nothing here charges for a link: a paid link is a penalty risk,
# not a shortcut, so it is deliberately absent.
PROSPECTS: list[dict] = [
    {"name": "AlternativeTo", "url": "https://alternativeto.net/", "kind": "submit",
     "note": "crowd-sourced software alternatives directory, free listing"},
    {"name": "Product Hunt", "url": "https://www.producthunt.com/", "kind": "submit",
     "note": "one-time launch listing; the first real links a tools site gets"},
    {"name": "Hacker News Show HN", "url": "https://news.ycombinator.com/show", "kind": "submit",
     "note": "Show HN for a free tool; technical audience"},
    {"name": "BetaList", "url": "https://betalist.com/", "kind": "submit",
     "note": "free listing for new web products"},
    {"name": "Indie Hackers", "url": "https://www.indiehackers.com/", "kind": "submit",
     "note": "products section lists small tools"},
    {"name": "Crunchbase", "url": "https://www.crunchbase.com/", "kind": "submit",
     "note": "company profile; a nofollow brand link and a real existence signal"},
    {"name": "Startup India", "url": "https://www.startupindia.gov.in/", "kind": "submit",
     "note": "government startup registry, free, Indian audience"},
    {"name": "IndiaMART", "url": "https://www.indiamart.com/", "kind": "submit",
     "note": "Indian business listing, brand presence in Indian search"},
    {"name": "SaaSworthy", "url": "https://www.saasworthy.com/", "kind": "submit",
     "note": "free software listing with an Indian audience"},
    {"name": "Capterra India", "url": "https://www.capterra.in/", "kind": "submit",
     "note": "free vendor listing for software tools"},
    {"name": "GetApp", "url": "https://www.getapp.com/", "kind": "submit",
     "note": "free software directory, sister of Capterra"},
    {"name": "PitchWall", "url": "https://pitchwall.co/", "kind": "submit",
     "note": "free product launch wall"},
    {"name": "Launching Next", "url": "https://www.launchingnext.com/", "kind": "submit",
     "note": "free startup listing"},
    {"name": "Awesome lists", "url": "https://github.com/sindresorhus/awesome",
     "kind": "resource",
     "note": "a PR adding a genuinely free finance calculator to a relevant awesome list"},
    {"name": "Wikipedia external links", "url": "https://en.wikipedia.org/wiki/Calculator",
     "kind": "resource",
     "note": "only if a real article cites the tool as a source; never spam it"},
    {"name": "Indian personal finance blogs", "url": "https://www.google.com/search?q=indian+personal+finance+blog+write+for+us",
     "kind": "email", "note": "blogs with a write-for-us page; pitch the editor, never mass-mail"},
    {"name": "Indian startup blogs", "url": "https://www.google.com/search?q=indian+startup+blog+guest+post",
     "kind": "email", "note": "startup publications that take founder-written pieces"},
    {"name": "Quora answers", "url": "https://www.quora.com/", "kind": "email",
     "note": "agent drafts the answer, Sir posts it; links are nofollow but send real readers"},
    {"name": "Reddit r/IndiaInvestments", "url": "https://www.reddit.com/r/IndiaInvestments/",
     "kind": "email", "note": "draft only; the answer must stand alone without the link"},
    {"name": "Reddit r/IndiaTax", "url": "https://www.reddit.com/r/IndiaTax/", "kind": "email",
     "note": "draft only; GST and tax questions are where the tools genuinely help"},
    {"name": "Reddit r/IndianStreetBets", "url": "https://www.reddit.com/r/IndianStreetBets/",
     "kind": "email", "note": "draft only; strict self-promotion rules"},
    {"name": "Dev.to", "url": "https://dev.to/", "kind": "submit",
     "note": "free technical writing platform; a build write-up earns a real link"},
    {"name": "Hashnode", "url": "https://hashnode.com/", "kind": "submit",
     "note": "free blogging platform with a follow link"},
    {"name": "Medium", "url": "https://medium.com/", "kind": "submit",
     "note": "free publishing; nofollow but real referral traffic"},
]

# The pages worth pointing an editor at. A pitch is only credible if it links
# to the page that answers the reader's question.
LINK_TARGETS = [
    ("/", "the calculator home"),
    ("/gst-calculator", "GST with and without tax"),
    ("/emi-calculator", "loan EMI and total interest"),
    ("/break-even-point-explained", "break-even"),
    ("/ltv-cac-ratio", "LTV to CAC"),
    ("/burn-rate-and-runway", "burn rate and runway"),
    ("/startup-valuation-explained", "startup valuation methods"),
    ("/shark-tank-valuation-calculator-in-crores", "Shark Tank deal valuation"),
    ("/profit-margin-calculator-rupees", "profit margin in rupees"),
    ("/cap-table-and-esop-pool", "cap table and ESOP dilution"),
]


# ------------------------------------------------------------------ mechanics

def reachable(url: str) -> str:
    """'live', 'blocked' or 'dead'. A 403 is not a dead prospect: directories
    like AlternativeTo and Product Hunt block a scripted GET while working
    fine in a browser, and dropping them would shrink the list to whatever
    happens to have no bot filter."""
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


def check_prospects() -> list[dict]:
    with ThreadPoolExecutor(max_workers=10) as ex:
        states = list(ex.map(lambda p: reachable(p["url"]), PROSPECTS))
    return [{**p, "status": s} for p, s in zip(PROSPECTS, states)]


def slugify(s: str) -> str:
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


# ------------------------------------------------------------------- packets

# Every venue asks a different question, so every venue gets a different packet.
# One generic blob for all of them is the thing that gets a submission flagged:
# Show HN wants a plain technical sentence and no marketing, Product Hunt wants
# a tagline and a maker comment, a directory wants categories. A packet that is
# byte-identical across three venues is also, obviously, not written for any of
# them. Keys are prospect names; anything not listed falls back to `generic`.
VENUE = {
    "AlternativeTo": {
        "fields": [("Name", "Tank Metrics"), ("URL", BASE),
                   ("Alternative to", "Excel templates, manual GST and EMI calculation"),
                   ("License", "Free"), ("Platforms", "Web (works on mobile)"),
                   ("Categories", "Business & Commerce, Finance, Calculators")],
        "blurb": ("Tank Metrics is a free web app with 100+ calculators for Indian small "
                  "businesses - GST, loan EMI, profit margin, break-even, payroll and "
                  "valuation. It is a lighter alternative to keeping the same sums in a "
                  "spreadsheet: no sign-up, no install, and each page shows the formula "
                  "it uses."),
        "note": "AlternativeTo asks what this replaces and under what licence - both answered above.",
    },
    "Product Hunt": {
        "fields": [("Name", "Tank Metrics"), ("URL", BASE),
                   ("Tagline", "100+ free calculators for Indian small businesses"),
                   ("Topics", "Fintech, Productivity, Calculators, Small Business"),
                   ("Pricing", "Free")],
        "blurb": ("Every number an Indian small business runs on, in one free place. GST "
                  "with and without tax, loan EMI and total interest, profit and operating "
                  "margin, break-even, CAC and LTV, burn rate and runway, valuation "
                  "multiples, payroll. No account, works on a phone, formula shown on "
                  "every page."),
        "maker": ("I kept rebuilding the same GST and EMI sums in a spreadsheet for every "
                  "project, so I put them in one place where the formula is visible and "
                  "the answer can be checked by hand. Free, no sign-up. Happy to hear "
                  "which calculator is missing."),
        "note": "Product Hunt wants a tagline, topics and a first maker comment - all three above.",
    },
    "Hacker News Show HN": {
        "fields": [("Title", "Show HN: 100+ free calculators for Indian business maths"),
                   ("URL", BASE)],
        "blurb": ("I built a set of calculators for the Indian business sums that are "
                  "annoying to get right: GST with and without tax, EMI on a "
                  "reducing-balance vs flat-rate loan, break-even, CAC/LTV, burn and "
                  "runway, valuation multiples. Static pages, no account, no tracking "
                  "beyond basic analytics."),
        "maker": ("Two things that bit me while building this and are worth knowing: the "
                  "rate a lender quotes is often a flat rate, not reducing balance, so the "
                  "effective rate is much higher than it looks; and GST has to be backed "
                  "out of an inclusive price differently from the way it is added to an "
                  "exclusive one. Both are handled explicitly. Source is on GitHub. "
                  "Feedback on anything that is wrong for a specific Indian context is "
                  "welcome."),
        "note": ("Show HN is technical and allergic to marketing. Keep the title plain, "
                 "say what it is and how it is built, and do not use the tagline."),
    },
    "BetaList": {
        "fields": [("Name", "Tank Metrics"), ("URL", BASE),
                   ("Tagline", "Free calculators for Indian business, in rupees"),
                   ("Description", "100+ free calculators for Indian founders and small businesses")],
        "blurb": ("A free collection of 100+ calculators for Indian small businesses and "
                  "founders: GST, EMI, margin, break-even, payroll, valuation. No "
                  "sign-up, works on a phone, formula shown on each page."),
        "note": "BetaList is for new products - the launch framing, not the directory fields.",
    },
    "Indie Hackers": {
        "fields": [("Product", "Tank Metrics"), ("URL", BASE),
                   ("One-liner", "Free Indian business calculators, built solo")],
        "blurb": ("100+ calculators for Indian business maths - GST, EMI, margin, "
                  "break-even, CAC/LTV, runway, valuation. Built and run solo, free, no "
                  "account."),
        "maker": ("Built this solo after rebuilding the same GST and EMI sheets for every "
                  "project. Free and no sign-up on purpose - the whole value is that you "
                  "can check the formula by hand. Would like to hear what to add next."),
        "note": "Indie Hackers rewards the build story - keep the maker note, it is the point.",
    },
    "Crunchbase": {
        "fields": [("Organization", "Tank Metrics"), ("Website", BASE),
                   ("Short description", "Free financial calculators for Indian businesses")],
        "blurb": ("Tank Metrics publishes free financial calculators for Indian small "
                  "businesses and founders, covering GST, loan EMI, margins, break-even, "
                  "payroll and startup valuation."),
        "note": ("Crunchbase wants a factual company description only. Do not claim "
                 "funding, employees or investors that do not exist."),
    },
    "Startup India": {
        "fields": [("Entity", "Tank Metrics"), ("Website", BASE),
                   ("Sector", "Financial services / Software"), ("Stage", "Early")],
        "blurb": ("Tank Metrics provides free financial calculators for Indian small "
                  "businesses - GST, EMI, margin, break-even, payroll and startup "
                  "valuation - in rupees, with no sign-up."),
        "note": ("Startup India is a government registry. Fill only fields that are true; "
                 "leave DPIIT recognition and funding blank if not held."),
    },
    "IndiaMART": {
        "fields": [("Business name", "Tank Metrics"), ("Website", BASE),
                   ("Category", "Business services / Financial software")],
        "blurb": ("Free online calculators for Indian businesses: GST, loan EMI, profit "
                  "margin, break-even and payroll, with the formula shown on each page."),
        "note": "IndiaMART is a business directory - use the plain business framing.",
    },
    "SaaSworthy": {
        "fields": [("Product", "Tank Metrics"), ("URL", BASE),
                   ("Category", "Financial software, Calculators"),
                   ("Free trial", "Free, no sign-up")],
        "blurb": ("100+ free financial calculators for Indian businesses and startups, "
                  "covering GST, EMI, margins, break-even, CAC/LTV, runway and valuation."),
        "note": "Software directory - answer the pricing and category fields exactly.",
    },
    "Capterra India": {
        "fields": [("Vendor", "Tank Metrics"), ("Product", "Tank Metrics"), ("URL", BASE),
                   ("Category", "Financial software"), ("Pricing", "Free")],
        "blurb": ("A free suite of 100+ financial calculators for Indian small businesses "
                  "and founders, covering GST, loan EMI, margin, break-even, payroll and "
                  "valuation multiples."),
        "note": "Capterra is a vendor listing - use the vendor/product framing.",
    },
    "GetApp": {
        "fields": [("Product", "Tank Metrics"), ("URL", BASE),
                   ("Category", "Financial software"), ("Pricing", "Free")],
        "blurb": ("Free financial calculators for Indian businesses: GST, EMI, margin, "
                  "break-even, payroll and startup valuation, each showing its formula."),
        "note": "GetApp mirrors Capterra's fields - keep the two descriptions distinct.",
    },
    "PitchWall": {
        "fields": [("Name", "Tank Metrics"), ("URL", BASE),
                   ("Tagline", "100+ free calculators for Indian businesses")],
        "blurb": ("Free calculators for Indian business maths - GST, EMI, margin, "
                  "break-even, payroll and valuation. No sign-up."),
        "note": "Launch wall - one line only, no long description field.",
    },
    "Launching Next": {
        "fields": [("Name", "Tank Metrics"), ("URL", BASE),
                   ("Tagline", "Free Indian business calculators")],
        "blurb": ("100+ free calculators for Indian small businesses: GST, loan EMI, "
                  "profit margin, break-even, payroll and startup valuation."),
        "note": "Startup listing - short description only.",
    },
    "Awesome lists": {
        "fields": [("Proposed entry",
                    "- [Tank Metrics](https://tankmetrics.in) - free calculators for "
                    "Indian business maths (GST, EMI, margin, break-even, payroll).")],
        "blurb": ("A pull request that adds one line to a relevant section of an existing "
                  "awesome list. Read that list's CONTRIBUTING first, and only open the PR "
                  "if the list genuinely has a section the tool belongs in."),
        "note": ("An awesome list is a curated repo, not a form. The deliverable is a PR "
                 "with one honest line, and a maintainer can simply decline it."),
    },
    "Wikipedia external links": {
        "fields": [("Note", "Only edit if a real article genuinely cites the tool as a source.")],
        "blurb": ("This is a monitor, not a submission. Wikipedia external links are for "
                  "sources an article relies on. Adding a link to promote the site is "
                  "against policy and gets reverted - leave this alone unless a real "
                  "article cites Tank Metrics."),
        "note": "Deliberately a no-op. Do not submit anything here.",
    },
    "Dev.to": {
        "fields": [("Title", "How Indian GST and EMI maths actually work, with the formulas"),
                   ("Canonical URL", f"{BASE}/gst-calculator")],
        "blurb": ("A technical write-up of the two sums people most often get wrong in "
                  "India: backing GST out of an inclusive price rather than adding it, and "
                  "the gap between a flat-rate and a reducing-balance loan quote. Each "
                  "formula worked through with real numbers, then checkable against a "
                  "calculator."),
        "note": ("Dev.to is a writing platform - the deliverable is a real article, and the "
                 "link goes in the canonical field rather than the body."),
    },
    "Hashnode": {
        "fields": [("Title", "The Indian business sums that are easy to get wrong"),
                   ("Canonical URL", f"{BASE}/break-even-point-explained")],
        "blurb": ("A written piece on break-even, GST-inclusive pricing and loan rates in "
                  "an Indian context, with the formulas and worked numbers, aimed at small "
                  "business owners rather than analysts."),
        "note": "Hashnode is a blog - write the article, link once at the end.",
    },
    "Medium": {
        "fields": [("Title", "What a Shark Tank deal actually values your company at"),
                   ("Canonical URL", f"{BASE}/shark-tank-valuation-calculator-in-crores")],
        "blurb": ("A plain-language piece on how an investment amount and an equity stake "
                  "produce a valuation, using Shark Tank India deals as the worked example, "
                  "and why the number changes between pre-money and post-money."),
        "note": ("Medium links are nofollow - the value here is referral readers, not "
                 "PageRank. Write for the reader."),
    },
}


def listing_packet(p: dict) -> str:
    v = VENUE.get(p["name"])
    if v:
        fields = "\n".join(f"    {k:<14} {val}" for k, val in v["fields"])
        extra = ""
        if v.get("maker"):
            extra = f"\nFirst comment (post this yourself, right after the listing):\n\n    {v['maker']}\n"
        return f"""# {p['name']} - submission content

- prospect: {p['url']}
- kind: {p['kind']}
- why this is legitimate: {p['note']}

Copy the fields below into the form. Nothing here needs a payment.

{fields}

Description:

    {v['blurb']}
{extra}
- how to submit: {v['note']}

---
AGENT-PREPARED - review and submit it yourself from your own account.
"""

    return f"""# {p['name']} - submission content

- prospect: {p['url']}
- kind: {p['kind']}
- why this is legitimate: {p['note']}

Copy the fields below into the form. Nothing here needs a payment.

    Name:        Tank Metrics
    URL:         {BASE}
    Category:    Business Tools / Finance / Calculators
    Language:    English and Hinglish

Description:

    Tank Metrics is a free set of 100+ calculators for Indian small businesses
    and founders: GST, loan EMI, profit margin, break-even, payroll, CAC and
    LTV, burn rate and runway, and valuation multiples. No sign-up, works on a
    phone, and every page shows the formula it uses.

Read this venue's own guidelines before submitting, and trim the description to
whatever length it actually allows.

---
AGENT-PREPARED - review and submit it yourself from your own account.
"""


def email_packet(p: dict, target: tuple[str, str]) -> str:
    url, what = target
    return f"""# {p['name']} - editor pitch

- prospect: {p['url']}
- kind: {p['kind']}
- why this is legitimate: {p['note']}
- link target: {BASE}{url} ({what})

Send this from your own address. One editor at a time, and only where the
site genuinely takes contributions.

    Subject: A free calculator for your readers

    Hi,

    I run Tank Metrics ({BASE}), a free set of 100+ calculators for Indian
    small businesses: GST, loan EMI, profit margin, break-even, CAC and LTV,
    burn rate and runway, valuation multiples. No sign-up, no paywall, and
    each page shows the formula it uses.

    I thought {what} might fit your readers: {BASE}{url}

    If it is useful, feel free to link it. If not, no reply needed.

    Thanks,
    [your name]

---
AGENT-PREPARED - Sir sends this himself. The agent must never send email.
"""


def answer_packet(p: dict, target: tuple[str, str]) -> str:
    url, what = target
    return f"""# {p['name']} - community answer draft

- prospect: {p['url']}
- kind: {p['kind']}
- link target: {BASE}{url} ({what})

Post this yourself. The answer must be useful with the link removed - both
Quora and Reddit remove pure self-promotion, and they are right to.

    Title: How do you work out {what} without a spreadsheet?

    Body:

    The short version is that {what} is one formula, and most people get it
    wrong because they mix up the number the bank quotes with the number they
    actually pay. Work the formula by hand once, then check it against a
    calculator before you use the number in a real decision.

    Two things that catch people out in India specifically: the rate you are
    quoted is often a flat rate rather than a reducing-balance rate, and tax
    is deducted at source before the money reaches you. Both change the
    answer, and neither is obvious from the headline number.

    I keep a free calculator for this here: {BASE}{url}
    It shows the formula and each step, so you can check the maths yourself.

---
AGENT-PREPARED - Sir posts this himself. The agent must never post to Quora,
Reddit, Medium or LinkedIn.
"""


def build_packet(p: dict, target: tuple[str, str], day: str) -> tuple[str, str]:
    stem = f"tools/outreach/authority/{day}-{slugify(p['name'])}"
    if p["kind"] in ("submit", "resource"):
        return f"{stem}-listing.md", listing_packet(p)
    if p["kind"] == "monitor":
        return "", ""
    if "Reddit" in p["name"] or "Quora" in p["name"]:
        return f"{stem}-answer.md", answer_packet(p, target)
    return f"{stem}-pitch.md", email_packet(p, target)


# ---------------------------------------------------------------- citations

def citations() -> list[dict]:
    """Free, login-free sources only. Classify each hit so a namesake is not
    reported as a mention of us."""
    hits: list[dict] = []
    try:
        q = urllib.parse.quote('"tankmetrics.in"')
        req = urllib.request.Request(
            f"https://hn.algolia.com/api/v1/search?query={q}&tags=(story,comment)",
            headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode())
        for h in data.get("hits", [])[:20]:
            text = (h.get("story_text") or h.get("comment_text") or "") + (h.get("url") or "")
            if "tankmetrics.in" in text.lower():
                hits.append({
                    "source": "Hacker News",
                    "where": h.get("title") or h.get("story_title") or "",
                    "url": f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                    "kind": "LINKED"})
    except Exception as e:
        print(f"  hn citation check: {e}")
    return hits


# ------------------------------------------------------------- github commit

def gh(method: str, path: str, payload=None, token: str = "") -> dict | list:
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": UA,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode()
    return json.loads(body) if body.strip() else {}


def commit_file(path: str, content: str, message: str, token: str) -> bool:
    """Create or update one file on main via the contents API."""
    sha = None
    try:
        cur = gh("GET", f"/repos/{REPO}/contents/{path}?ref=main", token=token)
        if isinstance(cur, dict):
            sha = cur.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    payload = {"message": message, "branch": "main",
               "content": base64.b64encode(content.encode()).decode()}
    if sha:
        payload["sha"] = sha
    try:
        gh("PUT", f"/repos/{REPO}/contents/{path}", payload, token)
        return True
    except urllib.error.HTTPError as e:
        print(f"  commit {path} failed: {e.code} {e.read().decode()[:200]}")
        return False


# ----------------------------------------------------------------------- main

def main() -> None:
    day = date.today().isoformat()
    print(f"authority run {time.strftime('%Y-%m-%d %H:%M')} (dry={DRY})")

    state = kv_get(_STATE_KEY) or {}
    prepared = set(state.get("prepared", []))
    prepared_today = state.get("prepared_today", 0) if state.get("prepared_day") == day else 0

    prospects = check_prospects()
    live = [p for p in prospects if p["status"] in ("live", "blocked") and p["kind"] != "monitor"]
    dead = [p for p in prospects if p["status"] == "dead"]
    print(f"  prospects: {len(prospects)} | usable: {len(live)} | dead: {len(dead)}")

    remaining = max(0, DAILY_QUOTA - prepared_today)
    todo = [p for p in live if p["name"] not in prepared]
    todo.sort(key=lambda p: {"submit": 0, "resource": 1, "email": 2}.get(p["kind"], 3))
    made: list[tuple[str, str]] = []
    for i, p in enumerate(todo[:remaining]):
        target = LINK_TARGETS[(prepared_today + i) % len(LINK_TARGETS)]
        path, content = build_packet(p, target, day)
        if path and content:
            made.append((path, content))
            prepared.add(p["name"])

    cites = citations()
    print(f"  packets this run: {len(made)} | citations: {len(cites)}")

    committed, commit_err = [], ""
    if not DRY and made:
        try:
            token = get_secret("GITHUB_TOKEN")
            for path, content in made:
                if commit_file(path, content,
                               f"Authority packet: {path.split('/')[-1]}", token):
                    committed.append(path)
            ledger = {
                "updated": time.strftime("%Y-%m-%dT%H:%M"),
                "prepared_total": len(prepared),
                "prepared": sorted(prepared),
                "prospects_total": len(PROSPECTS),
                "dead": [p["name"] for p in dead],
                "citations": cites,
            }
            if commit_file(LEDGER_PATH, json.dumps(ledger, indent=1) + "\n",
                           "Authority ledger", token):
                committed.append(LEDGER_PATH)
        except Exception as e:
            commit_err = str(e)
            print(f"  github error: {e}")

    if not DRY:
        kv_set(_STATE_KEY, {
            "prepared": sorted(prepared),
            "prepared_day": day,
            "prepared_today": prepared_today + len(made),
            "updated": time.strftime("%Y-%m-%dT%H:%M"),
        })
        kv_set("authority_summary", {
            "updated": time.strftime("%Y-%m-%dT%H:%M"),
            "prospects": len(PROSPECTS),
            "usable": len(live),
            "dead": len(dead),
            "packets_this_run": len(made),
            "prepared_total": len(prepared),
            "committed": committed,
            "commit_error": commit_err,
            "citations": len(cites),
        })

    report = [
        f"# Authority run {time.strftime('%Y-%m-%d %H:%M')}",
        "",
        f"- Prospects in the registry: {len(PROSPECTS)} ({len(live)} usable, {len(dead)} dead)",
        f"- Packets prepared this run: {len(made)} (daily quota {DAILY_QUOTA})",
        f"- Packets prepared all time: {len(prepared)}",
        f"- Citations found: {len(cites)}",
        "",
        "## Packets",
        "",
    ]
    report += [f"- `{p}`" for p, _ in made] or ["- none (quota reached or list exhausted)"]
    report += ["", "## Citations", ""]
    report += ([f"- {c['kind']} {c['source']}: {c['where']} {c['url']}" for c in cites]
               or ["- none found yet"])
    if dead:
        report += ["", "## Dead prospects (dropped)", ""]
        report += [f"- {p['name']} ({p['url']})" for p in dead]
    print("\n".join(report))


if __name__ == "__main__":
    try:
        main()
        fire_callback("COMPLETED")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        fire_callback("FAILED", str(e))
        sys.exit(1)
