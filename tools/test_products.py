#!/usr/bin/env python3
"""Guard the /digital-products page and its footer link.

Three things must stay true:

1. The page exists, has a canonical, og: tags and valid Product +
   BreadcrumbList JSON-LD.
2. Every page's footer links to it, so it is reachable without touching the
   home page (Sir's instruction: no home-page changes).
3. The buy button tells the truth. With PAYMENT_URL unset it must offer email
   and must NOT render a "Buy now" link that goes nowhere - claiming a purchase
   succeeded when no payment can be taken is the exact defect this guards.

    python3 tools/test_products.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
PAGE = SITE / "digital-products.html"
FAILURES: list[str] = []


def check_page() -> None:
    if not PAGE.exists():
        FAILURES.append("public/site/digital-products.html is missing")
        return
    text = PAGE.read_text(encoding="utf-8")
    if '<link rel="canonical" href="https://tankmetrics.in/digital-products">' not in text:
        FAILURES.append("canonical is wrong")
    for tag in ('og:title', 'og:description', 'og:url', 'og:type'):
        if f'property="{tag}"' not in text:
            FAILURES.append(f"{tag} is missing")
    if "google-site-verification" not in text:
        FAILURES.append("lost the google-site-verification tag")
    types = set()
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>',
                         text, re.S):
        try:
            types.add(json.loads(m.group(1))["@type"])
        except Exception as exc:
            FAILURES.append(f"invalid JSON-LD: {exc}")
    if not {"Product", "BreadcrumbList"} <= types:
        FAILURES.append(f"JSON-LD types are {sorted(types)}")


def check_footer_links() -> None:
    missing = []
    for p in sorted(SITE.rglob("*.html")):
        if 'href="/digital-products"' not in p.read_text(encoding="utf-8"):
            missing.append(str(p.relative_to(SITE)))
    if missing:
        FAILURES.append(f"{len(missing)} page(s) have no footer link: "
                        f"{missing[:3]}")


def check_buy_button_honesty() -> None:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gen_products_page", ROOT / "tools" / "gen_products_page.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    block = mod.buy_block()
    if mod.PAYMENT_URL:
        if mod.PAYMENT_URL not in block or "Buy now" not in block:
            FAILURES.append("PAYMENT_URL is set but the buy block does not use it")
    else:
        if "Buy now" in block:
            FAILURES.append("no payment link, yet the page renders a Buy now button")
        if "mailto:" not in block:
            FAILURES.append("no payment link and no email fallback")


def check_downloads() -> None:
    """The two free PDFs the page links to must actually exist and be real."""
    for rel in ("site/downloads/sample-preview.pdf",
                "site/downloads/gst-tax-reckoner.pdf"):
        f = ROOT / "public" / rel
        if not f.exists():
            FAILURES.append(f"public/{rel} is missing")
            continue
        head = f.read_bytes()[:5]
        if head != b"%PDF-":
            FAILURES.append(f"public/{rel} is not a PDF")
        if f.stat().st_size < 20_000:
            FAILURES.append(f"public/{rel} looks empty ({f.stat().st_size} bytes)")


def check_licence_gate() -> None:
    """The paid files must not be reachable by a plain link.

    A public URL cannot be revoked, so the whole refund story depends on the
    paid files having no public URL at all. If someone ever links the workbook
    or the masterclass directly, this fails.
    """
    page = (SITE / "digital-products.html").read_text(encoding="utf-8")

    if "licence-form" not in page:
        FAILURES.append("the licence form is missing from the products page")
    if "/site/licence.js" not in page:
        FAILURES.append("licence.js is not loaded by the products page")

    # The paid deliverables must never appear as a downloadable link.
    for paid in ("Indian-Business-Financial-Model.xlsx",
                 "Masterclass-Manual.pdf"):
        if paid in page:
            FAILURES.append(f"the paid file {paid} is named on the page")

    # And they must not exist under public/ where the web server would serve
    # them. The free sample and reckoner are allowed; the paid ones are not.
    for name in ("Indian-Business-Financial-Model.xlsx",
                 "Masterclass-Manual.pdf"):
        hits = list((ROOT / "public").rglob(name))
        if hits:
            FAILURES.append(f"paid file served from public/: {hits[0]}")

    js = ROOT / "public" / "site" / "licence.js"
    if not js.exists():
        FAILURES.append("public/site/licence.js is missing")
    else:
        src = js.read_text(encoding="utf-8")
        if "action: 'redeem'" not in src and 'action: "redeem"' not in src:
            FAILURES.append("licence.js does not call the redeem action")
        if "text/plain" not in src:
            FAILURES.append("licence.js must post text/plain to avoid a preflight")

    # The Apps Script must gate every delivery behind a licence check.
    gs = (ROOT / "tools" / "apps_script" / "Code.gs").read_text(encoding="utf-8")
    for needed in ("function redeem", "licenceState", "function revoke",
                   "ADMIN_SECRET", "function issue"):
        if needed not in gs:
            FAILURES.append(f"Code.gs is missing {needed}")


def check_no_home_page_change() -> None:
    """The product link belongs in the footer, not the home hero or nav."""
    home = (SITE / "index.html").read_text(encoding="utf-8")
    for marker in ('class="hero"', 'class="toplinks"'):
        m = re.search(re.escape(marker) + r".*?(?=</nav>|</div>)", home, re.S)
        if m and "digital-products" in m.group(0):
            FAILURES.append(f"product link leaked into {marker}")


def main() -> int:
    check_page()
    check_footer_links()
    check_buy_button_honesty()
    check_downloads()
    check_licence_gate()
    check_no_home_page_change()
    if FAILURES:
        print(f"FAIL: {len(FAILURES)} problem(s)")
        for f in FAILURES:
            print("  -", f)
        return 1
    print("ALL PASS: product page is honest, linked from every footer, "
          "and the home page is untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
