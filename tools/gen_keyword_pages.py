#!/usr/bin/env python3
"""Generate the keyword-targeted calculator pages (blog-<slug>.html).

The 30-page plan (see tools/keyword_pages.json) targets queries the site has no
page for yet - "shark tank valuation calculator in crores", "burn rate
calculator india", and so on. Each one is a real, working calculator plus a
700-word Hinglish/English article, not a thin doorway page: thin duplicates are
exactly what stopped Google indexing the rest of the site (see the daily SEO
runbook).

The file is `blog-<slug>.html`, so clean_urls.py gives it the clean URL
`/<slug>` - the exact URL the 30-page plan specifies. An earlier revision wrote
`blog-keyword-<slug>.html`, which cleaned to `/keyword-<slug>`; that prefix
matched neither the plan nor the query, and none of those URLs was ever indexed,
so they now 301 to the clean form (next.config.mjs).

Why the existing blog pipeline and not a brand-new family: it already gives a
page in this shape its clean URL (clean_urls.py), its
sitemap entry (wire_crawl_graph.py), Article + BreadcrumbList schema
(add_blog_schema.py), the "Run the numbers" cross-links (wire_blog_tools.py),
the PWA shell (add_pwa.py) and the language toggle. Reusing it means a new page
is wired into the crawl graph by construction instead of by hand.

The shell is copied verbatim from gen_news.py so a page here looks like every
other page on the site.

Usage:
    python3 tools/gen_keyword_pages.py            # all pages
    python3 tools/gen_keyword_pages.py --only 1 2 # just page_01 and page_02
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_tool_pages import ACCENTS, DATA, field_html  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
PAGES = json.loads((Path(__file__).parent / "keyword_pages.json").read_text(encoding="utf-8"))
BASE = "https://tankmetrics.in"
CTA = "Try Free on TankMetrics.in"

CATNAMES = {x["id"]: x["name"] for x in DATA["cats"]}

TOP_NAV = (
    '<nav class="toplinks"><a href="/">Home</a> '
    '<a href="/news">News</a> <a href="/blog" class="active">Blog</a> '
    '<a href="/about">About</a> <a href="/contact">Contact</a></nav>'
)

HEAD = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">\
<link rel="icon" href="/site/favicon.ico" sizes="any">\
<link rel="icon" href="/site/favicon.svg" type="image/svg+xml">\
<link rel="icon" href="/site/favicon.png" type="image/png" sizes="192x192">\
<link rel="apple-touch-icon" href="/site/favicon.png" sizes="192x192">\
<link rel="manifest" href="/site/manifest.webmanifest">\
<meta name="google-site-verification" content="CyIhu9CYYQapfzYJOeSLTP_XY_HWq0McbmY4uX342o4">\
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\
<title>{title}</title>\
<meta name="description" content="{desc}">\
<link rel="canonical" href="{canonical}">\
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">\
<meta name="theme-color" content="#FF9933">\
<link rel="preconnect" href="https://fonts.googleapis.com">\
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\
<link href="https://fonts.googleapis.com/css2?family=Gloock&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">\
<link rel="stylesheet" href="/site/style.css">\
<meta property="og:type" content="article">\
<meta property="og:title" content="{title}">\
<meta property="og:description" content="{desc}">\
<meta property="og:url" content="{canonical}">\
<meta property="og:image" content="{base}/og-image.png">\
<meta property="og:image:width" content="1200">\
<meta property="og:image:height" content="630">\
<meta property="og:site_name" content="Tank Metrics">\
<meta name="twitter:card" content="summary_large_image">\
<meta name="twitter:title" content="{title}">\
<meta name="twitter:description" content="{desc}">\
<meta name="twitter:image" content="{base}/og-image.png">\
<script type="application/ld+json">{faq_ld}</script>\
<script type="application/ld+json">{app_ld}</script>\
<script async src="https://www.googletagmanager.com/gtag/js?id=G-MHZ0V6HFC6"></script>\
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}\
gtag('js',new Date());gtag('config','G-MHZ0V6HFC6');</script>\
</head>"""

TOPBAR = (
    '<body><div class="tricolor"></div><div class="topbar"><div class="topbar-inner">'
    '<button class="menu-btn" id="menuBtn" aria-label="Menu" style="visibility:hidden">☰</button>'
    '<div class="brand"><a href="/" style="display:flex;align-items:center;gap:11px;'
    'text-decoration:none;color:inherit"><div class="brand-mark"><span class="rs">₹</span></div>'
    '<div class="brand-text"><span class="brand-name">Tank Metrics</span>'
    '<p>Simple money calculators, made for beginners</p></div></a></div>'
    + TOP_NAV +
    '</div></div>'
)

FOOTER = (
    '<footer class="site-footer"><div class="footer-grid"><div class="footer-col">'
    '<h4>Tank Metrics</h4><p>100+ free business calculators for entrepreneurs, students and '
    'small business owners. Everything is calculated right in your browser — nothing you type '
    'is ever sent anywhere.</p></div><div class="footer-col"><h4>Company</h4><ul>'
    '<li><a href="/about">About Us</a></li><li><a href="/blog">Blog</a></li>'
    '<li><a href="/news">News</a></li><li><a href="/contact">Contact Us</a></li></ul></div>'
    '<div class="footer-col"><h4>Legal</h4><ul><li><a href="/privacy-policy">Privacy Policy</a></li>'
    '<li><a href="/terms-and-conditions">Terms and Conditions</a></li>'
    '<li><a href="/refund-policy">Refund Policy</a></li>'
    '<li><a href="/disclaimer">Disclaimer</a></li></ul></div>'
    '<div class="footer-col"><h4>Popular</h4><ul><li><a href="/#cat_val">Valuation &amp; Deals</a></li>'
    '<li><a href="/#cat_cust">Unit Economics</a></li>'
    '<li><a href="/#cat_everyday">Everyday Money</a></li></ul></div>'
    '<div class="footer-col"><h4>Digital Products</h4><ul>'
    '<li><a href="/digital-products/indian-business-financial-model">Indian Business '
    'Financial Model</a></li></ul></div></div>'
    '<div class="footer-bottom"><span>© <span id="year"></span> Tank Metrics. Built for learning '
    'and quick estimates — for big decisions, always check with a qualified accountant or '
    'financial advisor.</span> <span>Made with <svg class="footer-heart" viewBox="0 0 24 24" '
    'aria-hidden="true" focusable="false"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 '
    '2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 '
    '8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg> in Bangalore, India</span></div></footer>'
    '<script>document.getElementById("year").textContent=(new Date).getFullYear()</script>'
)

TOGGLE_SCRIPT = """<script>(function(){
  var b=document.getElementById("langToggle");
  if(!b)return;
  var badge=b.querySelector(".lang-badge");
  var lab=b.querySelector(".lang-toggle-label");
  var en=document.querySelector('.post-lang[data-lang="en"]');
  var hing=document.querySelector('.post-lang[data-lang="hinglish"]');
  if(!en||!hing)return;
  var hinglish=false;
  function render(){
    en.hidden=hinglish;
    hing.hidden=!hinglish;
    lab.textContent=hinglish?"English":"Hinglish";
    if(badge)badge.textContent=hinglish?"A":"H";
    b.title=hinglish?"Read in English":"Read in Hinglish";
    document.documentElement.lang=hinglish?"hi-Latn":"en";
    b.setAttribute("aria-pressed",hinglish?"true":"false");
  }
  b.addEventListener("click",function(){hinglish=!hinglish;render();});
})();</script>"""

RUN_SCRIPT = """<script>{helpers}
var COMPUTE={compute};
function run(){{var e={{}};document.querySelectorAll('[data-k]').forEach(function(i){{e[i.dataset.k]=i.value;}});var r;try{{r=COMPUTE(e);}}catch(err){{r={{rows:[{{l:'Result',v:'—'}}]}};}}var o=document.getElementById('out');o.innerHTML=(r.rows||[]).map(function(x){{return '<div class="r"><span class="l">'+x.l+'</span><span class="v'+(x.cls?' '+x.cls:'')+'">'+x.v+'</span></div>';}}).join('')
+(r.tip?'<div class="benchmark"><b>Tip:</b> '+r.tip+'</div>':'');}}
function reflect(i){{if(i.dataset.unit!=='\u20b9')return;var raw=i.value,n=parseAmount(raw);
var f=i.closest('.field'),box=f&&f.querySelector('.amt-hint');
if(!raw.trim()||isNaN(n)||!/[a-z]/i.test(raw)){{if(box)box.remove();return;}}
if(!box){{box=document.createElement('span');box.className='amt-hint';box.setAttribute('aria-live','polite');f.appendChild(box);}}
box.textContent='= \u20b9'+fmtIN(n,0);}}
document.querySelectorAll('[data-k]').forEach(function(i){{i.addEventListener('input',function(){{reflect(i);run();}});reflect(i);}});
document.getElementById('clearBtn').addEventListener('click',function(){{document.querySelectorAll('[data-k]').forEach(function(i){{i.value='';}});run();}});
run();
</script>"""


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def content_blocks(c: dict) -> list[str]:
    """The article body: hook, what, formula, worked example, how-to, why-india."""
    out: list[str] = []
    out.append(f'<p>{c["hook"]}</p>')

    out.append(f'<h2>What is {esc(c["keyword"])}?</h2>')
    out.extend(f"<p>{p}</p>" for p in c["what"])

    f = c["formula"]
    out.append("<h2>Formula</h2>")
    out.append(
        '<div class="formula"><span class="lbl">The formula</span>'
        f'<code>{esc(f["expr"])}</code><p class="formula-note">{f["note"]}</p></div>'
    )

    ex = c["example"]
    out.append("<h2>Worked Example (in ₹ Crores)</h2>")
    out.append(f'<p>{ex["intro"]}</p>')
    head = "".join(f"<th>{esc(h)}</th>" for h in ex["table"]["headers"])
    rows = "".join(
        "<tr>" + "".join(f"<td>{esc(v)}</td>" for v in r) + "</tr>"
        for r in ex["table"]["rows"]
    )
    out.append(f"<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>")
    out.append(f'<p>{ex["outro"]}</p>')

    out.append("<h2>How to Use the Tank Metrics Calculator</h2>")
    steps = "".join(
        f'<li><strong>{esc(t)}</strong> {esc(d)}</li>' for t, d in c["steps"]
    )
    out.append(f'<ol class="keyword-steps">{steps}</ol>')

    out.append("<h2>Why Indian Calculation is Different (US vs India)</h2>")
    out.extend(f"<p>{p}</p>" for p in c["why_india"])

    if c.get("mistakes"):
        out.append("<h2>Common Mistakes</h2>")
        items = "".join(f"<li>{esc(m)}</li>" for m in c["mistakes"])
        out.append(f'<ul class="plain-list">{items}</ul>')

    if c.get("comparison"):
        cm = c["comparison"]
        out.append("<h2>Before TankMetrics vs After TankMetrics</h2>")
        head = "".join(f"<th>{esc(h)}</th>" for h in cm["headers"])
        rows = "".join(
            "<tr>" + "".join(f"<td>{esc(v)}</td>" for v in r) + "</tr>"
            for r in cm["rows"]
        )
        out.append(f"<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>")
    return out


def faq_ld(c: dict) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in c["faqs"]
        ],
    }


def app_ld(c: dict) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": c["title"].split(" - ")[0],
        "url": f"{BASE}/{c['slug']}",
        "applicationCategory": "FinanceApplication",
        "operatingSystem": "All",
        "browserRequirements": "Requires JavaScript",
        "description": c["description"],
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "INR"},
        "isAccessibleForFree": True,
        "publisher": {"@type": "Organization", "name": "Tank Metrics", "url": BASE},
    }


def card(c: dict) -> str:
    accent = ACCENTS.get(c.get("color", "blue"), "#4285F4")
    fields = "".join(field_html(f"kw{c['num']}", i) for i in c["calculator"]["inputs"])
    faq_html = "".join(
        f"<h3>{esc(q)}</h3><p>{esc(a)}</p>" for q, a in c["faqs"]
    )
    related = "".join(
        f'<li><a href="{u}">{esc(n)}</a></li>' for u, n in c["related"]
    )
    return (
        f'<div class="card" style="--accent:{accent}">'
        f'<div class="card-title"><h2>{esc(c["calculator"]["name"])}</h2>'
        '<button class="clear-btn" id="clearBtn" type="button">Clear</button></div>'
        f'<div class="inputs">{fields}</div><div class="readout" id="out"></div></div>'
        f'<section class="related-tools"><h2>Related free calculators</h2>'
        f'<ul class="related-list">{related}</ul></section>'
        f'<h2>Frequently asked questions</h2>{faq_html}'
    )


def page(c: dict) -> str:
    slug = c["slug"]
    # Point the canonical at the FILE path: clean_urls.py rewrites
    # /site/blog-<slug>.html -> /<slug> from url-map.json, the same way it does
    # for every other page. Naming the clean path directly would leave the
    # canonical as the only un-rewritten URL on the page.
    canonical = f"{BASE}/site/blog-{slug}.html"
    title = c["title"]
    desc = c["description"]
    en = "\n".join(content_blocks(c))
    hinglish = "\n".join(c["hinglish_blocks"])
    tail = (
        f'<div class="cta-inline"><p>{esc(c["cta"])}</p>'
        f'<a class="btn-primary" href="/">{CTA} →</a></div>'
    )
    head = HEAD.format(
        title=html.escape(title), desc=html.escape(desc), canonical=canonical,
        base=BASE,
        faq_ld=json.dumps(faq_ld(c), ensure_ascii=False),
        app_ld=json.dumps(app_ld(c), ensure_ascii=False),
    )
    body = (
        TOPBAR
        + '<div class="main" style="max-width:1280px;margin:0 auto">'
        + f'<div class="page-hero"><div class="tag">🧮 {esc(CATNAMES.get(c["cat"], "Money"))}</div>'
        + f'<h1>{esc(c["h1"])}</h1><p>{esc(c["description"])}</p></div>'
        + '<div class="page-wrap"><div class="post-meta">'
        + f'<span class="tag2">{esc(CATNAMES.get(c["cat"], "Money"))}</span>'
        + f'<span>{c["date_display"]}</span>'
        + '<button class="lang-toggle" id="langToggle" type="button" aria-pressed="false" '
          'title="Read in Hinglish"><span class="lang-badge" aria-hidden="true">H</span>'
          '<span class="lang-toggle-label">Hinglish</span></button></div>'
        + card(c)
        + f'<div class="post-lang" data-lang="en">{en}{tail}</div>'
        + f'<div class="post-lang" data-lang="hinglish" lang="hi-Latn" hidden>{hinglish}{tail}</div>'
        + '<nav class="tool-nav"><a href="/blog">← All guides</a>'
          '<a href="/">All calculators →</a></nav>'
        + '</div></div>'
        + FOOTER + TOGGLE_SCRIPT
        + RUN_SCRIPT.format(helpers=DATA["helpers"], compute=c["calculator"]["compute"])
        + '</body></html>'
    )
    return head + body


def blog_cards(pages: list[dict]) -> int:
    """Add a listing card for each keyword page to the /blog Guides grid.

    gen_news.py rewrites the news grid on every run but leaves the Guides grid
    alone, so the cards are inserted here rather than hand-edited. Idempotent:
    a card whose clean href is already present is skipped, so re-running the
    pipeline never duplicates one.
    """
    listing = SITE / "blog.html"
    if not listing.exists():
        return 0
    text = listing.read_text(encoding="utf-8")
    marker = '</div></div><div id="paneNews"'
    if marker not in text:
        return 0
    cards = ""
    for c in pages:
        href = f"/{c['slug']}"
        # An earlier revision linked the /keyword-<slug> form; drop that stale
        # card so the listing does not carry two links to the same page.
        stale = f'<a class="blog-card" href="/keyword-{c["slug"]}"'
        if stale in text:
            text = text[:text.index(stale)] + text[text.index("</a>", text.index(stale)) + 4:]
        if f'href="{href}"' in text:
            continue
        accent = ACCENTS.get(c.get("color", "blue"), "#4285F4")
        cat = CATNAMES.get(c["cat"], "Money")
        cards += (
            f'<a class="blog-card" href="{href}" style="border-top-color:{accent}">'
            f'<span class="cat">{esc(cat)}</span>'
            f'<h2>{esc(c["h1"].split(" - ")[0])}</h2>'
            f'<p>{esc(c["description"])}</p>'
            '<span class="readmore">Read the guide →</span></a>'
        )
    if not cards:
        return 0
    listing.write_text(text.replace(marker, cards + marker, 1), encoding="utf-8")
    return len(pages)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", type=int, default=None)
    args = ap.parse_args()
    SITE.mkdir(parents=True, exist_ok=True)
    written = 0
    chosen = [c for c in PAGES["pages"] if not args.only or c["num"] in args.only]
    for c in chosen:
        assert len(c["title"]) <= 65, f"{c['slug']}: title {len(c['title'])} > 65"
        assert 50 <= len(c["description"]) <= 165, f"{c['slug']}: desc {len(c['description'])}"
        (SITE / f"blog-{c['slug']}.html").write_text(page(c), encoding="utf-8")
        written += 1
    cards = blog_cards(chosen)
    print(f"wrote {written} keyword page(s) of {len(PAGES['pages'])} in the plan; "
          f"blog cards ensured for {cards}")


if __name__ == "__main__":
    main()
