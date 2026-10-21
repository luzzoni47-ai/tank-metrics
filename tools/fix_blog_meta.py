#!/usr/bin/env python3
"""Bring every blog post's head up to the SEO/social rules.

Three defects were live on all six guides:

* no `og:title` / `og:description` / `og:url` / `og:type`, so Facebook and
  WhatsApp fell back to a generic card instead of the article headline;
* `twitter:title` / `twitter:description` still carried the site-wide default
  ("Tank Metrics — Free Business Calculators");
* `<title>` and meta description ran past what Google renders (69-78 and
  166-168 chars), so the search result was truncated mid-sentence.

The social traffic this site is built to convert arrives as a shared link, so a
generic preview card costs real clicks. Re-running is safe: values are set, not
appended.

    python3 tools/fix_blog_meta.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
BASE = "https://tankmetrics.in"
BRAND = "Tank Metrics"
TITLE_MAX = 60
DESC_MIN, DESC_MAX = 150, 158

# slug -> (title without brand, meta description)
FIX = {
    "burn-rate-runway-guide": (
        "Burn Rate and Runway Explained",
        "Gross vs net burn rate explained, the runway formula with a worked example, and how to extend your startup's runway without gutting the whole business.",
    ),
    "ltv-cac-ratio-explained": (
        "LTV:CAC Ratio Explained: The 3:1 Rule",
        "How to calculate customer lifetime value and customer acquisition cost, why 3:1 is the LTV:CAC benchmark, and what your number says about your business.",
    ),
    "marketplace-fees-explained": (
        "Marketplace Fees Explained for Sellers",
        "Marketplace fees explained for Indian sellers: what Amazon and Flipkart actually charge, and why an ₹800 sale on a marketplace can pay you only ₹580 today.",
    ),
    "markup-vs-margin-explained": (
        "Markup vs Margin: Why ₹8,000 Earns 50%",
        "Markup and margin come from the same sale but never match. A ₹4,000 cost, an ₹8,000 price — and why a 50% margin is really a 100% markup every single time.",
    ),
    "startup-valuation-explained": (
        "Startup Valuation: Pre-Money vs Post-Money",
        "Pre-money and post-money valuation with a worked example: an investor offers 50 lakh for 5%, and how to check the dilution math yourself in one minute.",
    ),
    "what-is-ebitda": (
        "What Is EBITDA? A Simple Guide for Founders",
        "EBITDA explained in plain English: what it stands for, the formula, a worked example in rupees, and why investors always ask about it first of everything.",
    ),
}

TITLE_TAG = re.compile(r"<title>.*?</title>", re.S)
DESC_TAG = re.compile(r'<meta name="description" content="[^"]*">')
OG_TITLE = re.compile(r'<meta property="og:title" content="[^"]*">')
OG_DESC = re.compile(r'<meta property="og:description" content="[^"]*">')
OG_TYPE = re.compile(r'<meta property="og:type" content="[^"]*">')
OG_URL = re.compile(r'<meta property="og:url" content="[^"]*">')
TW_TITLE = re.compile(r'<meta name="twitter:title" content="[^"]*">')
TW_DESC = re.compile(r'<meta name="twitter:description" content="[^"]*">')


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def main() -> None:
    bad = 0
    for slug, (head, desc) in FIX.items():
        title = f"{head} | {BRAND}"
        if len(title) > TITLE_MAX:
            print(f"FAIL {slug}: title {len(title)} chars")
            bad += 1
        if not (DESC_MIN <= len(desc) <= DESC_MAX):
            print(f"FAIL {slug}: description {len(desc)} chars")
            bad += 1
    if bad:
        raise SystemExit(f"{bad} value(s) out of range — fix before writing")

    for slug, (head, desc) in FIX.items():
        f = SITE / f"blog-{slug}.html"
        if not f.exists():
            print(f"  SKIP missing: {f.name}")
            continue
        t = f.read_text(encoding="utf-8")
        title = f"{head} | {BRAND}"
        canon = f"{BASE}/{slug}"
        e_title, e_desc = esc(title), esc(desc)
        t = TITLE_TAG.sub(f"<title>{e_title}</title>", t, count=1)
        t = DESC_TAG.sub(f'<meta name="description" content="{e_desc}">', t, count=1)
        t = TW_TITLE.sub(f'<meta name="twitter:title" content="{e_title}">', t, count=1)
        t = TW_DESC.sub(f'<meta name="twitter:description" content="{e_desc}">', t, count=1)
        if OG_TITLE.search(t):
            t = OG_TITLE.sub(f'<meta property="og:title" content="{e_title}">', t, count=1)
        if OG_DESC.search(t):
            t = OG_DESC.sub(f'<meta property="og:description" content="{e_desc}">', t, count=1)
        if OG_TYPE.search(t):
            t = OG_TYPE.sub('<meta property="og:type" content="article">', t, count=1)
        if OG_URL.search(t):
            t = OG_URL.sub(f'<meta property="og:url" content="{canon}">', t, count=1)
        # Insert anything the head never had, right after the canonical.
        extra = ""
        if not OG_TITLE.search(t):
            extra += f'<meta property="og:title" content="{e_title}">'
        if not OG_DESC.search(t):
            extra += f'<meta property="og:description" content="{e_desc}">'
        if not OG_TYPE.search(t):
            extra += '<meta property="og:type" content="article">'
        if not OG_URL.search(t):
            extra += f'<meta property="og:url" content="{canon}">'
        if extra:
            t = re.sub(r'(<link rel="canonical"[^>]*>)', r"\1" + extra, t, count=1)
        f.write_text(t, encoding="utf-8")
        print(f"  fixed {f.name}  title={len(title)} desc={len(desc)}")
    print("\ndone")


if __name__ == "__main__":
    main()
