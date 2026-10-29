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


def kv_get(key: str):
    if not kv_available():
        return None
    try:
        req = urllib.request.Request(
            f"{_KV_BASE}/v1/kv/{key}",
            headers={"Authorization": f"Bearer {_KV_TOKEN}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())["value"]
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

def listing_packet(p: dict) -> str:
    return f"""# {p['name']} - submission content

- prospect: {p['url']}
- kind: {p['kind']}
- why this is legitimate: {p['note']}

Copy the fields below into the form. Nothing here needs a payment.

    Name:        Tank Metrics
    URL:         {BASE}
    Tagline:     Free Indian business calculators - GST, EMI, margin, payroll and 100 more
    Category:    Business Tools / Finance / Calculators
    Tags:        calculator, gst, emi, finance, small business, india, free tool
    Language:    English and Hinglish

Short description:

    Tank Metrics is a free set of 100+ calculators for Indian small businesses
    and founders. GST, loan EMI, profit margin, break-even, payroll, valuation
    multiples and more. No sign-up, runs in the browser, and every page shows
    the formula it uses.

Long description:

    Tank Metrics covers the numbers an Indian small business actually runs on:
    GST with and without tax, loan EMI and total interest, profit and operating
    margin, break-even, CAC and LTV, burn rate and runway, valuation multiples
    and payroll. Each calculator is one page, works on a phone, needs no
    account, and states the formula so the answer can be checked by hand.
    It is free.

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

    if not DRY and made:
        try:
            token = get_secret("GITHUB_TOKEN")
            for path, content in made:
                commit_file(path, content,
                            f"Authority packet: {path.split('/')[-1]}", token)
            ledger = {
                "updated": time.strftime("%Y-%m-%dT%H:%M"),
                "prepared_total": len(prepared),
                "prepared": sorted(prepared),
                "prospects_total": len(PROSPECTS),
                "dead": [p["name"] for p in dead],
                "citations": cites,
            }
            commit_file(LEDGER_PATH, json.dumps(ledger, indent=1) + "\n",
                        "Authority ledger", token)
        except Exception as e:
            print(f"  github error: {e}")

    if not DRY:
        kv_set(_STATE_KEY, {
            "prepared": sorted(prepared),
            "prepared_day": day,
            "prepared_today": prepared_today + len(made),
            "updated": time.strftime("%Y-%m-%dT%H:%M"),
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
