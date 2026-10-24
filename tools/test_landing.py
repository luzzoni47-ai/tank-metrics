#!/usr/bin/env python3
"""Guard the Indian Business Financial Model landing page.

The page is a sales page, which is exactly the kind of page that drifts into
claims nobody can back up. Four things must stay true:

1. **No invented social proof.** No testimonials, no star ratings, no review
   counts, no "1,000+ founders" counters, no company logos. The product has not
   been reviewed by anyone yet, and a fake rating is both a lie and, under the
   Indian consumer-protection rules on misleading advertising, a liability.
   This check is a deny-list of the words and markup that pattern uses.

2. **Every figure traces to the model.** The numbers in the interactive preview
   must match tools/landing_data.json, which is produced by running the shipped
   workbook. A number typed by hand into the generator would not match and the
   check fails.

3. **The buy button tells the truth.** With no payment link configured it must
   open a prefilled email and must NOT render a live "Buy now" that goes
   nowhere, and must never show a success state.

4. **The page is wired up.** Canonical, OG tags, Product + BreadcrumbList
   JSON-LD, a selector and an FAQ accordion that work, and every internal link
   resolving to a real route.

    python3 tools/test_landing.py
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
SITE = PUBLIC / "site"
PAGE = SITE / "digital-products" / "indian-business-financial-model.html"
DATA = json.loads((ROOT / "tools" / "landing_data.json").read_text(encoding="utf-8"))
URL_MAP = json.loads((ROOT / "tools" / "url-map.json").read_text(encoding="utf-8"))

CLEAN = "/digital-products/indian-business-financial-model"
CANON = f"https://tankmetrics.in{CLEAN}"

STATIC_OK = {
    "/", "/blog", "/news", "/about", "/contact", "/privacy-policy",
    "/terms-and-conditions", "/disclaimer", "/refund-policy",
    "/digital-products",
}

FAILURES: list[str] = []


def text_of(page: str) -> str:
    """Visible text only: script and style bodies stripped, entities decoded."""
    body = re.sub(r"<script.*?</script>", " ", page, flags=re.S)
    body = re.sub(r"<style.*?</style>", " ", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", html.unescape(body))


def check_exists() -> None:
    if not PAGE.exists():
        FAILURES.append(
            "public/site/digital-products/indian-business-financial-model.html "
            "is missing - run python3 tools/gen_landing_page.py")
    elif URL_MAP.get(CLEAN) != "/site/digital-products/indian-business-financial-model.html":
        FAILURES.append(
            f"url-map.json does not map {CLEAN} to the page; clean_urls.py "
            "needs the NESTED_PAGES entry")


def check_no_fake_social_proof() -> None:
    """The page must not claim popularity, praise or ratings it does not have.

    A sales page's whole job is persuasion, so this is the check that matters
    most. Each pattern below is something the page could plausibly grow into
    later - a testimonial block, a star widget, a "trusted by" logo row.
    """
    page = PAGE.read_text(encoding="utf-8")
    visible = text_of(page).lower()

    banned_words = {
        r"\btestimonial": "a testimonial block",
        r"\bstar rating": "a star rating claim",
        r"\b\d(?:\.\d)?\s*(?:/|out of)\s*5\b": "a rating out of five",
        r"\brated\s+\d": "a numeric rating",
        # A popularity counter. The quantity must read as a total ("1,000+",
        # "join 500", "over 2,000"), not as a threshold in a price rule such as
        # "the first 50 buyers", which is a factual statement about pricing.
        r"\b\d[\d,]*\+\s*(?:happy\s+)?(?:customers|buyers|users|founders|businesses)\b":
            "a customer counter",
        r"\b(?:join|trusted by|over|more than|used by)\s+\d[\d,]*\+?\s*"
        r"(?:happy\s+)?(?:customers|buyers|users|founders|businesses)\b":
            "a customer counter",
        r"\btrusted by\b": "a 'trusted by' claim",
        r"\bas seen (?:in|on)\b": "an 'as seen in' claim",
        r"\bloved by\b": "a 'loved by' claim",
        r"\bbest ?seller\b": "a bestseller claim",
        r"\bno\.?\s*1\b": "a number-one claim",
        r"\baward[- ]winning\b": "an award claim",
        r"\bcase studies? of (?:our )?(?:happy )?customers\b": "a case-study claim",
    }
    for pattern, what in banned_words.items():
        m = re.search(pattern, visible)
        if m:
            FAILURES.append(
                f"the page carries {what} ({m.group(0)!r}); the product has no "
                "reviews yet and must not imply any")

    # Markup that only exists to display a rating or a testimonial.
    markup = {
        r'itemprop=["\']ratingValue': "an aggregate rating in structured data",
        r'itemprop=["\']reviewCount': "a review count in structured data",
        r'"@type"\s*:\s*"AggregateRating"': "an AggregateRating JSON-LD block",
        r'"@type"\s*:\s*"Review"': "a Review JSON-LD block",
        r'class="[^"]*testimonial': "a testimonial element",
        r'class="[^"]*star-rating': "a star-rating element",
    }
    for pattern, what in markup.items():
        if re.search(pattern, page, re.I):
            FAILURES.append(f"the page contains {what}, which is fabricated social proof")


def check_figures_match_the_model() -> None:
    """The preview numbers must be the model's own output, not typed in.

    landing_data.json is written by running the shipped workbook once per
    business type. If a figure on the page disagrees with it, the page is
    quoting a number the model does not produce.
    """
    page = PAGE.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="lp-data">(.*?)</script>',
                  page, re.S)
    if not m:
        FAILURES.append("the interactive preview has no data block")
        return
    try:
        payload = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        FAILURES.append(f"the preview data block is not valid JSON: {exc}")
        return

    types = DATA["business_types"]
    if set(payload) != set(types):
        FAILURES.append(
            f"the preview covers {sorted(payload)} but the model was run for "
            f"{sorted(types)}")
        return

    def short(v: float) -> str:
        a = abs(v)
        if a >= 1_00_00_000:
            return f"{v / 1_00_00_000:.2f} Cr"
        if a >= 1_00_000:
            return f"{v / 1_00_00_000:.2f} Cr" if a >= 1_00_00_000 else f"{v / 1_00_000:.2f} L"
        return f"{v:,.0f}"

    for t, row in types.items():
        got = payload[t]
        for key, field in (("revenue", "revenue_month_60"),
                           ("ebitda", "ebitda_month_60"),
                           ("cash", "cash_month_60"),
                           ("breakeven", "break_even_revenue_month"),
                           ("valuation", "valuation_blended")):
            want = short(float(row[field]))
            if got.get(key) != want:
                FAILURES.append(
                    f"{t}: the page shows {key}={got.get(key)!r} but the model "
                    f"produces {want!r} - regenerate landing_data.json")

    if "illustrative" not in text_of(page).lower():
        FAILURES.append("the sample figures are not labelled as illustrative")


def check_buy_button_honesty() -> None:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gen_landing_page", ROOT / "tools" / "gen_landing_page.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    page = PAGE.read_text(encoding="utf-8")
    if mod.PAYMENT_URL:
        if mod.PAYMENT_URL not in page:
            FAILURES.append("PAYMENT_URL is set but the page does not use it")
    else:
        if "mailto:hello@tankmetrics.in" not in page:
            FAILURES.append("no payment link and no email fallback")
        for label in re.findall(r">\s*(Buy now[^<]*)<", page):
            FAILURES.append(
                f"no payment link, yet the page renders {label.strip()!r}")

    # A fake success state is the other half of the same defect.
    for bad in ("Payment successful", "Thank you for your purchase",
                "Order confirmed", "payment received"):
        if bad.lower() in page.lower():
            FAILURES.append(f"the page shows a fake success state: {bad!r}")

    if mod.PAYMENT_URL is None and "Checkout is being finalised" not in page:
        FAILURES.append("the page does not tell the buyer that checkout is pending")


def check_head_and_schema() -> None:
    page = PAGE.read_text(encoding="utf-8")
    if f'<link rel="canonical" href="{CANON}">' not in page:
        FAILURES.append("canonical is wrong")
    for tag in ("og:title", "og:description", "og:url", "og:type"):
        if f'property="{tag}"' not in page:
            FAILURES.append(f"{tag} is missing")
    if "google-site-verification" not in page:
        FAILURES.append("lost the google-site-verification tag")

    title = html.unescape(re.search(r"<title>(.*?)</title>", page, re.S).group(1)).strip()
    if not 10 <= len(title) <= 65:
        FAILURES.append(f"title is {len(title)} chars, expected 10-65")
    desc = html.unescape(
        re.search(r'<meta name="description" content="([^"]*)"', page).group(1))
    if not 50 <= len(desc) <= 165:
        FAILURES.append(f"description is {len(desc)} chars, expected 50-165")
    og = dict(re.findall(r'<meta property="(og:[a-z]+)" content="([^"]*)"', page))
    if og.get("og:title") and html.unescape(og["og:title"]) != title:
        FAILURES.append("og:title differs from <title>")

    types = set()
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>',
                         page, re.S):
        try:
            block = json.loads(m.group(1))
        except json.JSONDecodeError as exc:
            FAILURES.append(f"invalid JSON-LD: {exc}")
            continue
        for node in (block if isinstance(block, list) else [block]):
            types.add(node.get("@type"))
    for needed in ("Product", "BreadcrumbList", "FAQPage"):
        if needed not in types:
            FAILURES.append(f"JSON-LD has no {needed} block (found {sorted(types)})")
    if "VideoObject" in types and not (SITE / "video" / "walkthrough.mp4").exists():
        FAILURES.append("a VideoObject is declared but the video file is missing")

    # A Product offer must not invent a rating.
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>',
                         page, re.S):
        if "aggregateRating" in m.group(1):
            FAILURES.append("the Product schema carries an aggregateRating")


def check_interactions() -> None:
    page = PAGE.read_text(encoding="utf-8")
    if 'role="tablist"' not in page or page.count('role="tab"') < 5:
        FAILURES.append("the business-type selector is not a real tab list")
    if not re.search(r'aria-selected="true"', page):
        FAILURES.append("no tab is marked selected")
    if "<details" not in page or "<summary" not in page:
        FAILURES.append("the FAQ is not an accordion")
    if "IntersectionObserver" not in page:
        FAILURES.append("the reveal animation has no observer")
    if "prefers-reduced-motion" not in page:
        FAILURES.append("the animation ignores prefers-reduced-motion")
    # The reveal must be opt-in. If `.rv` were hidden in plain CSS, one script
    # error would leave the whole page blank - unacceptable on a sales page.
    css = (ROOT / "tools" / "landing_style.py").read_text(encoding="utf-8")
    if re.search(r"^\.lp \.rv\{opacity:0", css, re.M):
        FAILURES.append(
            "the reveal CSS hides content by default; it must be scoped under "
            ".lp-anim so the page renders without JavaScript")
    if ".lp-anim .rv{opacity:0" not in css:
        FAILURES.append("the reveal animation has no opt-in class")
    if "classList.add('lp-anim')" not in page:
        FAILURES.append("the script never opts in to the reveal animation")


def check_hero_clears_the_header() -> None:
    """On mobile the topbar is position:fixed and floats over the page.

    The other pages get away with it because their hero is a pale gradient that
    hides the overlap. This hero is near-black, so anything inside the top 71px
    is visibly sliced in half - the first version of the page clipped its own
    badge.

    This reads the CSS out of the GENERATED page, not out of landing_style.py.
    That distinction matters: a stale __pycache__ entry once kept serving the
    old 52px rule while the source said 96px, so a check on the source passed
    while the shipped page was still broken. Verify the artifact.
    """
    page = PAGE.read_text(encoding="utf-8")
    m = re.search(r"<style>(.*?)</style>", page, re.S)
    if not m:
        FAILURES.append("the page carries no inline stylesheet")
        return
    css = m.group(1)

    media = re.search(r"@media \(max-width:760px\)\{(.*?)\n\}", css, re.S)
    if not media:
        FAILURES.append("no mobile breakpoint in the page's own stylesheet")
        return
    pad = re.search(r"\.lp \.hero\{padding:(\d+)px", media.group(1))
    if not pad:
        FAILURES.append("the mobile hero has no explicit top padding")
        return
    # The topbar is 71px on mobile; require it cleared with room to spare.
    if int(pad.group(1)) < 90:
        FAILURES.append(
            f"the shipped page pads the mobile hero only {pad.group(1)}px from "
            "the top, but the fixed header is 71px tall - the hero will be "
            "clipped (is landing_style.py shadowed by a stale __pycache__?)")


def check_links() -> None:
    page = PAGE.read_text(encoding="utf-8")
    for href in sorted(set(re.findall(r'href="(/[^"#?]*)"', page))):
        if href in ("/",) or href in STATIC_OK:
            continue
        if href in URL_MAP:
            continue
        if href.startswith("/site/"):
            if (PUBLIC / href.lstrip("/")).exists():
                continue
        FAILURES.append(f"the page links to {href}, which is not a real route")
    # No placeholder anchors left behind.
    for bad in ('href="#"', 'href=""', "TODO", "PLACEHOLDER", "lorem ipsum"):
        if bad.lower() in page.lower():
            FAILURES.append(f"the page still contains {bad!r}")


def check_video_claim() -> None:
    """If the page promises a video, the video must be a real file.

    And the page must not describe it as something it is not: the walkthrough is
    rendered from the model's own sheet data, not captured as a screen
    recording, so it must not say "screen recording" or "recorded".
    """
    page = PAGE.read_text(encoding="utf-8")
    says_video = bool(re.search(r'<video\b', page))
    exists = (SITE / "video" / "walkthrough.mp4").exists()
    if says_video and not exists:
        FAILURES.append("the page embeds a video that is not in public/site/video/")
    if not says_video and "Video walkthrough" in text_of(page):
        FAILURES.append("the page promises a video walkthrough but embeds none")
    if exists:
        for name in ("walkthrough.mp4", "walkthrough.webm", "walkthrough.jpg"):
            p = SITE / "video" / name
            if not p.exists():
                FAILURES.append(f"the video asset {name} is missing")
            elif p.stat().st_size < 4096:
                FAILURES.append(f"the video asset {name} looks empty")

    visible = text_of(page).lower()
    for claim in ("screen recording", "recorded screen", "screen-recorded",
                  "actual screen capture", "screen capture of"):
        if claim in visible:
            FAILURES.append(
                f"the page calls the walkthrough a {claim!r}, but it is rendered "
                "from the model's sheet data rather than captured from a screen")


def check_paid_files_never_linked() -> None:
    page = PAGE.read_text(encoding="utf-8")
    for paid in ("Indian-Business-Financial-Model.xlsx", "Masterclass-Manual.pdf"):
        if paid in page:
            FAILURES.append(f"the paid file {paid} is named on the page")


def main() -> int:
    if not PAGE.exists():
        check_exists()
        print(f"FAIL: {len(FAILURES)} problem(s)")
        for f in FAILURES:
            print("  -", f)
        return 1
    check_exists()
    check_no_fake_social_proof()
    check_figures_match_the_model()
    check_buy_button_honesty()
    check_head_and_schema()
    check_interactions()
    check_hero_clears_the_header()
    check_links()
    check_video_claim()
    check_paid_files_never_linked()
    if FAILURES:
        print(f"FAIL: {len(FAILURES)} problem(s)")
        for f in FAILURES:
            print("  -", f)
        return 1
    print("ALL PASS: the landing page is honest, wired up, and its figures come "
          "from the model")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
