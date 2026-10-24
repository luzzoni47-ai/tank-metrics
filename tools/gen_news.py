#!/usr/bin/env python3
"""Render the news desk: one page per story, plus the /news index.

Stories live in tools/news.json. Each carries an English body and a Hinglish
body with the same headings, a source line, and a CTA pointing at the
calculator the story is really about. That last part is the point of the desk:
a reader arrives from a headline and leaves through a tool.

The generator writes the pages, the index, the sitemap entries, llms.txt and
tools/url-map.json, so a new story is one JSON block plus this script.

Usage:
    python3 tools/gen_news.py
"""
from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
NEWS = json.loads((Path(__file__).parent / "news.json").read_text(encoding="utf-8"))
BASE = "https://tankmetrics.in"

TOP_NAV = (
    '<nav class="toplinks"><a href="/">Home</a> '
    '<a href="/news" class="active">News</a> '
    '<a href="/blog">Blog</a> <a href="/about">About</a> '
    '<a href="/contact">Contact</a></nav>'
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
{ld}\
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
    '<h4>Tank Metrics</h4><p>100 free business calculators for entrepreneurs, students and '
    'small business owners. Everything is calculated right in your browser — nothing you type '
    'is ever sent anywhere.</p></div><div class="footer-col"><h4>Company</h4><ul>'
    '<li><a href="/about">About Us</a></li><li><a href="/blog">Blog</a></li>'
    '<li><a href="/news">News</a></li><li><a href="/contact">Contact Us</a></li></ul></div>'
    '<div class="footer-col"><h4>Legal</h4><ul><li><a href="/privacy-policy">Privacy Policy</a></li>'
    '<li><a href="/terms-and-conditions">Terms and Conditions</a></li>'
    '<li><a href="/disclaimer">Disclaimer</a></li></ul></div>'
    '<div class="footer-col"><h4>Popular</h4><ul><li><a href="/#cat_val">Valuation &amp; Deals</a></li>'
    '<li><a href="/#cat_cust">Unit Economics</a></li>'
    '<li><a href="/#cat_everyday">Everyday Money</a></li></ul></div></div>'
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


def heading_count(blocks: list[str]) -> int:
    return sum(len(re.findall(r"<h[23][ >]", b)) for b in blocks)


def body_html(blocks: list[str]) -> str:
    return "\n".join(blocks)


def article_ld(item: dict, canonical: str) -> str:
    ld = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": item["title"],
        "description": item["dek"],
        "datePublished": item["date"],
        "dateModified": item.get("updated", item["date"]),
        "articleSection": item["category"],
        "inLanguage": "en-IN",
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "author": {"@type": "Organization", "name": "Tank Metrics"},
        "publisher": {"@type": "Organization", "name": "Tank Metrics", "url": BASE},
        "isAccessibleForFree": True,
    }
    bc = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "News", "item": BASE + "/news"},
            {"@type": "ListItem", "position": 3, "name": item["title"], "item": canonical},
        ],
    }
    out = ""
    for block in (ld, bc):
        out += ('<script type="application/ld+json">'
                + json.dumps(block, ensure_ascii=False) + "</script>")
    return out


def source_and_cta(item: dict) -> tuple[str, str]:
    source = ""
    if item.get("source_url"):
        source = (
            f'<p class="news-source">Source: <a href="{item["source_url"]}" '
            f'rel="nofollow noopener" target="_blank">{html.escape(item["source_name"])}</a>'
            f' — figures as reported on {item["date_display"]}.</p>'
        )
    cta = item.get("cta") or {}
    cta_html = ""
    if cta:
        cta_html = (
            f'<div class="cta-inline"><p>{html.escape(cta["text"])}</p>'
            f'<a class="btn-primary" href="{cta["href"]}">{html.escape(cta["label"])} →</a></div>'
        )
    return source, cta_html


def related_html(item: dict) -> str:
    if not item.get("related"):
        return ""
    links = "".join(
        f'<li><a href="/{r["slug"]}">{html.escape(r["title"])}</a></li>'
        for r in item["related"]
    )
    return f'<h2>Related reading</h2><ul class="news-related">{links}</ul>'


def short_title(headline: str, limit: int = 60) -> str:
    """Fit a headline into what Google shows, without leaving a dangling word.

    A plain cut leaves titles ending in "and", "This" or "Wins", which reads
    like a bug in the search result. Drop those trailing words as well.
    """
    if len(headline) <= limit:
        return headline
    cut = headline[:limit].rsplit(" ", 1)[0].rstrip(" ,:;-—")
    stop = {"a", "an", "and", "as", "at", "but", "by", "for", "from", "in",
            "into", "is", "it", "its", "of", "on", "or", "that", "the", "this",
            "to", "was", "were", "will", "with", "why"}
    words = cut.split()
    while words and words[-1].lower() in stop:
        words.pop()
    return " ".join(words) or cut


def story_page(item: dict) -> str:
    slug = item["slug"]
    canonical = f"{BASE}/{slug}"
    # The headline is what earns the click, so it wins over the brand suffix:
    # the suffix is dropped as soon as the pair would overflow, and the
    # headline is only shortened when it alone is too long.
    title = f"{item['title']} | Tank Metrics"
    if len(title) > 65:
        title = short_title(item["title"], 65)
    desc = item["dek"]
    if len(desc) > 158:
        desc = desc[:155].rsplit(" ", 1)[0] + "..."
    source, cta_html = source_and_cta(item)
    related = related_html(item)
    tail = source + cta_html + related
    return (
        HEAD.format(title=html.escape(title), desc=html.escape(desc), canonical=canonical,
                    base=BASE, ld=article_ld(item, canonical))
        + TOPBAR
        + '<div class="main" style="max-width:1280px;margin:0 auto">'
        + f'<div class="page-hero"><div class="tag">📰 {html.escape(item["category"])}</div>'
        + f'<h1>{html.escape(item["title"])}</h1><p>{html.escape(item["dek"])}</p></div>'
        + '<div class="page-wrap"><div class="post-meta">'
        + f'<span class="tag2">{html.escape(item["category"])}</span>'
        + f'<span>{item["date_display"]}</span>'
        + '<button class="lang-toggle" id="langToggle" type="button" aria-pressed="false" '
          'title="Read in Hinglish"><span class="lang-badge" aria-hidden="true">H</span>'
          '<span class="lang-toggle-label">Hinglish</span></button></div>'
        + f'<div class="post-lang" data-lang="en">{body_html(item["body_en"])}{tail}</div>'
        + f'<div class="post-lang" data-lang="hinglish" hidden>{body_html(item["body_hinglish"])}{tail}</div>'
        + '<nav class="tool-nav"><a href="/news">← All news</a>'
          '<a href="/blog">Guides →</a></nav>'
        + '</div></div>'
        + FOOTER + TOGGLE_SCRIPT + '</body></html>'
    )


def index_page(items: list[dict]) -> str:
    canonical = f"{BASE}/news"
    title = "News — Startup Funding, Shark Tank and Money News | Tank Metrics"
    desc = ("Startup funding rounds, Shark Tank deals and money rules that affect Indian "
            "founders and small businesses, explained in plain English and Hinglish.")
    cards = ""
    for it in items:
        cards += (
            f'<a class="blog-card" href="/{it["slug"]}">'
            f'<span class="cat">{html.escape(it["category"])}</span>'
            f'<h2>{html.escape(it["title"])}</h2>'
            f'<p>{html.escape(it["dek"])}</p>'
            f'<span class="readmore">Read the story →</span></a>'
        )
    ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Tank Metrics News",
        "url": canonical,
        "description": desc,
        "isPartOf": {"@type": "WebSite", "name": "Tank Metrics", "url": BASE},
    }
    return (
        HEAD.format(title=html.escape(title), desc=html.escape(desc), canonical=canonical,
                    base=BASE,
                    ld='<script type="application/ld+json">'
                       + json.dumps(ld, ensure_ascii=False) + "</script>")
        + TOPBAR
        + '<div class="main" style="max-width:1280px;margin:0 auto">'
        + '<div class="page-hero"><div class="tag">📰 Tank Metrics News</div>'
        + '<h1>Funding rounds, Shark Tank deals and money rules — explained fast.</h1>'
        + f'<p>{html.escape(desc)}</p></div>'
        + f'<div class="blog-grid">{cards}</div>'
        + '</div>'
        + FOOTER + '</body></html>'
    )


def write_sitemap_entries(slugs: list[str]) -> None:
    """Append the news URLs to public/sitemap.xml, replacing any earlier block."""
    p = ROOT / "public" / "sitemap.xml"
    xml = p.read_text(encoding="utf-8")
    # Strip every news entry regardless of the changefreq/priority an earlier
    # writer gave it. wire_crawl_graph.py emits these same pages as weekly/0.6
    # (clean_urls.py then rewrites the loc), so matching only the daily/0.9
    # shape left a second copy behind and the sitemap advertised each story
    # twice - which the live SEO monitor reports as duplicate entries, titles
    # and descriptions.
    news = {f"{BASE}/news", *(f"{BASE}/{s}" for s in slugs)}
    xml = re.sub(
        r"\n  <url><loc>(?:" + "|".join(re.escape(u) for u in sorted(news)) + r")</loc>"
        r"<lastmod>[^<]*</lastmod><changefreq>[^<]*</changefreq>"
        r"<priority>[^<]*</priority></url>", "", xml)
    stamp = date.today().isoformat()
    block = (f'  <url><loc>{BASE}/news</loc><lastmod>{stamp}</lastmod>'
             f'<changefreq>daily</changefreq><priority>0.9</priority></url>')
    for s in slugs:
        block += (f'\n  <url><loc>{BASE}/{s}</loc><lastmod>{stamp}</lastmod>'
                  f'<changefreq>daily</changefreq><priority>0.9</priority></url>')
    xml = xml.replace("</urlset>", block + "\n</urlset>")
    p.write_text(xml, encoding="utf-8")


def write_llms(items: list[dict]) -> None:
    p = ROOT / "public" / "llms.txt"
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"\n## News\n(?:- \[[^\n]*\n)*", "\n", t)
    lines = ["", "## News",
             f"- [News desk]({BASE}/news): funding rounds, Shark Tank deals and money "
             "rules for Indian founders."]
    for it in items:
        lines.append(f"- [{it['title']}]({BASE}/{it['slug']})")
    p.write_text(t.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")


STRIP_RE = re.compile(r'<div class="blog-grid" id="newsGrid">.*?</div>', re.S)
# One-time migration from the old <section class="news-strip"> wrapper.
LEGACY_RE = re.compile(r'<section class="news-strip">.*?</section>', re.S)


# A news card should look like a guide card, so the tab switch does not change
# the page's shape. Categories borrow the guide palette; anything unmapped
# falls back to the site blue.
CAT_COLORS = {
    "Shark Tank": "#f2a600",
    "Tax Rules": "#ea4335",
    "Funding": "#4285f4",
    "Small Business": "#34a853",
}


def strip_html(items: list[dict], limit: int = 6) -> str:
    """The news pane, built as a plain grid of guide-shaped cards."""
    cards = ""
    for it in items[:limit]:
        color = CAT_COLORS.get(it["category"], "#4285f4")
        cards += (
            f'<a class="blog-card" href="/{it["slug"]}" style="border-top-color:{color}">'
            f'<span class="cat">{html.escape(it["category"])}</span>'
            f'<h2>{html.escape(it["title"])}</h2>'
            f'<p>{html.escape(it["dek"])}</p>'
            f'<span class="readmore">Read the story \u2192</span></a>'
        )
    return f'<div class="blog-grid" id="newsGrid">{cards}</div>' 


def write_home_strips(items: list[dict]) -> int:
    """Refresh the news strip on the home page and the blog listing.

    Both pages carry a hand-written strip, so a new story would otherwise never
    appear on them. Replace the whole section each run instead of appending.
    """
    # Only the blog listing carries a strip. The home page stays a clean
    # calculator catalogue, so a visitor is not pushed into reading first.
    targets = {
        SITE / "blog.html": strip_html(items),
    }
    updated = 0
    for path, section in targets.items():
        t = path.read_text(encoding="utf-8")
        if LEGACY_RE.search(t):
            t = LEGACY_RE.sub(lambda _: section, t, count=1)
        elif STRIP_RE.search(t):
            t = STRIP_RE.sub(lambda _: section, t, count=1)
        else:
            continue
        path.write_text(t, encoding="utf-8")
        updated += 1
    return updated


def write_url_map(slugs: list[str]) -> None:
    p = Path(__file__).parent / "url-map.json"
    m = json.loads(p.read_text(encoding="utf-8"))
    m["/news"] = "/site/news.html"
    for s in slugs:
        m[f"/{s}"] = f"/site/news-{s}.html"
    p.write_text(json.dumps(dict(sorted(m.items())), indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")


def main() -> None:
    SITE.mkdir(parents=True, exist_ok=True)
    items = NEWS["items"]
    slugs = []
    for it in items:
        en_heads = heading_count(it["body_en"])
        hi_heads = heading_count(it["body_hinglish"])
        if en_heads != hi_heads:
            raise SystemExit(
                f"{it['slug']}: English has {en_heads} headings, Hinglish has {hi_heads}")
        if re.search(r"[\u0900-\u097F]", " ".join(it["body_hinglish"])):
            raise SystemExit(f"{it['slug']}: Hinglish block contains Devanagari")
        (SITE / f"news-{it['slug']}.html").write_text(story_page(it), encoding="utf-8")
        slugs.append(it["slug"])
    (SITE / "news.html").write_text(index_page(items), encoding="utf-8")
    write_sitemap_entries(slugs)
    write_llms(items)
    write_url_map(slugs)
    write_home_strips(items)
    print(f"wrote {len(items)} news pages + /news index")


if __name__ == "__main__":
    main()
