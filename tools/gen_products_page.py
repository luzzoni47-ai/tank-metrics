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


PAGE_CSS = """
.licence-form { display:flex; flex-wrap:wrap; gap:10px; align-items:flex-end;
                margin:14px 0 6px; }
.licence-form label { flex:1 1 100%; font-weight:600; font-size:.92rem;
                      color:#1F3864; }
.licence-form input { flex:1 1 260px; padding:12px 14px; font-size:1rem;
                      font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
                      letter-spacing:.06em; text-transform:uppercase;
                      border:1.5px solid #CBD5E1; border-radius:10px;
                      background:#fff; }
.licence-form input:focus { outline:none; border-color:#2E5C8A;
                            box-shadow:0 0 0 3px rgba(46,92,138,.14); }
.licence-form button { flex:0 0 auto; padding:12px 22px; font-size:1rem;
                       font-weight:600; color:#fff; background:#1F3864;
                       border:0; border-radius:10px; cursor:pointer; }
.licence-form button:hover:not(:disabled) { background:#2E5C8A; }
.licence-form button:disabled { opacity:.6; cursor:progress; }
.licence-result { margin:12px 0; padding:14px 16px; border-radius:10px;
                  font-size:.95rem; line-height:1.55; }
.licence-info { background:#EEF4FB; border-left:4px solid #2E5C8A; }
.licence-good { background:#EFF8F0; border-left:4px solid #138808; }
.licence-bad  { background:#FDECEC; border-left:4px solid #C0392B; }
.licence-result code { font-family:ui-monospace,Menlo,monospace;
                       background:rgba(0,0,0,.06); padding:1px 5px;
                       border-radius:4px; }
"""

LICENCE_ENDPOINT_SET = True  # matches ENDPOINT in public/site/licence.js


def licence_block() -> str:
    """The download box. Files are not linked here; a key unlocks them.

    A public link cannot be revoked. A licence key can, which is what makes a
    refund actually cut off access.
    """
    return """<h2>Already bought? Get your files</h2>
<p>Enter the licence key from your order email. It looks like
<code>TM-XXXX-XXXX-XXXX-XXXX</code>.</p>
<form id="licence-form" class="licence-form" autocomplete="off">
  <label for="licence-key">Licence key</label>
  <input id="licence-key" name="key" type="text" inputmode="text"
         placeholder="TM-XXXX-XXXX-XXXX-XXXX" spellcheck="false" required>
  <button id="licence-submit" type="submit">Get my files</button>
</form>
<div id="licence-result" class="licence-result" hidden></div>
<p class="amt-hint">Lost your key? Email
<a href="mailto:hello@tankmetrics.in?subject=Lost%20licence%20key">hello@tankmetrics.in</a>
with your order number and I will resend it.</p>
<script src="/site/licence.js" defer></script>"""


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
    ("Part 1 — Foundations",
     "The model in ten minutes; the three statements and why they tie; "
     "top-down versus bottom-up assumptions."),
    ("Part 2 — Your business type",
     "One chapter each for manufacturing, trading, services, agency and SaaS, "
     "with what drives revenue and where the cash hides."),
    ("Part 3 — The Indian layer",
     "GST, TDS, payroll with PF and ESI, depreciation under the IT Act, "
     "working capital, and debt with a full EMI schedule."),
    ("Part 4 — Value and money",
     "Unit economics, break-even, valuation by DCF and multiple, fundraising, "
     "burn and runway, and fifteen mistakes to avoid."),
    ("Part 5 — Case study",
     "One Indian manufacturer, modelled month by month from assumptions to "
     "valuation."),
    ("Part 6 — Building in India",
     "Choosing a structure, MSME benefits, pricing, inventory valuation, "
     "budgeting, working with a CA, due diligence and the compliance calendar."),
    ("Part 7 — Advanced modelling",
     "Seasonality, multiple products, sensitivity, sector benchmarks, model "
     "hygiene and hiring."),
    ("Part 8 — Sector playbooks",
     "Twelve more sectors: restaurants, construction, healthcare, education, "
     "logistics, agri, exports, D2C, professional firms, local services, "
     "franchising, and cash intensity ranked."),
    ("Part 9 — Investor conversations",
     "Fifty questions an investor asks, with how to answer each, and four more "
     "case studies."),
    ("Part 10 — Reading the numbers",
     "Every ratio that matters, applying for a bank loan, and the statements "
     "line by line."),
    ("Part 11 — Putting it to work",
     "A 90-day plan, a fundability self-assessment, and the Excel recipes you "
     "will want."),
    ("Part 12 — The founder's toolkit",
     "A cash-crisis playbook, a Hinglish glossary of the terms you actually "
     "use, and scripts for the conversations founders avoid."),
    ("Part 13 — Working with the model",
     "Presenting the model, reviewing anyone's model in twenty minutes, and a "
     "one-page quick reference."),
]


def build_body() -> str:
    sheets = "".join(
        f'<div class="card"><div class="card-body">'
        f'<h3 class="card-title">{i + 1}. {n}</h3>'
        f'<p class="card-desc">{d}</p></div></div>'
        for i, (n, d) in enumerate(SHEETS))
    chapters = "".join(
        f'<li><strong>{title}</strong> — {desc}</li>' for title, desc in CHAPTERS)
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

{licence_block()}

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
<style>{PAGE_CSS}</style>
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
