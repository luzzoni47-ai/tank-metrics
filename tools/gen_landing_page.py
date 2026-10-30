#!/usr/bin/env python3
"""Generate the Indian Business Financial Model sales landing page.

    python3 tools/gen_landing_page.py

Writes:
    public/site/digital-products/indian-business-financial-model.html

Served at the clean URL /digital-products/indian-business-financial-model by the
rewrite in next.config.mjs, which reads tools/url-map.json - so clean_urls.py has
to know about this page too (see NESTED_PAGES there).

Two rules this page must never break, both guarded by tools/test_landing.py:

1. Every figure is real. The metrics in the interactive preview come from
   tools/landing_data.json, which is produced by running the shipped workbook
   itself (see tools/gen_landing_data.py). Nothing here is an invented number,
   and the sample block is labelled as the model's own defaults.

2. No invented social proof. No testimonials, no star ratings, no "2,847
   founders bought this" counter, no logos of companies that never bought it.
   The product has not been reviewed by anyone yet and the page must not
   pretend otherwise.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

from landing_style import LP_CSS

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
OUT_DIR = SITE / "digital-products"
OUT = OUT_DIR / "indian-business-financial-model.html"
BASE = "https://tankmetrics.in"

# The clean public path. clean_urls.py owns the mapping; this is the same value.
CLEAN = "/digital-products/indian-business-financial-model"
CANON = f"{BASE}{CLEAN}"

# Sir pastes the Razorpay / Gumroad checkout link here. While it is empty the
# buy button opens a prefilled email instead of pretending to take money. The
# inline script reads the same value from the page, so switching to a real
# gateway is a one-line change in two places and nothing else.
PAYMENT_URL: str | None = None
CONTACT_EMAIL = "hello@tankmetrics.in"
MAILTO = (f"mailto:{CONTACT_EMAIL}?subject=Indian%20Business%20Financial"
          f"%20Model%20%E2%80%93%20Purchase%20Enquiry")

PRODUCT = "Indian Business Financial Model"
PRICE = "₹4,999"
FUTURE_PRICE = "₹7,999"
MANUAL_PAGES = 156
SHEET_COUNT = 21
LAUNCH_LIMIT = 50

TITLE = "Indian Business Financial Model | Tank Metrics"
DESC = ("A 21-sheet Excel financial model and a 156-page masterclass for Indian "
        "businesses — manufacturing, trading, services, agency and SaaS. "
        "₹4,999 launch price.")
VIDEO = f"{BASE}/site/video/walkthrough.mp4"
POSTER = f"{BASE}/site/video/walkthrough.jpg"

DATA = json.loads((Path(__file__).resolve().parent / "landing_data.json")
                  .read_text(encoding="utf-8"))
TYPES = DATA["business_types"]

# The real sheet order in the shipped workbook, with what each one is for.
SHEETS: list[tuple[str, str]] = [
    ("Start Here", "How to use the model in ten minutes, and what not to touch."),
    ("Assumptions", "Every driver in one place: growth, pricing, cost, GST, tax and DSO/DPO."),
    ("Revenue Build", "Units, customers or billable hours — the switch picks your driver."),
    ("Headcount", "Role-wise count and salary, with PF, ESI and the annual hike."),
    ("Operating Expenses", "Rent, marketing, tools, legal and travel — fixed and variable."),
    ("CapEx &amp; Depreciation", "Asset purchases and WDV depreciation at the IT Act rate."),
    ("Working Capital", "Receivables, inventory and payables, so you see the cash you lock up."),
    ("Debt &amp; EMI", "Term loan, EMI, interest and principal, month by month."),
    ("Profit &amp; Loss", "60 months of profit and loss, with the year-wise summary."),
    ("Balance Sheet", "60 months of assets, liabilities and equity, tied to the cash flow."),
    ("Cash Flow", "Indirect method — operating, investing and financing."),
    ("Automatic Checks", "Three tests. Every month must read OK, or you fix the input."),
    ("Unit Economics", "CAC, LTV, LTV:CAC, payback and lifetime contribution."),
    ("Scenario Planning", "Worst, base and best, with a multiplier for each driver."),
    ("Business Valuation", "DCF and revenue multiple, side by side."),
    ("Investor Dashboard", "ARR, burn, runway, gross margin and Rule of 40 on one page."),
    ("Fundraise Summary", "How much to raise and where each rupee goes."),
    ("Partner Split", "Who owns what and who gets what, for two partners or four."),
    ("GST &amp; TDS", "Output GST, input credit, net payable, and the TDS timing."),
    ("Break-even Analysis", "The monthly and annual revenue you must cross."),
    ("Monthly Close Checklist", "A 14-point checklist to close the books every month."),
]

# The real 13 parts of the masterclass, with the real chapter titles.
CURRICULUM: list[tuple[str, str, list[str]]] = [
    ("Part 1", "Foundations", [
        "How to use this manual",
        "The model in ten minutes",
        "The three statements, and why they tie",
        "Assumptions: top-down versus bottom-up",
    ]),
    ("Part 2", "Your business type", [
        "Manufacturing",
        "Trading, retail and distribution",
        "Services",
        "Agency and freelancers",
        "SaaS and subscription",
    ]),
    ("Part 3", "The Indian layer", [
        "GST inside the model",
        "TDS, TCS and why cash differs from profit",
        "Payroll in India: PF, ESI, professional tax and gratuity",
        "Depreciation and capex under the IT Act",
        "Working capital: DSO, DPO and inventory days",
        "Debt: term loans, EMI and working-capital limits",
    ]),
    ("Part 4", "Value and money", [
        "Unit economics: does one customer make money?",
        "Break-even: the revenue you must cross",
        "Valuation: DCF, multiples and the Indian SME reality",
        "Fundraising: how much, and why",
        "Burn, runway and default alive",
        "The fifteen mistakes almost every founder makes",
    ]),
    ("Part 5", "Case study", [
        "One Indian business, modelled end to end",
    ]),
    ("Part 6", "Building in India", [
        "Choosing a business structure in India",
        "MSME registration and the benefits you are entitled to",
        "Pricing: the fastest lever on profit",
        "Inventory valuation: FIFO, weighted average and why it matters",
        "Budgeting and variance: plan versus actual",
        "Working with a CA, and what to hand over",
        "Due diligence: what a buyer or investor checks",
        "The Indian compliance calendar",
        "The Excel skills this model uses",
        "Exit: selling the business you built",
    ]),
    ("Part 7", "Advanced modelling", [
        "Modelling seasonality",
        "Several products, several revenue lines",
        "Sensitivity: which assumption actually matters",
        "Sector benchmarks for Indian businesses",
        "Model hygiene: keeping it trustworthy for years",
        "Hiring: modelling the team you will actually need",
    ]),
    ("Part 8", "Sector playbooks", [
        "Restaurants, construction, healthcare and education",
        "Logistics, agriculture, exports and D2C",
        "Professional services, local services and franchising",
        "Fifteen Indian business models, ranked by cash intensity",
    ]),
    ("Part 9", "Investor conversations", [
        "Fifty questions an investor will ask — and how to answer",
        "Four more case studies",
    ]),
    ("Part 10", "Reading the numbers", [
        "The ratios that matter, and what they tell you",
        "Applying for a bank loan: what they ask and what decides it",
        "Reading a financial statement line by line",
        "Growth: when faster is worse",
    ]),
    ("Part 11", "Putting it to work", [
        "Your first 90 days with this model",
        "Is your business fundable? A self-assessment",
        "Excel recipes you will want",
    ]),
    ("Part 12", "The founder's toolkit", [
        "The cash crisis playbook",
        "Business terms in Hinglish",
        "Scripts for the conversations founders avoid",
    ]),
    ("Part 13", "Working with the model", [
        "Presenting your model in a meeting",
        "Reviewing any financial model in twenty minutes",
        "The one-page quick reference",
        "Where to go for help",
    ]),
]

AUDIENCE: list[tuple[str, str, str]] = [
    ("Manufacturing", "Factory and workshop owners",
     "Plan capacity, raw-material cost and a term loan. See the month your "
     "EMI and your working capital both bite."),
    ("Trading &amp; Distribution", "Wholesalers, stockists, retail chains",
     "Model inventory days and debtor days. Find out how much cash your "
     "growth is quietly locking up in stock."),
    ("Services", "Consultants, IT firms, professionals",
     "Price a billable hour that actually covers overheads, and see the "
     "utilisation you need before profit appears."),
    ("Agencies &amp; Freelancers", "Retainer businesses and studios",
     "Per-client profit, retainer mix and the cost of delivery — before you "
     "sign the next contract."),
    ("SaaS &amp; Subscriptions", "Founders and product teams",
     "MRR, churn, cohorts and ARR, with burn and runway on the same page as "
     "the P&amp;L."),
    ("Founders &amp; Partners", "Anyone raising money or splitting profit",
     "A fundraise summary, a partner split and the investor metrics an "
     "investor will ask for."),
]

DELIVERABLES: list[tuple[str, str, str]] = [
    ("Editable Excel model",
     "The 21-sheet workbook. Every formula is open and unlocked, so you can "
     "see how each figure is calculated and change anything."),
    ("156-page masterclass",
     "13 parts and over 60 chapters, written in plain language for Indian "
     "business owners rather than finance specialists."),
    ("Video walkthrough",
     "A guided tour of the workbook, rendered from the shipped model's own "
     "sheets, so you are not left staring at 21 tabs on day one."),
    ("Checklists &amp; templates",
     "Monthly close checklist, pre-fundraise checklist, board pack index, "
     "investor update email and a data-room index."),
    ("12 months of email support",
     "If a formula confuses you, write in and get a written answer. No "
     "support ticket queue."),
    ("Free eligible updates",
     "When a GST slab, tax rate or PF limit changes, the file is updated and "
     "buyers get the new version at no cost."),
]

STEPS: list[tuple[str, str]] = [
    ("Open Assumptions",
     "Fill the designated input cells. This is the only sheet you type into."),
    ("Pick your business type",
     "One dropdown switches the revenue driver to units, hours or customers."),
    ("Enter your numbers",
     "Revenue driver, headcount, operating expenses and capital expenditure."),
    ("Read the Checks sheet",
     "Every month must say OK. A red flag points at the input to correct."),
    ("Use the dashboard",
     "The Investor Dashboard and the three statements tell your one-page story."),
]

FAQ: list[tuple[str, str]] = [
    ("Does the model work in Google Sheets?",
     "The file is .xlsx, and Google Sheets opens it with the formulas intact. "
     "A few formatting details shift, and very large workbooks can feel slow. "
     "For the full experience use desktop Excel, LibreOffice Calc or WPS "
     "Office. Whichever you choose, open the Checks sheet first and confirm "
     "every month still reads OK before you rely on the numbers — every "
     "spreadsheet application evaluates formulas slightly differently."),
    ("Do I need accounting knowledge?",
     "No. The manual starts from the basics and explains each term the first "
     "time it is used. If you can read a bank statement and a GST invoice, "
     "you can use this model. Where a concept needs more depth, the relevant "
     "chapter is linked from the sheet."),
    ("Is it useful for a CA, or only for a business owner?",
     "Both. It is built for owners who want to understand their own numbers, "
     "and accountants find it a useful starting structure to work from. It is "
     "a planning and decision tool — it does not file returns, and it does not "
     "replace your CA."),
    ("Which business types are supported?",
     "Five: manufacturing, trading and distribution, services, agency and "
     "freelancers, and SaaS or subscription businesses. Each one changes the "
     "revenue driver in the model — units for manufacturing and trading, "
     "billable hours for services and agency, customers for SaaS."),
    ("How do I receive the product?",
     "After your payment is confirmed you receive a licence key by email. "
     "Enter that key in the box on this page and the workbook and manual unlock "
     "for you. There is no public download link, which is what lets a refund "
     "genuinely cut off access."),
    ("What does the refund policy cover?",
     "A seven-day refund window from the date of purchase, subject to the "
     "published terms. Write to hello@tankmetrics.in with your order number and "
     "the refund is processed on the same key that delivered your files."),
    ("Is this a tax filing tool?",
     "No. It is a financial planning and educational aid. It helps you model "
     "GST, TDS, payroll cost, depreciation and tax as planning assumptions. "
     "It does not compute your statutory liability, file a return or "
     "substitute for professional advice. Confirm applicable rates with a "
     "qualified professional."),
    ("Are updates included?",
     "Yes. When a statutory rate that the model uses changes — GST, income "
     "tax, PF or ESI limits — the workbook is revised and every buyer gets the "
     "updated file free. You keep lifetime access to the product you bought."),
]

VIDEO_PRESENT = (SITE / "video" / "walkthrough.mp4").exists()


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def inr(v: float) -> str:
    """Indian short form: 9.71L, 1.17Cr, 9,600."""
    a = abs(v)
    if a >= 1_00_00_000:
        return f"₹{v / 1_00_00_000:.2f} Cr"
    if a >= 1_00_000:
        return f"₹{v / 1_00_000:.2f} L"
    if a >= 1000:
        return f"₹{v:,.0f}"
    return f"₹{v:,.0f}"


def num(v: float) -> str:
    a = abs(v)
    if a >= 1_00_00_000:
        return f"{v / 1_00_00_000:.2f} Cr"
    if a >= 1_00_000:
        return f"{v / 1_00_000:.2f} L"
    return f"{v:,.0f}"


ICON = {
    "check": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" '
             'stroke="currentColor" stroke-width="2.6" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>',
    "arrow": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" '
             'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><line x1="5" y1="12" x2="19" y2="12"/>'
             '<polyline points="12 5 19 12 12 19"/></svg>',
    "play": '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" '
            'aria-hidden="true"><polygon points="6 3 20 12 6 21"/></svg>',
    "lock": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" '
            'height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    "sheet": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" '
             'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" '
             'height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/>'
             '<line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/>'
             '<line x1="15" y1="3" x2="15" y2="21"/></svg>',
    "book": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 '
            '6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 '
            '6.5 2z"/></svg>',
    "shield": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" '
              'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
              'stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 '
              '3v7c0 6 8 10 8 10z"/></svg>',
    "clock": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" '
             'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
             '<polyline points="12 7 12 12 16 14"/></svg>',
    "refresh": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" '
               'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
               'stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-3-6.7"/>'
               '<polyline points="21 3 21 9 15 9"/></svg>',
    "mail": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" '
            'height="16" rx="2"/><polyline points="2 7 12 14 22 7"/></svg>',
    "chart": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" '
             'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><line x1="4" y1="20" x2="4" y2="10"/>'
             '<line x1="10" y1="20" x2="10" y2="4"/><line x1="16" y1="20" x2="16" y2="13"/>'
             '<line x1="22" y1="20" x2="22" y2="7"/></svg>',
}

DELIVERABLE_ICONS = ["sheet", "book", "play", "check", "mail", "refresh"]


# --------------------------------------------------------------------------
# sections
# --------------------------------------------------------------------------

def mockup() -> str:
    """The dashboard illustration. Inline SVG and CSS only.

    No <img>: the CSP is img-src 'self' data:, so an off-site mockup would be
    silently blocked, and a same-origin one is another request for a picture
    that is cheaper to draw in markup.
    """
    rev = [float(v) for v in DATA["dashboard_default"].values()
           if isinstance(v, (int, float))][:1]
    return """
<div class="mock" aria-hidden="true">
  <div class="mock-bar"><i></i><i></i><i></i><span>Indian Business Financial Model.xlsx</span></div>
  <div class="mock-body">
    <div class="kpis">
      <div class="kpi"><small>Revenue / mo</small><b>₹9.71 L<span class="up">▲</span></b></div>
      <div class="kpi"><small>Gross margin</small><b>50%</b></div>
      <div class="kpi"><small>Cash in bank</small><b>₹6.17 Cr</b></div>
    </div>
    <div class="chart">
      <div class="cap"><span>Revenue — 12 months</span><b>4% / month</b></div>
      <svg viewBox="0 0 300 96" width="100%" height="96" role="img"
           aria-label="Illustrative revenue curve rising over twelve months">
        <defs>
          <linearGradient id="lpfill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#1678FD" stop-opacity=".55"/>
            <stop offset="100%" stop-color="#1678FD" stop-opacity="0"/>
          </linearGradient>
        </defs>
        <path d="M0 78 C30 74 52 70 78 64 C104 58 128 50 154 42 C180 34 204 26 230 18
                 C254 11 278 6 300 3 L300 96 L0 96 Z" fill="url(#lpfill)"/>
        <path d="M0 78 C30 74 52 70 78 64 C104 58 128 50 154 42 C180 34 204 26 230 18
                 C254 11 278 6 300 3" fill="none" stroke="#63A9FF" stroke-width="2.4"
              stroke-linecap="round"/>
        <path d="M0 90 C40 88 80 84 120 79 C160 74 200 68 240 61 C264 57 284 54 300 52"
              fill="none" stroke="#21A542" stroke-width="2" stroke-dasharray="5 4"
              stroke-linecap="round"/>
      </svg>
    </div>
    <div class="sheet">
      <div class="cap"><span>Checks — every month must read OK</span><span>60 / 60</span></div>
      <table>
        <tr><th>Line item</th><th>Month 1</th><th>Month 60</th></tr>
        <tr><td>Revenue</td><td>9,60,000</td><td>97,10,425</td></tr>
        <tr><td>Gross profit</td><td>4,80,000</td><td>48,55,213</td></tr>
        <tr><td>EBITDA</td><td>2,40,500</td><td>45,31,027</td></tr>
        <tr class="ok"><td>Check 1: balance sheet</td><td>OK</td><td>OK</td></tr>
        <tr class="ok"><td>Check 2: no negative cash</td><td>OK</td><td>OK</td></tr>
      </table>
    </div>
  </div>
  <div class="badge badge-a">
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#21A542"
         stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"
         aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>
    <span>60/60 months tie<small>Balance sheet balances</small></span>
  </div>
  <div class="badge badge-b">
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#1678FD"
         stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"
         aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/>
      <line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
    <span>21 sheets<small>5 business types</small></span>
  </div>
</div>"""


def hero() -> str:
    facts = [
        (PRICE, "Launch price"),
        (FUTURE_PRICE, f"After {LAUNCH_LIMIT} buyers"),
        (f"{SHEET_COUNT}", "Excel sheets"),
        (f"{MANUAL_PAGES}", "Manual pages"),
        ("Lifetime", "Access"),
    ]
    fact_html = "".join(
        f'<div class="fact"><b>{esc(a)}</b><span>{esc(b)}</span></div>'
        for a, b in facts)
    video_line = (
        '<span class="dot"></span> Walkthrough video included'
        if VIDEO_PRESENT else
        '<span class="dot"></span> Built for Indian businesses')
    return f"""
<header class="hero" id="top">
  <div class="wrap">
    <div class="hero-grid">
      <div>
        <div class="hero-tag">{video_line}</div>
        <h1>Understand your numbers. <em>Build a better business.</em></h1>
        <p class="sub">One powerful Excel financial model and a practical
        masterclass built for Indian businesses — from manufacturing and
        trading to agencies and SaaS. Change an assumption and watch revenue,
        profit, cash flow and valuation move with it.</p>
        <div class="btn-row hero-cta">
          <a class="btn btn-primary" href="{MAILTO}" data-checkout>
            Get Your Financial Model {ICON['arrow']}
          </a>
          <a class="btn btn-dark" href="#inside">Explore What&rsquo;s Inside</a>
        </div>
        <p class="hero-note">One payment of {PRICE}. No subscription. GST
        invoice provided.</p>
        <div class="facts">{fact_html}</div>
      </div>
      <div>{mockup()}</div>
    </div>
  </div>
</header>"""


def strip() -> str:
    items = [
        f"{SHEET_COUNT} linked sheets",
        "60-month forecast",
        "Five business types",
        "GST, TDS and payroll built in",
        "Automatic checks",
        "Lifetime access",
    ]
    return '<div class="strip"><div class="wrap strip-in">' + "".join(
        f'<span>{ICON["check"]}{esc(i)}</span>' for i in items) + "</div></div>"


def problem() -> str:
    rows = [
        ("Manufacturing", "units, production cost and capacity"),
        ("Trading", "inventory, stock turnover and receivables"),
        ("Services", "billable hours and utilisation"),
        ("Agencies", "retainers, clients and delivery cost"),
        ("SaaS", "subscriptions, MRR, churn and ARR"),
    ]
    lis = "".join(
        f'<li><strong>{esc(k)}</strong> &mdash; {v}</li>' for k, v in rows)
    return f"""
<section class="sec" id="problem">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="eyebrow">The problem</span>
      <h2>Most financial models aren&rsquo;t built for your business</h2>
      <p>Generic templates assume one kind of company. A factory, a
      distributor, a consultancy and a SaaS product earn money in completely
      different ways, so a model built for software quietly gives the other
      four the wrong answer.</p>
    </div>
    <div class="cards cards-2">
      <div class="card rv">
        <div class="ico">{ICON['chart']}</div>
        <h3>One model, five revenue drivers</h3>
        <p>A single dropdown changes how revenue is built. The sheet then asks
        for the numbers that actually drive <em>your</em> business:</p>
        <ul class="ticks">{lis}</ul>
      </div>
      <div class="card rv">
        <div class="ico">{ICON['refresh']}</div>
        <h3>Change an assumption, see the consequence</h3>
        <p>Every figure traces back to the Assumptions sheet. Move your growth
        rate, your price, your debtor days or your salary bill, and the P&amp;L,
        the balance sheet, the cash flow and the valuation all move together —
        which is how you find out whether a decision is affordable before you
        make it.</p>
        <p>The model also refuses to let you fool yourself: three automatic
        checks test the balance sheet, the cash balance and the debt schedule
        in all 60 months, and a red flag tells you which input to fix.</p>
      </div>
    </div>
  </div>
</section>"""


def demo() -> str:
    """The interactive preview, driven by the real model's own output."""
    tabs = "".join(
        f'<button class="tab" type="button" role="tab" data-type="{esc(t)}" '
        f'aria-selected="{"true" if i == 0 else "false"}" '
        f'id="tab-{esc(t.lower())}">{esc(t)}</button>'
        for i, t in enumerate(TYPES))

    drivers = {
        "Manufacturing": ("Units produced and sold",
                          "Each unit carries a price and a raw-material plus direct-labour cost."),
        "Trading": ("Units bought and sold",
                    "Revenue is stock moved; the cash hides in inventory and debtors."),
        "Services": ("Billable hours",
                     "Revenue is hours billed; utilisation decides whether you profit."),
        "Agency": ("Billable hours on retainers",
                   "Revenue is delivery hours; retainer mix decides the margin."),
        "SaaS": ("Subscribers",
                 "Revenue is customers, with churn working against growth every month."),
    }
    payload = {}
    for t, d in TYPES.items():
        payload[t] = {
            "revenue": num(d["revenue_month_60"]),
            "gross_profit": num(d["gross_profit_month_60"]),
            "gross_margin": f"{d['gross_margin'] * 100:.0f}%",
            "ebitda": num(d["ebitda_month_60"]),
            "net_profit": num(d["net_profit_month_60"]),
            "cash": num(d["cash_month_60"]),
            "breakeven": num(d["break_even_revenue_month"]),
            "valuation": num(d["valuation_blended"]),
            "driver_label": drivers[t][0],
            "driver_note": drivers[t][1],
            "driver_value": f"{d['driver_month_1']:,.0f}",
        }

    first = next(iter(TYPES))
    f = payload[first]
    metrics = [
        ("Revenue &middot; month 60", f["revenue"]),
        ("Gross margin", f["gross_margin"]),
        ("Operating profit (EBITDA)", f["ebitda"]),
        ("Cash in bank &middot; month 60", f["cash"]),
        ("Break-even revenue / month", f["breakeven"]),
        ("Blended valuation", f["valuation"]),
    ]
    metric_html = "".join(
        f'<div class="metric"><small>{k}</small><b data-metric="{i}">{esc(v)}</b></div>'
        for i, (k, v) in enumerate(metrics))

    return f"""
<section class="sec" id="preview">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="eyebrow">See it work</span>
      <h2>Pick a business type and watch the model follow</h2>
      <p>The numbers below are the shipped workbook&rsquo;s own defaults,
      recalculated for each business type. They are illustrative — your own
      figures will be different.</p>
    </div>
    <div class="demo rv">
      <div class="demo-head">
        <div>
          <h3>Business type</h3>
          <p>The same model, five different revenue drivers.</p>
        </div>
        <div class="tabs" role="tablist" aria-label="Business type">{tabs}</div>
      </div>
      <div class="demo-body">
        <div class="demo-metrics" id="lp-metrics">{metric_html}</div>
        <div class="demo-side">
          <div class="driver">
            <small>Revenue driver</small>
            <b id="lp-driver-label">{esc(f['driver_label'])}</b>
            <p id="lp-driver-note">{esc(f['driver_note'])}</p>
          </div>
          <div class="side-card">
            <h3>What the model does with it</h3>
            <ul>
              <li>Builds revenue month by month for 60 months</li>
              <li>Carries it through the P&amp;L, balance sheet and cash flow</li>
              <li>Tests all three with the automatic checks</li>
              <li>Reports it on the Investor Dashboard and valuation sheets</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="demo-note">
        <strong>Illustrative figures.</strong> These are the model&rsquo;s own
        default assumptions (4% monthly growth, ₹8,000 price, 50% gross
        margin), run once per business type. They are not a forecast, not a
        promise of results, and not a substitute for your own numbers.
      </div>
    </div>
  </div>
</section>
<script type="application/json" id="lp-data">{json.dumps(payload, ensure_ascii=False)}</script>"""


def sheets_section() -> str:
    cards = "".join(
        f'<div class="sheet-card rv"><div class="n">{i + 1}</div>'
        f'<div><h4>{n}</h4><p>{d}</p></div></div>'
        for i, (n, d) in enumerate(SHEETS))
    return f"""
<section class="sec" id="inside">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="eyebrow">The workbook</span>
      <h2>All {SHEET_COUNT} sheets, and what each one does</h2>
      <p>Nothing is hidden and nothing is locked. Every sheet exists to answer
      a question you will actually ask.</p>
    </div>
    <div class="sheets">{cards}</div>
  </div>
</section>"""


def curriculum_section() -> str:
    total = sum(len(ch) for _, _, ch in CURRICULUM)
    parts = "".join(
        f'<div class="part rv"><div class="pn">{esc(num_label)}</div><div>'
        f'<h3>{esc(title)}</h3><ul>'
        + "".join(f"<li>{esc(c)}</li>" for c in chapters)
        + "</ul></div></div>"
        for num_label, title, chapters in CURRICULUM)
    topics = [
        "Financial modelling fundamentals", "Revenue assumptions and forecasting",
        "GST, TDS and cash timing", "Indian payroll and employee costs",
        "Working capital and inventory", "Depreciation and capital expenditure",
        "Loans, EMI and interest", "Cap tables and dilution",
        "Three-statement modelling", "CAC, LTV and contribution margin",
        "Burn rate and runway", "Valuation methods", "Investor metrics",
        "Common founder mistakes", "Finance glossary", "Indian SME case study",
    ]
    chips = "".join(f"<li>{esc(t)}</li>" for t in topics)
    return f"""
<section class="sec" id="manual">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="eyebrow">The masterclass</span>
      <h2>{MANUAL_PAGES} pages. 13 parts. {total} chapters.</h2>
      <p>The manual explains the reason behind every line in the model, in
      plain language — not just what to type, but why it matters.</p>
    </div>
    <div class="cur">{parts}</div>
    <div class="sec-head rv" style="margin:52px auto 22px">
      <h2 style="font-size:clamp(21px,2.4vw,27px)">Every topic you need is a chapter</h2>
    </div>
    <ul class="sheets" style="list-style:none">{chips}</ul>
  </div>
</section>"""


def video_section() -> str:
    if not VIDEO_PRESENT:
        return ""
    return f"""
<section class="sec" id="walkthrough">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="eyebrow">Watch it first</span>
      <h2>See the real workbook in 45 seconds</h2>
      <p>Every sheet, assumption and figure in this walkthrough is read out of
      the shipped model itself — the same file a buyer receives. Assumptions,
      the revenue build, the 60-month P&amp;L, the automatic checks, the
      Investor Dashboard, break-even and the monthly close.</p>
    </div>
    <div class="demo rv" style="padding:14px">
      <video controls preload="metadata" poster="/site/video/walkthrough.jpg"
             playsinline style="width:100%;border-radius:14px;display:block;background:#070B18">
        <source src="/site/video/walkthrough.webm" type="video/webm">
        <source src="/site/video/walkthrough.mp4" type="video/mp4">
        Your browser cannot play this video. The workbook and the manual are
        included with your purchase either way.
      </video>
      <p class="demo-note" style="border:0;background:transparent;padding:14px 6px 4px">
        The figures shown are the shipped model&rsquo;s default assumptions, so
        they are illustrative of how the model behaves, not a forecast for your
        business.
      </p>
    </div>
  </div>
</section>"""


def deliverables() -> str:
    cards = "".join(
        f'<div class="card rv"><div class="ico">{ICON[DELIVERABLE_ICONS[i]]}</div>'
        f"<h3>{t}</h3><p>{d}</p></div>"
        for i, (t, d) in enumerate(DELIVERABLES))
    return f"""
<section class="sec" id="what-you-get">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="eyebrow">What you receive</span>
      <h2>Everything in one purchase</h2>
      <p>One payment, lifetime access, no subscription and no upsell ladder.</p>
    </div>
    <div class="cards cards-3">{cards}</div>
    <div class="disc rv" style="margin-top:24px">
      <h3>What this is not</h3>
      <p>This is a planning and learning tool. It is not accounting software
      and it is not tax filing software. It will not compute your statutory
      liability or file a return for you, and it does not replace your
      accountant.</p>
    </div>
  </div>
</section>"""


def audience_section() -> str:
    cards = "".join(
        f'<div class="card rv"><h3>{t}</h3>'
        f'<p style="font-weight:600;color:var(--lp-blue);font-size:12.5px;'
        f'letter-spacing:.04em;text-transform:uppercase">{who}</p>'
        f"<p>{d}</p></div>"
        for t, who, d in AUDIENCE)
    return f"""
<section class="sec" id="who">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="eyebrow">Who it is for</span>
      <h2>Built for the decisions you are actually facing</h2>
      <p>Not every business models the same way. Here is what each one can
      decide with the model.</p>
    </div>
    <div class="cards cards-3">{cards}</div>
  </div>
</section>"""


def steps_section() -> str:
    cards = "".join(
        f'<div class="step rv"><div class="sn">{i + 1}</div>'
        f"<h3>{t}</h3><p>{d}</p></div>"
        for i, (t, d) in enumerate(STEPS))
    return f"""
<section class="sec" id="how">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="eyebrow">How it works</span>
      <h2>Five steps from blank sheet to a plan</h2>
      <p>You type into one sheet. The other twenty do the work.</p>
    </div>
    <div class="steps">{cards}</div>
  </div>
</section>"""


def pricing() -> str:
    ticks = [
        "Editable 21-sheet Excel workbook",
        f"{MANUAL_PAGES}-page masterclass manual",
        "Video walkthrough of the real model",
        "Checklists and templates",
        "12 months of email support",
        "Lifetime access to the product you buy",
    ]
    tick_html = "".join(
        f"<li>{ICON['check']}<span>{esc(t)}</span></li>" for t in ticks)
    if PAYMENT_URL:
        cta = (f'<a class="btn btn-primary btn-block" href="{esc(PAYMENT_URL)}" '
               f'rel="noopener">Get Your Financial Model — {PRICE}</a>')
    else:
        cta = (f'<a class="btn btn-primary btn-block" href="{MAILTO}" '
               f'data-checkout>Get Your Financial Model — {PRICE}</a>')
    return f"""
<section class="sec" id="pricing">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="eyebrow">Pricing</span>
      <h2>One payment. Everything included.</h2>
    </div>
    <div class="price-wrap">
      <div class="price-card rv">
        <div class="price-badge">Launch price</div>
        <h3 style="font-size:17px;margin-bottom:4px">{esc(PRODUCT)}</h3>
        <div class="price-now">
          <b>{PRICE}</b><s>{FUTURE_PRICE}</s>
          <em>one-time</em>
        </div>
        <p class="price-note">The planned price becomes {FUTURE_PRICE} after the
        first {LAUNCH_LIMIT} buyers. That is a planned future price set by us —
        not a discount verified by anyone else.</p>
        <ul class="ticks">{tick_html}</ul>
        {cta}
        <p class="refund">Seven-day refund policy, subject to the published
        terms. Read the <a href="/refund-policy">refund policy</a> before you
        buy. Checkout is being finalised — until the payment link is live, the
        button above opens a pre-filled email to {CONTACT_EMAIL} and you will
        get the payment link as soon as it is ready.</p>
      </div>
      <div class="price-side">
        <div class="side-card rv">
          <h3>Try before you buy</h3>
          <p>Two free PDFs, no email needed. Read the writing before you spend
          anything.</p>
          <ul>
            <li><a href="/site/downloads/sample-preview.pdf"><strong>Sample
            preview</strong></a> — the opening chapters of the masterclass.</li>
            <li><a href="/site/downloads/gst-tax-reckoner.pdf"><strong>GST +
            Tax Reckoner</strong></a> — slabs, TDS sections and the compliance
            calendar.</li>
          </ul>
        </div>
        <div class="side-card side-dark rv">
          <h3>Already bought it?</h3>
          <p>Enter your licence key below and your files unlock. Every copy is
          stamped with the buyer&rsquo;s details, which is what makes a refund
          able to cut off access.</p>
          <div class="btn-row" style="margin-top:16px">
            <a class="btn btn-dark" href="#unlock">Unlock my files
            {ICON['arrow']}</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>"""


def faq_section() -> str:
    items = "".join(
        f"<details><summary>{esc(q)}</summary>"
        f'<div class="a">{a}</div></details>'
        for q, a in FAQ)
    return f"""
<section class="sec" id="faq">
  <div class="wrap">
    <div class="sec-head rv">
      <span class="eyebrow">Questions</span>
      <h2>Straight answers</h2>
    </div>
    <div class="faq">{items}</div>
  </div>
</section>"""


def unlock_section() -> str:
    """The licence box.

    It lives here rather than on a separate page because /digital-products is
    now a redirect: a buyer who paid must be able to redeem on the same page
    that sold them the product. The files have no public URL, so this box is
    the only way in, and a refund revokes the key it hands out.
    """
    return """
<section class="sec-tight" id="unlock">
  <div class="wrap">
    <div class="unlock rv">
      <h2>Already bought? Get your files</h2>
      <p>Enter the licence key from your order email. It looks like
      <code>TM-XXXX-XXXX-XXXX-XXXX</code>.</p>
      <form id="licence-form" class="licence-form" autocomplete="off">
        <label for="licence-key">Licence key</label>
        <input id="licence-key" name="key" type="text" inputmode="text"
               placeholder="TM-XXXX-XXXX-XXXX-XXXX" spellcheck="false" required>
        <button id="licence-submit" type="submit">Get my files</button>
      </form>
      <div id="licence-result" class="licence-result" hidden></div>
      <p class="unlock-hint">Lost your key? Email
      <a href="mailto:hello@tankmetrics.in?subject=Lost%20licence%20key">hello@tankmetrics.in</a>
      with your order number and I will resend it.</p>
    </div>
  </div>
</section>
<script src="/site/licence.js" defer></script>"""


def closing() -> str:
    return f"""
<section class="sec-tight">
  <div class="wrap">
    <div class="disc rv">
      <h3>Disclaimer</h3>
      <p>This digital product is a financial planning and educational aid, not
      tax, legal, investment or accounting advice. Confirm applicable tax rates
      and compliance requirements with a qualified professional. Features and
      statutory assumptions must be verified before use. Tax rates, GST slabs
      and PF/ESI limits shown in the model reflect Indian rules as understood
      at the time of writing and may change.</p>
    </div>
  </div>
</section>

<section class="sec-tight">
  <div class="wrap">
    <div class="final rv">
      <h2>Understand your numbers. Build a better business.</h2>
      <p>{SHEET_COUNT} sheets, {MANUAL_PAGES} pages and a walkthrough — one
      payment of {PRICE}, yours for life.</p>
      <div class="btn-row">
        <a class="btn btn-primary" href="{MAILTO}" data-checkout>
          Get Your Financial Model {ICON['arrow']}
        </a>
        <a class="btn btn-dark" href="#inside">Explore What&rsquo;s Inside</a>
      </div>
      <small>Planned price rises to {FUTURE_PRICE} after the first
      {LAUNCH_LIMIT} buyers.</small>
    </div>
  </div>
</section>"""


SITE_FOOTER = """
<footer class="site-footer"><div class="footer-grid"><div class="footer-col"><h4>Tank Metrics</h4><p>100 free business calculators for entrepreneurs, students and small business owners. Everything is calculated right in your browser — nothing you type is ever sent anywhere.</p><span class="footer-flag"><span class="s"></span><span class="w"></span><span class="g"></span></span></div><div class="footer-col"><h4>Company</h4><ul><li><a href="/about">About Us</a></li><li><a href="/blog">Blog</a></li><li><a href="/contact">Contact Us</a></li></ul></div><div class="footer-col"><h4>Legal</h4><ul><li><a href="/privacy-policy">Privacy Policy</a></li><li><a href="/terms-and-conditions">Terms and Conditions</a></li><li><a href="/refund-policy">Refund Policy</a></li><li><a href="/disclaimer">Disclaimer</a></li></ul></div><div class="footer-col"><h4>Popular</h4><ul><li><a href="/#cat_val">Valuation &amp; Deals</a></li><li><a href="/#cat_cust">Unit Economics</a></li><li><a href="/#cat_everyday">Everyday Money</a></li></ul></div><div class="footer-col"><h4>Digital Products</h4><ul><li><a href="/digital-products/indian-business-financial-model">Indian Business Financial Model</a></li></ul></div></div><div class="footer-bottom"><span>© <span id="year"></span> Tank Metrics. Built for learning and quick estimates — for big decisions, always check with a qualified accountant or financial advisor.</span> <span>Made with <svg class="footer-heart" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg> in Bangalore, India</span></div></footer>
<script>document.getElementById("year").textContent=(new Date).getFullYear()</script>
"""

LP_FOOT = """
<div class="lp-foot"><div class="wrap lp-foot-in">
  <p><strong>Tank Metrics</strong> — simple money tools and practical finance
  education for Indian businesses. The Indian Business Financial Model is a
  planning and learning aid, not tax or accounting advice.</p>
  <nav aria-label="Footer">
    <a href="/">Home</a>
    <a href="/digital-products/indian-business-financial-model">Indian Business Financial Model</a>
    <a href="/blog">Blog</a>
    <a href="/about">About</a>
    <a href="/contact">Contact</a>
  </nav>
</div></div>
"""

LP_JS = """
(function () {
  var dataEl = document.getElementById('lp-data');
  if (dataEl) {
    var data = JSON.parse(dataEl.textContent);
    var order = ['revenue', 'gross_margin', 'ebitda', 'cash', 'breakeven', 'valuation'];
    var tabs = Array.prototype.slice.call(document.querySelectorAll('.tab[data-type]'));
    function select(type) {
      var d = data[type];
      if (!d) { return; }
      order.forEach(function (key, i) {
        var el = document.querySelector('[data-metric="' + i + '"]');
        if (el) { el.textContent = d[key]; }
      });
      var lbl = document.getElementById('lp-driver-label');
      var note = document.getElementById('lp-driver-note');
      if (lbl) { lbl.textContent = d.driver_label; }
      if (note) { note.textContent = d.driver_note; }
      tabs.forEach(function (b) {
        b.setAttribute('aria-selected', b.getAttribute('data-type') === type ? 'true' : 'false');
      });
    }
    tabs.forEach(function (b) {
      b.addEventListener('click', function () { select(b.getAttribute('data-type')); });
      b.addEventListener('keydown', function (e) {
        var i = tabs.indexOf(b), n = null;
        if (e.key === 'ArrowRight') { n = tabs[(i + 1) % tabs.length]; }
        if (e.key === 'ArrowLeft') { n = tabs[(i - 1 + tabs.length) % tabs.length]; }
        if (n) { e.preventDefault(); n.focus(); select(n.getAttribute('data-type')); }
      });
    });
  }

  // Checkout. While PAYMENT_URL is empty the button is a plain mailto link, so
  // it works with JavaScript switched off. Once a real gateway is pasted in,
  // every button with data-checkout routes there instead.
  var PAYMENT_URL = '';
  var buttons = document.querySelectorAll('[data-checkout]');
  if (PAYMENT_URL) {
    Array.prototype.forEach.call(buttons, function (b) {
      b.setAttribute('href', PAYMENT_URL);
      b.setAttribute('rel', 'noopener');
    });
  }

  // Reveal on scroll. Opt-in: the sections are visible in plain CSS, and this
  // adds the hiding class only now that there is script running to reveal them
  // again. If anything below throws, the page is still fully readable.
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var items = document.querySelectorAll('.rv');
  var revealAll = function () {
    Array.prototype.forEach.call(items, function (el) { el.classList.add('in'); });
  };
  if (reduce || !('IntersectionObserver' in window)) {
    revealAll();
    return;
  }
  document.documentElement.classList.add('lp-anim');
  // Anything already in the viewport reveals immediately, so the top of the
  // page is never blank while the observer warms up.
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
  Array.prototype.forEach.call(items, function (el) { io.observe(el); });
  // Last resort: if the observer has not revealed the first screen within a
  // second, reveal everything. A hidden hero costs a sale; the animation does
  // not matter that much.
  setTimeout(function () {
    if (!document.querySelector('.rv.in')) { revealAll(); }
  }, 1000);
})();
"""


def build_page() -> str:
    # The Product/Offer markup tells Google the page sells something. With no
    # payment link the buttons open a prefilled email, so claiming InStock at a
    # price is false - and that false claim is what earned the "Product snippets"
    # and "Merchant listings" structured-data warnings. Google also requires
    # `image` on Product and `seller` on Offer for a merchant listing, so the old
    # block was invalid as well as untrue. Ship it only once checkout is real.
    if PAYMENT_URL:
        product_schema = {
            "@context": "https://schema.org", "@type": "Product",
            "name": PRODUCT,
            "description": DESC,
            "url": CANON,
            "image": [f"{BASE}/og-image.png"],
            "brand": {"@type": "Brand", "name": "Tank Metrics"},
            "offers": {
                "@type": "Offer", "price": "4999", "priceCurrency": "INR",
                "availability": "https://schema.org/InStock", "url": PAYMENT_URL,
                "itemCondition": "https://schema.org/NewCondition",
                "seller": {"@type": "Organization", "name": "Tank Metrics"},
            },
        }
    else:
        product_schema = None
    crumb = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": PRODUCT, "item": CANON},
        ],
    }
    faq_schema = {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer",
                                "text": html.unescape(html.unescape(
                                    __import__("re").sub(r"<[^>]+>", "", a)))}}
            for q, a in FAQ
        ],
    }
    blocks = [b for b in (product_schema, crumb, faq_schema) if b]
    if VIDEO_PRESENT:
        blocks.append({
            "@context": "https://schema.org", "@type": "VideoObject",
            "name": f"{PRODUCT} — walkthrough",
            "description": ("A 45-second screen-by-screen walkthrough of the "
                            "Indian Business Financial Model workbook."),
            "thumbnailUrl": POSTER, "contentUrl": VIDEO,
            "uploadDate": "2026-10-24", "duration": "PT44S",
        })
    ld = "".join(
        '<script type="application/ld+json">'
        + json.dumps(b, ensure_ascii=False, separators=(",", ":"))
        + "</script>" for b in blocks)

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
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
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(TITLE)}">
<meta name="twitter:description" content="{esc(DESC)}">
<meta name="twitter:image" content="{BASE}/og-image.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/site/style.css">
<style>{LP_CSS}</style>
{ld}
</head><body>
<div class="tricolor"></div>
<div class="topbar"><div class="topbar-inner">
<button class="menu-btn" id="menuBtn" type="button" aria-label="Open menu" aria-expanded="false">•••</button>
<div class="brand"><a href="/" class="brand-home-link" style="display:flex;align-items:center;gap:11px;text-decoration:none;color:inherit"><div class="brand-mark"><span class="rs">₹</span></div><div class="brand-text"><span class="brand-name">Tank Metrics</span><p>Simple money calculators, made for beginners</p></div></a></div>
<nav class="toplinks"><a href="/">Home</a> <a href="/news">News</a> <a href="/blog">Blog</a> <a href="/about">About</a> <a href="/digital-products/indian-business-financial-model" class="active">Products</a> <a href="/contact">Contact</a></nav>
</div></div>
<div class="lp">
{hero()}
{strip()}
{problem()}
{demo()}
{sheets_section()}
{video_section()}
{curriculum_section()}
{deliverables()}
{audience_section()}
{steps_section()}
{pricing()}
{unlock_section()}
{faq_section()}
{closing()}
{LP_FOOT}
</div>
{SITE_FOOTER}
<script>{LP_JS}</script>
</body></html>
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_page(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  clean url: {CLEAN}")
    print(f"  video: {'included' if VIDEO_PRESENT else 'MISSING'}")
    print(f"  checkout: {'live' if PAYMENT_URL else 'email fallback (no payment link)'}")


if __name__ == "__main__":
    main()
