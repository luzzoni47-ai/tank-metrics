#!/usr/bin/env python3
"""Guard the product footer columns and the retired /digital-products hub.

The hub page at /digital-products is gone. The product page
(/digital-products/indian-business-financial-model) is now the only page that
sells and delivers the model, and every footer carries it under a Digital
Products heading. Four things must stay true:

1. The retired hub is not a page and not linked anywhere. It redirects. A page
   that still linked it would send the visitor through a redirect and split one
   page's ranking signals across two URLs.
2. Every page's footer carries the product link under a "Digital Products"
   heading, and every footer's Legal column carries the refund policy.
3. The buy button tells the truth. With PAYMENT_URL unset it must offer email
   and must NOT render a "Buy now" link that goes nowhere - claiming a purchase
   succeeded when no payment can be taken is the exact defect this guards.
4. The licence gate stays shut: no paid file is reachable without a key.

    python3 tools/test_products.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
PUBLIC = ROOT / "public"
PRODUCT_PAGE = SITE / "digital-products" / "indian-business-financial-model.html"
PRODUCT_URL = "/digital-products/indian-business-financial-model"
HUB = "/digital-products"
URL_MAP = json.loads((ROOT / "tools" / "url-map.json").read_text(encoding="utf-8"))
FAILURES: list[str] = []


def check_hub_is_retired() -> None:
    if (SITE / "digital-products.html").exists():
        FAILURES.append("the retired hub public/site/digital-products.html is back")
    if HUB in URL_MAP:
        FAILURES.append("url-map.json still maps the retired hub /digital-products")
    linked = [p.relative_to(SITE).as_posix()
              for p in sorted(SITE.rglob("*.html"))
              if f'href="{HUB}"' in p.read_text(encoding="utf-8")]
    if linked:
        FAILURES.append(f"{len(linked)} page(s) still link the retired hub: "
                        f"{linked[:3]}")
    cfg = (ROOT / "next.config.mjs").read_text(encoding="utf-8")
    if f"source: '{HUB}'," not in cfg:
        FAILURES.append("next.config.mjs has no redirect for the retired hub")
    sitemap = (PUBLIC / "sitemap.xml").read_text(encoding="utf-8")
    if f"<loc>https://tankmetrics.in{HUB}</loc>" in sitemap:
        FAILURES.append("the sitemap still lists the retired hub")


def check_product_page() -> None:
    if not PRODUCT_PAGE.exists():
        FAILURES.append("the product page is missing - run tools/gen_landing_page.py")
        return
    text = PRODUCT_PAGE.read_text(encoding="utf-8")
    if f'<link rel="canonical" href="https://tankmetrics.in{PRODUCT_URL}">' not in text:
        FAILURES.append("canonical is wrong")
    for tag in ("og:title", "og:description", "og:url", "og:type"):
        if f'property="{tag}"' not in text:
            FAILURES.append(f"{tag} is missing")
    if "google-site-verification" not in text:
        FAILURES.append("lost the google-site-verification tag")
    types = set()
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>',
                         text, re.S):
        try:
            block = json.loads(m.group(1))
        except Exception as exc:
            FAILURES.append(f"invalid JSON-LD: {exc}")
            continue
        for node in (block if isinstance(block, list) else [block]):
            types.add(node.get("@type"))
    if not {"BreadcrumbList"} <= types:
        FAILURES.append(f"JSON-LD types are {sorted(types)}")
    # Product markup claims the page sells at a price; it must only be present
    # once checkout is live (see test_landing.py).
    m_pay = re.search(r"""var PAYMENT_URL = ['"]([^'"]*)['"]""", text)
    if "Product" in types and not (m_pay and m_pay.group(1)):
        FAILURES.append("a Product schema is shipped while checkout is not live")
    # The breadcrumb must not point at the retired hub.
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>',
                         text, re.S):
        if '"BreadcrumbList"' in m.group(1) and f"{HUB}\"" in m.group(1):
            FAILURES.append("the BreadcrumbList still names the retired hub")


def check_footer_columns() -> None:
    """Every footer carries the product column and a full Legal column."""
    no_product, no_refund, extra = [], [], []
    for p in sorted(SITE.rglob("*.html")):
        t = p.read_text(encoding="utf-8")
        if '<footer class="site-footer">' not in t:
            continue
        rel = p.relative_to(SITE).as_posix()
        if "<h4>Digital Products</h4>" not in t:
            no_product.append(rel)
        if f'href="{PRODUCT_URL}"' not in t:
            no_product.append(rel)
        if "/refund-policy" not in t:
            no_refund.append(rel)
        if t.count("<h4>Digital Products</h4>") > 1:
            extra.append(rel)
    if no_product:
        FAILURES.append(f"{len(no_product)} footer(s) lack the product column: "
                        f"{sorted(set(no_product))[:3]}")
    if no_refund:
        FAILURES.append(f"{len(no_refund)} footer(s) lack the refund policy: "
                        f"{no_refund[:3]}")
    if extra:
        FAILURES.append(f"{len(extra)} page(s) have the product column twice: "
                        f"{extra[:3]}")


def check_buy_button_honesty() -> None:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gen_landing_page", ROOT / "tools" / "gen_landing_page.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    page = PRODUCT_PAGE.read_text(encoding="utf-8")
    if mod.PAYMENT_URL:
        if mod.PAYMENT_URL not in page:
            FAILURES.append("PAYMENT_URL is set but the page does not use it")
    else:
        if "mailto:hello@tankmetrics.in" not in page:
            FAILURES.append("no payment link and no email fallback")
        for label in re.findall(r">\s*(Buy now[^<]*)<", page):
            FAILURES.append(
                f"no payment link, yet the page renders {label.strip()!r}")


def check_licence_gate() -> None:
    """The paid files must not be reachable by a plain link.

    A public URL cannot be revoked, so the whole refund story depends on the
    paid files having no public URL at all. If someone ever links the workbook
    or the masterclass directly, this fails.
    """
    page = PRODUCT_PAGE.read_text(encoding="utf-8")

    if "licence-form" not in page:
        FAILURES.append("the licence form is missing from the product page")
    if "/site/licence.js" not in page:
        FAILURES.append("licence.js is not loaded by the product page")

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
    check_hub_is_retired()
    check_product_page()
    check_footer_columns()
    check_buy_button_honesty()
    check_licence_gate()
    check_no_home_page_change()
    if FAILURES:
        print(f"FAIL: {len(FAILURES)} problem(s)")
        for f in FAILURES:
            print("  -", f)
        return 1
    print("ALL PASS: the hub is retired, every footer sells the product, and "
          "the licence gate stays shut")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
