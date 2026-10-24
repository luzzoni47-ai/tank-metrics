#!/usr/bin/env python3
"""Generate /digital-products and link it from every footer.

The page is generated so a price, a bullet or the payment link is a one-line
change and the copy stays in step with the workbook it sells.

The buy button points at PAYMENT_URL. Until Sir pastes a real Razorpay /
Gumroad link it stays None, and the page then says the checkout is being set up
and offers email instead. It must never claim a purchase succeeded, because no
payment has been taken.

    python3 tools/gen_products_page.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
BASE = "https://tankmetrics.in"

# Sir pastes the Razorpay / Gumroad checkout link here. None = not set up yet.
PAYMENT_URL: str | None = None
CONTACT_EMAIL = "hello@tankmetrics.in"

TITLE = "Digital Products — Tank Metrics"
DESC = (
    "The Indian Business Financial Model: a 21-sheet Excel model plus a "
    "156-page masterclass covering manufacturing, trading, services, agency "
    "and SaaS."
)
CANON = f"{BASE}/digital-products"

PRODUCT = "Indian Business Financial Model"
PRICE = "₹4,999"
MRP = "₹7,999"
MANUAL_PAGES = 156
SAMPLE = "/site/downloads/sample-preview.pdf"
RECKONER = "/site/downloads/gst-tax-reckoner.pdf"

FOOTER_LINK = ('<li><a href="/digital-products">Digital Products</a></li>')

LEGAL_RE = re.compile(
    r'(<div class="footer-col"><h4>Legal</h4><ul>)(.*?)(</ul></div>)', re.S)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


def buy_block() -> str:
    if PAYMENT_URL:
        return (f'<a class="btn-primary" href="{esc(PAYMENT_URL)}" '
                f'rel="noopener">Buy now — {PRICE}</a>')
    return (
        '<p class="amt-hint"><strong>Checkout is being set up.</strong> '
        f'Email <a href="mailto:{CONTACT_EMAIL}?subject=Indian%20Business%20'
        'Financial%20Model">' + CONTACT_EMAIL + '</a> and I will send the '
        'payment link the moment it is live.</p>'
    )


SHEETS = [
    ("START HERE", "How to use the model in ten minutes, and what not to touch."),
    ("Assumptions", "Every driver in one place: growth, pricing, cost, GST, tax, DSO/DPO."),
    ("Revenue Build", "Units, customers or billable hours — the switch picks your driver."),
    ("Headcount", "Role-wise count and salary, with PF, ESI and the annual hike."),
    ("OpEx", "Rent, marketing, tools, legal, travel — fixed and variable, escalating."),
    ("CapEx &amp; Depreciation", "Asset purchases and WDV depreciation at the IT Act rate."),
    ("Working Capital", "Receivables, inventory and payables, so you see the cash you lock up."),
    ("Debt", "Term loan, EMI, interest and principal, month by month."),
    ("P&amp;L", "60 months of profit and loss, with the year-wise summary."),
    ("Balance Sheet", "60 months of assets, liabilities and equity, tied to the cash flow."),
    ("Cash Flow", "Indirect method — operating, investing and financing."),
    ("Checks", "Three automatic checks. Every month must read OK, or you fix the input."),
    ("Unit Economics", "CAC, LTV, LTV:CAC, payback and lifetime contribution."),
    ("Scenarios", "Worst, base and best, with a multiplier for each driver."),
    ("Valuation", "DCF and revenue multiple, side by side."),
    ("Investor Dashboard", "ARR, burn, runway, gross margin and Rule of 40 on one page."),
    ("Fundraise Summary", "How much to raise and where each rupee goes."),
    ("Partner Split", "Who owns what and who gets what, for two brothers or four."),
    ("GST &amp; TDS", "Output GST, input credit, net payable, and the TDS timing."),
    ("Break-even", "The monthly and annual revenue you must cross."),
    ("Monthly Close", "A 14-point checklist to close the books every month."),
]

CHAPTERS = [
    "How to read the model in ten minutes",
    "Assumptions: top-down vs bottom-up, and what is realistic in India",
    "Revenue: units, subscriptions and billable hours",
    "GST inside the model — output, input credit and cash timing",
    "TDS, TCS and why your cash and your profit differ",
    "India payroll: CTC structure, PF, ESI, professional tax and gratuity",
    "Working capital: DSO, DPO and inventory days",
    "Depreciation and capital expenditure under the IT Act",
    "Debt: term loans, moratorium, EMI and working-capital limits",
    "Cap table and dilution maths — fully diluted, ESOP pool, preference shares",
    "How the three statements tie together, step by step",
    "Unit economics: CAC, LTV, payback and contribution margin",
    "Burn, runway and default alive vs default dead",
    "Valuation: DCF, multiples and the Indian SME reality",
    "The metrics an investor actually checks",
    "Fifteen mistakes almost every founder makes in a model",
    "Glossary of 100+ finance terms",
    "Case study: one Indian business, modelled screen by screen",
]


def build_body() -> str:
    sheets = "".join(
        f'<div class="card"><div class="card-body">'
        f'<h3 class="card-title">{i + 1}. {n}</h3>'
        f'<p class="card-desc">{d}</p></div></div>'
        for i, (n, d) in enumerate(SHEETS))
    chapters = "".join(f"<li>{c}</li>" for c in CHAPTERS)
    return f'''<div class="main main-prose" style="max-width:1100px;margin:0 auto">
<div class="page-hero"><div class="tag">📘 Digital Products</div>
<h1>Indian Business Financial Model</h1>
<p>One Excel model and one masterclass for manufacturing, trading, services, agency and SaaS businesses — {PRICE}.</p></div>
</div>

<div class="page-wrap" style="max-width:1100px">
<h2>What this is</h2>
<p>Most financial models are built for software companies. This one is built for
Indian businesses. Pick your business type from a dropdown and the model changes
its own revenue driver — units for manufacturing and trading, billable hours for
services and agency, customers for SaaS.</p>
<p>It is a working Excel file, not a template full of dummy numbers. Every
formula is open, so you can see exactly how each figure is calculated and change
anything you like. The manual explains the reason behind each line, in plain
language.</p>

<h2>Inside the Excel model — {len(SHEETS)} sheets</h2>
<div class="grid">{sheets}</div>

<h2>Inside the masterclass — {MANUAL_PAGES} pages</h2>
<ol class="plain-list">{chapters}</ol>

<h2>Who it is for</h2>
<ul class="plain-list">
<li><strong>Manufacturing</strong> — factory owners planning capacity, raw material and a term loan.</li>
<li><strong>Trading, retail and distribution</strong> — anyone whose money sits in stock and debtors.</li>
<li><strong>Services</strong> — consultants and IT firms billing by the hour.</li>
<li><strong>Agency and freelancers</strong> — retainers, utilisation and per-client profit.</li>
<li><strong>SaaS and subscription</strong> — MRR, churn, cohorts and ARR.</li>
<li><strong>Founders and partners</strong> — anyone raising money or splitting profit between brothers.</li>
</ul>

<h2>What else you get</h2>
<ul class="plain-list">
<li><strong>Video walkthrough</strong> — short screen recordings, one per section of the model.</li>
<li><strong>Checklists and templates</strong> — pre-fundraise checklist, board pack, investor update email and data-room index.</li>
<li><strong>Twelve months of email support</strong> — if a formula confuses you, write in and get an answer.</li>
<li><strong>Free updates</strong> — when a tax rate, GST slab or PF limit changes, the file is updated and you get it free.</li>
<li><strong>Lifetime access</strong> — the file is yours, with no subscription.</li>
</ul>

<h2>How to use it</h2>
<ol class="plain-list">
<li>Open the Assumptions sheet and fill the yellow cells.</li>
<li>Pick your business type.</li>
<li>Fill the revenue row that matches your type, then headcount, expenses and capex.</li>
<li>Open the Checks sheet. Every month must say OK.</li>
<li>Read the Investor Dashboard. That is your one-page story.</li>
</ol>

<h2>Read before you buy</h2>
<p>Two free PDFs, no email needed.</p>
<ul class="plain-list">
<li><a href="{SAMPLE}"><strong>Download the sample preview</strong></a> — the
first three chapters, plus a sample from every later part, watermarked.</li>
<li><a href="{RECKONER}"><strong>Download the GST + Tax Reckoner</strong></a> —
GST slabs, TDS sections, the compliance calendar and the deductions worth
knowing. A useful guide on its own.</li>
</ul>

<h2>Price</h2>
<p><strong>{PRICE}</strong> — launch price, {MRP} after the first fifty buyers.
One payment, no subscription. GST invoice provided.</p>
{buy_block()}

<h2>Questions</h2>
<div class="card"><div class="card-body">
<h3 class="card-title">Does it work on Google Sheets?</h3>
<p class="card-desc">The file is .xlsx. Google Sheets opens it, and the formulas
work, but a few formatting details shift. For the full experience use Excel,
LibreOffice Calc or WPS.</p></div></div>
<div class="card"><div class="card-body">
<h3 class="card-title">Do I need to know accounting?</h3>
<p class="card-desc">No. The manual starts from the basics and explains each
term. If you can read a bank statement, you can use this.</p></div></div>
<div class="card"><div class="card-body">
<h3 class="card-title">Is this for a CA or for me?</h3>
<p class="card-desc">It is for you, and your CA will find it useful. It is a
planning and decision tool, not a filing tool. Confirm rates with your CA before
you file.</p></div></div>
<div class="card"><div class="card-body">
<h3 class="card-title">What if it does not suit my business?</h3>
<p class="card-desc">Write in within seven days for a full refund, no questions
asked. Every copy is stamped with your details, so please do not share it.</p>
</div></div>

<p class="amt-hint">This is a digital product. It is a planning aid, not tax or
investment advice. Tax rates, GST slabs and PF/ESI limits shown are the Indian
rules as of 2026.</p>
</div>'''


def build_page() -> str:
    body = build_body()
    schema = (
        '{"@context":"https://schema.org","@type":"Product",'
        f'"name":"{esc(PRODUCT)}","description":"{esc(DESC)}",'
        f'"url":"{CANON}","brand":{{"@type":"Brand","name":"Tank Metrics"}},'
        '"offers":{"@type":"Offer","price":"4999","priceCurrency":"INR",'
        f'"availability":"https://schema.org/InStock","url":"{CANON}"}}'
        + "}"
    )
    crumb = (
        '{"@context":"https://schema.org","@type":"BreadcrumbList",'
        '"itemListElement":[{"@type":"ListItem","position":1,"name":"Home",'
        f'"item":"{BASE}/"}},{{"@type":"ListItem","position":2,'
        f'"name":"Digital Products","item":"{CANON}"}}]}}'
    )
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<link rel="icon" href="/site/favicon.ico" sizes="any">
<link rel="icon" href="/site/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/site/favicon.png" type="image/png" sizes="192x192">
<meta name="google-site-verification" content="CyIhu9CYYQapfzYJOeSLTP_XY_HWq0McbmY4uX342o4">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(TITLE)}</title>
<meta name="description" content="{esc(DESC)}">
<link rel="canonical" href="{CANON}">
<meta property="og:title" content="{esc(TITLE)}">
<meta property="og:description" content="{esc(DESC)}">
<meta property="og:type" content="product">
<meta property="og:url" content="{CANON}">
<meta property="og:site_name" content="Tank Metrics">
<meta property="og:image" content="{BASE}/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(TITLE)}">
<meta name="twitter:description" content="{esc(DESC)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Gloock&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/site/style.css">
<script type="application/ld+json">{schema}</script>
<script type="application/ld+json">{crumb}</script>
</head><body>
<div class="tricolor"></div>
<div class="topbar"><div class="topbar-inner">
<button class="menu-btn" id="menuBtn" type="button" aria-label="Open menu" aria-expanded="false">•••</button>
<div class="brand"><a href="/" class="brand-home-link" style="display:flex;align-items:center;gap:11px;text-decoration:none;color:inherit"><div class="brand-mark"><span class="rs">₹</span></div><div class="brand-text"><span class="brand-name">Tank Metrics</span><p>Simple money calculators, made for beginners</p></div></a></div>
<nav class="toplinks"><a href="/">Home</a> <a href="/news">News</a> <a href="/blog">Blog</a> <a href="/about">About</a> <a href="/digital-products" class="active">Products</a> <a href="/contact">Contact</a></nav>
</div></div>
{body}
</body></html>
'''


def add_footer_link() -> int:
    """Add the Digital Products link to every footer's Legal column."""
    changed = 0
    for p in sorted(SITE.rglob("*.html")):
        t = orig = p.read_text(encoding="utf-8")
        if 'href="/digital-products"' in t:
            continue

        def sub(m):
            head, items, tail = m.group(1), m.group(2), m.group(3)
            if "digital-products" in items:
                return m.group(0)
            return head + items + FOOTER_LINK + tail

        t = LEGAL_RE.sub(sub, t)
        if t != orig:
            p.write_text(t, encoding="utf-8")
            changed += 1
    return changed


def main() -> None:
    (SITE / "digital-products.html").write_text(build_page(), encoding="utf-8")
    n = add_footer_link()
    print(f"wrote /site/digital-products.html; footer link added to {n} pages")
    print(f"payment link: {'set' if PAYMENT_URL else 'NOT SET (page shows email)'}")


if __name__ == "__main__":
    main()
