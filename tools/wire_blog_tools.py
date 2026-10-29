#!/usr/bin/env python3
"""Link each blog post to the calculators that answer its question.

Sir asked for the blog and the calculators to point at each other. The news
pages already do this (gen_news.py writes a `related` list), and the tool pages
already link to sibling tools, but a blog post linked to nothing: a reader who
finished "What is EBITDA?" had no way to run the number, and the calculator
pages had no editorial context pointing back.

This adds one "Run the numbers" section near the end of every blog post and
back-links it from the matching calculator pages. The mapping is explicit
rather than guessed, because a wrong link is worse than no link: the section
names the tool and says what it answers.

Idempotent: the section carries a `<!-- blog-tools -->` marker, so a second run
changes nothing.

Usage:
    python3 tools/wire_blog_tools.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
TOOLS = SITE / "tools"
URL_MAP = json.loads((ROOT / "tools" / "url-map.json").read_text(encoding="utf-8"))
MARKER = "<!-- blog-tools -->"

# post slug -> [(clean url, tool name, why it is relevant)]
MAP: dict[str, list[tuple[str, str, str]]] = {
    "blog-import-duty-explained": [
        ("/import-duty-and-customs-calculator", "Import Duty & Customs",
         "add customs duty and IGST to your own order value"),
        ("/landed-cost-calculator", "Landed Cost",
         "roll every cost up into the real price of the goods"),
    ],
    "blog-what-is-ebitda": [
        ("/ebitda-and-margin", "EBITDA & Margin",
         "enter your revenue, cost of goods and operating expenses"),
        ("/net-profit-margin", "Net Profit Margin",
         "see what is left after interest and tax"),
    ],
    "blog-ltv-cac-ratio-explained": [
        ("/ltv-cac-ratio", "LTV:CAC Ratio",
         "put your own numbers into the ratio this post explains"),
        ("/customer-acquisition-cost-cac", "Customer Acquisition Cost",
         "work out what one customer really costs you"),
        ("/customer-lifetime-value-ltv", "Customer Lifetime Value",
         "build the LTV figure from your own order value and churn"),
    ],
    "blog-startup-valuation-explained": [
        ("/implied-valuation", "Implied Valuation",
         "turn an offer and a stake into a company value"),
        ("/pre-money-and-post-money-valuation", "Pre-Money & Post-Money",
         "see how a round splits into before and after"),
        ("/revenue-multiple", "Revenue Multiple",
         "compare your valuation with your revenue"),
    ],
    "blog-burn-rate-runway-guide": [
        ("/burn-rate-and-runway", "Burn Rate & Runway",
         "work out how many months your cash still buys"),
        ("/run-rate", "Run Rate",
         "scale a single month to a year"),
    ],
    "blog-marketplace-fees-explained": [
        ("/marketplace-fee-calculator", "Marketplace Fee Calculator",
         "see what a platform commission leaves you"),
        ("/cod-and-rto-loss-calculator", "COD & RTO Loss",
         "price the returns that eat an online seller's margin"),
    ],
    "blog-markup-vs-margin-explained": [
        ("/markup-vs-margin", "Markup vs Margin",
         "get both figures from your cost and selling price"),
        ("/gross-profit-and-margin", "Gross Profit & Margin",
         "see what is left after the direct cost of the sale"),
    ],
    "blog-break-even-point-explained": [
        ("/break-even-point", "Break-Even Point",
         "find the sales level where your profit is zero"),
        ("/contribution-margin", "Contribution Margin",
         "work out how much each sale adds towards fixed costs"),
    ],
    "blog-pharma-distributor-margin-explained": [
        ("/distributor-and-retailer-margin", "Distributor & Retailer Margin",
         "split an MRP into the stockist, retailer and manufacturer prices"),
        ("/mrp-reverse-calculator", "MRP Reverse",
         "work back from an MRP to the cost the pack has to come in at"),
        ("/markup-vs-margin", "Markup vs Margin",
         "see why the same rupee figure is two different percentages"),
    ],
    "blog-discount-impact-on-profit-explained": [
        ("/discount-impact-on-profit", "Discount Impact on Profit",
         "see what a discount leaves of your profit before you announce it"),
        ("/gross-profit-and-margin", "Gross Profit & Margin",
         "get the margin the discount is eating into"),
        ("/break-even-point", "Break-Even Point",
         "find how many extra sales a discount forces you to make"),
    ],
    "blog-boutique-profit-margin-explained": [
        ("/break-even-point", "Break-Even Point",
         "find the pieces you must sell to cover the shop's fixed costs"),
        ("/gross-profit-and-margin", "Gross Profit & Margin",
         "get the margin on a single piece from its price and cost"),
        ("/contribution-margin", "Contribution Margin",
         "see how much each piece adds towards the rent"),
    ],
    "blog-arpu-average-revenue-per-user": [
        ("/arpu-mrr-and-arr", "ARPU, MRR & ARR",
         "put your own revenue and user count into the ARPU formula"),
        ("/customer-lifetime-value-ltv", "Customer Lifetime Value",
         "turn a monthly ARPU into what one user is worth over their whole life"),
        ("/churn-rate", "Churn Rate",
         "measure how fast users leave, which caps what ARPU can earn you"),
    ],
    "blog-franchise-roi-explained": [
        ("/franchise-store-roi", "Franchise / Store ROI",
         "put your own sales, running costs and opening cost into the outlet's return"),
        ("/return-on-investment-roi", "Return on Investment (ROI)",
         "turn any profit and investment into a yearly percentage"),
    ],
}

BACKLINK_MARKER = "<!-- tool-blog -->"


def blog_section(rows: list[tuple[str, str, str]]) -> str:
    items = "".join(
        f'<li><a href="{url}">{name}</a> — {why}.</li>' for url, name, why in rows
    )
    return (
        MARKER
        + '<section class="related-tools blog-tools"><h2>Run the numbers</h2>'
        + "<p>This post explains the idea. These free calculators do the "
        + "arithmetic on your own figures, right in your browser.</p>"
        + f'<ul class="related-list">{items}</ul></section>'
    )


# Words that carry no topic, reused to score a post against a calculator name.
STOP = {
    "blog", "guide", "explained", "explain", "what", "is", "the", "and", "for",
    "of", "to", "in", "on", "a", "an", "how", "why", "your", "you", "with",
    "calculator", "calculation", "calculate", "simple", "first", "time",
    "founders", "founder", "small", "business", "businesses", "india", "indian",
    "vs", "versus", "point", "full", "form", "free", "run", "numbers",
}

# Used when a post's title matches no calculator name: the tools a visitor to
# a small-business finance site is most likely to want next.
DEFAULT_TOOLS = [
    ("/percentage-calculator", "Percentage Calculator"),
    ("/gross-profit-and-margin", "Gross Profit & Margin"),
    ("/break-even-point", "Break-Even Point"),
]


def tools_for_post(slug: str, title: str, slugs: dict[str, str],
                   names: dict[str, str]) -> list[tuple[str, str, str]]:
    """Curated links when the post is in MAP, otherwise the closest tools.

    The daily guide run writes a new post without touching this file, so a
    hand-written map alone would leave every future post with no calculator
    links. This falls back to scoring the post title against the calculator
    names, and then to the category defaults, so the section always exists.
    """
    if slug in MAP:
        return MAP[slug]

    words = {w for w in re.split(r"[^a-z0-9]+", f"{slug} {title}".lower())
             if w and w not in STOP and len(w) > 2}
    scored = []
    for cid, name in names.items():
        name_words = {w for w in re.split(r"[^a-z0-9]+", name.lower()) if w}
        hits = len(words & name_words)
        if hits:
            scored.append((hits, cid))
    scored.sort(key=lambda x: (-x[0], x[1]))
    picks = [cid for _h, cid in scored[:3]]
    if len(picks) < 2:
        return [
            (url, name, "put your own numbers through this calculation")
            for url, name in DEFAULT_TOOLS
        ]
    return [
        (f"/{slugs[cid]}", names[cid],
         "put your own numbers through this calculation")
        for cid in picks
    ]


def clean_url(slug: str) -> str:
    """The public path for a post file.

    The post file is `blog-what-is-ebitda.html` but the site serves it at
    `/what-is-ebitda` (next.config.mjs redirects the `/site/blog-*.html` form,
    and url-map.json holds the clean path). Using the file stem directly
    produced 16 dead links - every one of them a 404 - so the mapping is read
    from url-map.json rather than guessed.
    """
    return URL_MAP.get(f"/{slug}.html") or f"/{slug.removeprefix('blog-')}"


def post_title(text: str) -> str:
    m = re.search(r'<div class="page-hero">.*?<h1>(.*?)</h1>', text, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def main() -> None:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from gen_tool_pages import build_slugs, DATA

    slugs = build_slugs(DATA["calcs"])
    names = {c["id"]: c["name"] for c in DATA["calcs"]}
    changed_posts = 0
    by_tool: dict[str, list[tuple[str, str]]] = {}

    for page in sorted(SITE.glob("blog-*.html")):
        slug = page.stem
        text = page.read_text(encoding="utf-8")
        title = post_title(text)
        rows = tools_for_post(slug, title, slugs, names)
        if not rows:
            print(f"skip (no tools matched): {slug}")
            continue
        for url, _name, _why in rows:
            by_tool.setdefault(url, []).append((slug, title))
        if MARKER in text:
            continue
        anchor = '<footer class="site-footer">'
        idx = text.find(anchor)
        if idx == -1:
            print(f"skip (no footer anchor): {slug}")
            continue
        cut = text.rfind("</div></div>", 0, idx)
        if cut == -1:
            cut = idx
        text = text[:cut] + blog_section(rows) + text[cut:]
        page.write_text(text, encoding="utf-8")
        changed_posts += 1

    changed_tools = 0
    for url, posts in by_tool.items():
        page = TOOLS / f"{url.lstrip('/')}.html"
        if not page.exists():
            continue
        text = page.read_text(encoding="utf-8")
        items = "".join(
            f'<li><a href="{clean_url(slug)}">{title}</a> — the guide behind '
            f"this calculator.</li>"
            for slug, title in posts
        )
        if BACKLINK_MARKER in text:
            # The section already exists, so a new guide has to be merged into
            # it; skipping outright would leave every later post with a
            # one-way link. Only the missing guides are appended.
            m = re.search(
                re.escape(BACKLINK_MARKER) + r".*?<ul class=\"related-list\">(.*?)</ul>",
                text, re.S)
            if not m:
                continue
            have = set(re.findall(r'href="([^"]+)"', m.group(1)))
            extra = "".join(
                f'<li><a href="{clean_url(slug)}">{title}</a> — the guide '
                f"behind this calculator.</li>"
                for slug, title in posts if clean_url(slug) not in have
            )
            if not extra:
                continue
            text = text[: m.end(1)] + extra + text[m.end(1) :]
            page.write_text(text, encoding="utf-8")
            changed_tools += 1
            continue
        section = (
            BACKLINK_MARKER
            + '<section class="related-tools tool-blog"><h2>Read the guide</h2>'
            + f'<ul class="related-list">{items}</ul></section>'
        )
        anchor = '<nav class="tool-nav">'
        if anchor in text:
            text = text.replace(anchor, section + anchor, 1)
        else:
            text = text.replace('<footer class="site-footer">',
                                section + '<footer class="site-footer">', 1)
        page.write_text(text, encoding="utf-8")
        changed_tools += 1

    total_posts = len(list(SITE.glob("blog-*.html")))
    print(f"blog posts linked: {changed_posts}/{total_posts}")
    print(f"calculator pages back-linked: {changed_tools}")


if __name__ == "__main__":
    main()
