#!/usr/bin/env python3
"""Generate one indexable page per calculator category.

The home page shows 13 category blocks whose tool cards are rendered by
JavaScript, so a crawler that does not run JS sees the block but not the 100
tools inside it, and a visitor who taps "Ad Agency Toolkit" has nowhere to go.

This writes /site/<category-slug>.html for every category: a real title, meta
description, H1, canonical, the category's tool cards as two-up links to their
own pages, an FAQ block, and CollectionPage + BreadcrumbList + FAQPage JSON-LD.

`clean_urls.py` turns the /site/ path into the public clean URL, and
`wire_crawl_graph.py` lists it in the sitemap, so this file stays the only
place that decides what a category page contains.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
DATA = json.loads((Path(__file__).parent / "calcs.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(ROOT / "tools"))
from gen_tool_pages import build_slugs  # noqa: E402
from siteconfig import BASE  # noqa: E402

SLUGS = build_slugs(DATA["calcs"])

ACCENTS = {
    "blue": "#4285F4", "green": "#34A853",
    "yellow": "#F2A600", "red": "#EA4335",
}

# A short, honest sentence per category. Written out rather than derived, so the
# intro is prose a person would say instead of a list of tool names.
BLURBS = {
    "everyday": "The money maths that comes up every week — a percentage of "
                "something, interest on a loan, what is left after the EMI, and "
                "splitting a bill without an argument.",
    "profit": "What the business actually keeps. Gross margin down to net "
              "margin, plus the return ratios a lender or an investor asks for.",
    "val": "The numbers behind a funding conversation — what the company is "
           "worth, what a cheque buys, and how much of the company the founder "
           "still owns afterwards.",
    "cust": "Unit economics: what it costs to win a customer, what that customer "
            "is worth over time, and whether the difference is wide enough to "
            "build on.",
    "growth": "How fast the business is moving and how long the cash lasts — "
              "run rate, CAGR, burn, runway and the break-even point.",
    "pricing": "What to charge and what survives the journey to the customer — "
               "MRP worked backwards, GST, landed cost, marketplace fees and "
               "the cost of a return.",
    "ops": "What a person really costs the business, what to charge as a "
           "freelancer, and how long a new store takes to pay for itself.",
    "investor": "The view from the other side of the table — how many times the "
                "money multiplied, the yearly return, and how big the market "
                "actually is.",
    "bonus": "Run the numbers a pitch invites questions about before someone "
             "else does.",
    "agency": "The metrics an agency is judged on — return on ad spend, the "
              "cost of a click and a client, margins, and how much of a "
              "person's day is billable.",
    "realestate": "Buying, renting and what a property is worth — EMI, yield, "
                  "stamp duty, brokerage and the real difference between rent "
                  "and a home loan.",
    "taxwealth": "Take-home pay, the old and new tax regimes, and the savings "
                 "instruments an Indian salaried person actually uses.",
    "dailyfun": "Light calculators for the things people look up on a whim — "
                "age, dates, BMI and the number puzzles that come up in "
                "family WhatsApp groups.",
}


def slug_for(cat: dict) -> str:
    s = cat["name"].lower().replace("&", " and ").replace("%", " percent ")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return re.sub(r"-{2,}", "-", s)


def tools_of(cat: dict) -> list[dict]:
    return [c for c in DATA["calcs"] if c["cat"] == cat["id"]]


def title_for(cat: dict, n: int) -> str:
    word = "Calculator" if n == 1 else "Calculators"
    return f"{cat['name']} — {n} Free {word} | Tank Metrics"


def desc_for(cat: dict, n: int) -> str:
    word = "calculator" if n == 1 else "calculators"
    return (f"{n} free {cat['name'].lower()} {word} for India. "
            f"Instant answers, worked in your browser, no sign-up and nothing "
            f"you type ever leaves the page.")[:158]


def faqs(cat: dict, tools: list[dict]) -> list[tuple[str, str]]:
    """Questions that are specific to this category, so no two share prose."""
    name = cat["name"]
    n = len(tools)
    names = [t["name"] for t in tools]
    listed = ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else names[0]
    word = "calculator" if n == 1 else "calculators"
    return [
        (f"What calculators are in {name}?",
         f"{name} holds {n} {word}: {listed}. Each one has its own page "
         f"with the formula and a worked Indian example."),
        (f"Are the {name} calculators free?",
         f"Yes. {'Every one of them is' if n > 1 else 'It is'} free, needs no "
         f"account and shows no paywall. There is no limit on how often you use "
         f"{'them' if n > 1 else 'it'}."),
        (f"Is my data sent anywhere when I use these tools?",
         "No. Every calculation runs inside your browser. The numbers you type "
         "are never uploaded, stored or sold."),
        (f"Do these use Indian lakh and crore formatting?",
         "Yes. Amounts are shown in the Indian numbering system, and the tax "
         "and salary tools use current Indian slabs and rules rather than a "
         "converted US template."),
    ]


def card_html(c: dict, accent: str) -> str:
    href = f"/site/tools/{SLUGS[c['id']]}.html"
    return (
        f'<a class="tcard" href="{href}" style="--accent:{accent}">'
        f'<h3>{html.escape(c["name"], quote=False)}</h3>'
        f'<p>{html.escape(c["desc"], quote=False)}</p>'
        f'<span class="tcard-go">Open calculator '
        f'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="2.6" stroke-linecap="round" '
        f'stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></span>'
        f'</a>'
    )


def sibling_html(cat: dict) -> str:
    others = [x for x in DATA["cats"] if x["id"] != cat["id"]]
    links = "".join(
        f'<a href="/site/{slug_for(x)}.html">{html.escape(x["name"], quote=False)}</a>'
        for x in others
    )
    return f'<nav class="cat-siblings" aria-label="Other toolkits"><h2>Other toolkits</h2><div>{links}</div></nav>'


# Two cards per row on desktop and tablet, one on a phone. Inlined so the rule
# is scoped to this page and style.css stays untouched.
GRID_CSS = (
    "<style>"
    ".cat-intro{max-width:760px;color:var(--muted);font-size:16.5px;line-height:1.65}"
    ".cat-tools{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin:8px 0 40px}"
    ".tcard{display:flex;flex-direction:column;gap:10px;background:#fff;"
    "border:1px solid var(--line);border-top:3px solid var(--accent,var(--blue));"
    "border-radius:16px;padding:22px 22px 18px;text-decoration:none;color:inherit;"
    "transition:box-shadow .2s ease,transform .15s ease;min-width:0}"
    ".tcard:hover{transform:translateY(-3px);box-shadow:0 18px 40px -20px rgba(8,11,18,.28)}"
    ".tcard h3{font-size:17px;margin:0;letter-spacing:-.02em}"
    ".tcard p{font-size:13.5px;color:var(--muted);line-height:1.6;margin:0}"
    ".tcard-go{margin-top:auto;font-size:13px;font-weight:600;color:var(--accent,var(--blue));"
    "display:inline-flex;align-items:center;gap:6px}"
    ".cat-siblings{margin:48px 0 24px;padding-top:28px;border-top:1px solid var(--line)}"
    ".cat-siblings h2{font-size:18px;margin-bottom:14px}"
    ".cat-siblings div{display:flex;flex-wrap:wrap;gap:8px}"
    ".cat-siblings a{font-size:13.5px;padding:8px 14px;border:1px solid var(--line);"
    "border-radius:999px;background:#fff;color:var(--ink-2)}"
    ".cat-siblings a:hover{border-color:var(--blue);color:var(--blue)}"
    "@media(max-width:768px){.cat-tools{grid-template-columns:1fr}}"
    "</style>"
)


def build_page(cat: dict) -> str:
    slug = slug_for(cat)
    tools = tools_of(cat)
    accent = ACCENTS.get(cat["color"], "#4285F4")
    title = title_for(cat, len(tools))
    desc = desc_for(cat, len(tools))
    url = f"{BASE}/site/{slug}.html"

    cards = "".join(card_html(c, accent) for c in tools)
    faq_items = faqs(cat, tools)
    faq_html = "".join(
        f"<h3>{html.escape(q, quote=False)}</h3><p>{html.escape(a, quote=False)}</p>"
        for q, a in faq_items
    )
    n = len(tools)
    count_line = f"{n} calculator in this toolkit" if n == 1 else f"{n} calculators in this toolkit"

    collection_ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": cat["name"],
        "url": url,
        "description": desc,
        "inLanguage": "en-IN",
        "isPartOf": {"@id": f"{BASE}/#website"},
        "about": {"@type": "Thing", "name": cat["name"]},
        "hasPart": [
            {
                "@type": "SoftwareApplication",
                "name": c["name"],
                "url": f"{BASE}/site/tools/{SLUGS[c['id']]}.html",
                "applicationCategory": "FinanceApplication",
                "operatingSystem": "Any (web browser)",
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "INR"},
            }
            for c in tools
        ],
    }
    bc_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": cat["name"], "item": url},
        ],
    }
    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faq_items
        ],
    }

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><link rel="icon" href="/site/favicon.ico" sizes="any"><link rel="icon" href="/site/favicon.svg" type="image/svg+xml"><link rel="icon" href="/site/favicon.png" type="image/png" sizes="192x192"><link rel="apple-touch-icon" href="/site/favicon.png" sizes="192x192"><link rel="manifest" href="/site/manifest.webmanifest"><meta name="google-site-verification" content="CyIhu9CYYQapfzYJOeSLTP_XY_HWq0McbmY4uX342o4"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<meta name="theme-color" content="#FF9933">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"><link rel="stylesheet" href="/site/style.css">{GRID_CSS}
<meta property="og:type" content="website"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}/og-image.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:site_name" content="Tank Metrics"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{title}"><meta name="twitter:description" content="{desc}"><meta name="twitter:image" content="{BASE}/og-image.png">
<script type="application/ld+json">{json.dumps(collection_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(bc_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-MHZ0V6HFC6"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-MHZ0V6HFC6');</script>
</head><body><div class="tricolor"></div><div class="topbar"><div class="topbar-inner"><button class="menu-btn" id="menuBtn" aria-label="Menu" style="visibility:hidden">☰</button><div class="brand"><a href="/" style="display:flex;align-items:center;gap:11px;text-decoration:none;color:inherit"><div class="brand-mark"><span class="rs">₹</span></div><div class="brand-text"><span class="brand-name">Tank Metrics</span><p>Simple money calculators, made for beginners</p></div></a></div><nav class="toplinks"><a href="/">Home</a> <a href="/site/blog.html">Blog</a> <a href="/site/about.html">About</a> <a href="/site/contact.html">Contact</a></nav></div></div>
<div class="main" style="max-width:1280px;margin:0 auto">
<div class="page-hero"><div class="tag">{html.escape(cat['name'], quote=False)}</div><h1>{html.escape(cat['name'], quote=False)}</h1><p class="cat-intro">{html.escape(BLURBS.get(cat['id'], ''), quote=False)}</p></div>
<div class="page-wrap">
<h2>{count_line}</h2>
<div class="cat-tools">{cards}</div>
<h2>Frequently asked questions</h2>
{faq_html}
{sibling_html(cat)}
<div class="cta-inline"><p>Looking for something else?</p><a class="btn-primary" href="/">Browse all 100 calculators →</a></div>
<p><a href="/">← All 100 Tank Metrics calculators</a></p>
</div></div>
<footer class="site-footer"><div class="footer-grid"><div class="footer-col"><h4>Tank Metrics</h4><p>100 free business calculators for entrepreneurs, students and small business owners. Everything is calculated right in your browser — nothing you type is ever sent anywhere.</p></div><div class="footer-col"><h4>Company</h4><ul><li><a href="/site/about.html">About Us</a></li><li><a href="/site/blog.html">Blog</a></li><li><a href="/site/contact.html">Contact Us</a></li></ul></div><div class="footer-col"><h4>Legal</h4><ul><li><a href="/site/privacy-policy.html">Privacy Policy</a></li><li><a href="/site/terms-and-conditions.html">Terms and Conditions</a></li><li><a href="/site/disclaimer.html">Disclaimer</a></li></ul></div><div class="footer-col"><h4>Popular</h4><ul><li><a href="/site/valuation-and-deals.html">Valuation &amp; Deals</a></li><li><a href="/site/customers-and-unit-economics.html">Unit Economics</a></li><li><a href="/site/everyday-money-basics.html">Everyday Money</a></li></ul></div><div class="footer-col"><h4>Digital Products</h4><ul><li><a href="/digital-products/indian-business-financial-model">Indian Business Financial Model</a></li></ul></div></div><div class="footer-bottom"><span>© 2026 Tank Metrics. Built for learning and quick estimates — for big decisions, always check with a qualified accountant or financial advisor.</span> <span>Made with <svg class="footer-heart" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg> in Bangalore, India</span></div></footer>
</body></html>
"""


def check_no_collisions(slugs: dict[str, str]) -> None:
    """A category slug must not shadow a tool, a static page or another category."""
    taken = set(slugs.values())
    taken |= {"about", "contact", "blog", "news", "privacy-policy",
              "terms-and-conditions", "disclaimer", "refund-policy"}
    seen: set[str] = set()
    for cat in DATA["cats"]:
        s = slug_for(cat)
        if s in taken:
            raise SystemExit(f"category slug {s!r} collides with an existing page")
        if s in seen:
            raise SystemExit(f"duplicate category slug {s!r}")
        seen.add(s)


def main() -> None:
    check_no_collisions(SLUGS)
    written = []
    for cat in DATA["cats"]:
        p = SITE / f"{slug_for(cat)}.html"
        p.write_text(build_page(cat), encoding="utf-8")
        written.append((slug_for(cat), len(tools_of(cat))))
    total = sum(n for _, n in written)
    print(f"category pages written: {len(written)}")
    for slug, n in written:
        print(f"  /{slug}  ({n} tools)")
    print(f"tools linked: {total}")


if __name__ == "__main__":
    main()
