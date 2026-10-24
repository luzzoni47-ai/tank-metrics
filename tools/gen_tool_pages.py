#!/usr/bin/env python3
"""Generate one indexable page per calculator.

Google cannot rank a tool that only exists as a hash fragment on the home page.
This writes /site/tools/<slug>.html for every calculator: real title, meta
description, H1, canonical, FAQPage + SoftwareApplication JSON-LD, a live
calculator that reuses the exact arithmetic from index.html, and an internal
link back into the home-page card.

Nothing here changes what visitors already see on the home page.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
TOOLS = SITE / "tools"
DATA = json.loads((Path(__file__).parent / "calcs.json").read_text(encoding="utf-8"))
GUIDES = json.loads((Path(__file__).parent / "tool_guides.json").read_text(encoding="utf-8"))
HGUIDES = json.loads(
    (Path(__file__).parent / "tool_guides_hinglish.json").read_text(encoding="utf-8"))
EXAMPLES = json.loads((Path(__file__).parent / "tool_examples.json").read_text(encoding="utf-8"))
BASE = "https://tankmetrics.in"

ACCENTS = {
    "blue": "#4285F4", "green": "#34A853",
    "yellow": "#F2A600", "red": "#EA4335",
}

# Words that should stay uppercase or keep their exact spelling in a slug.
ACRONYMS = {
    "gst", "cgst", "sgst", "igst", "emi", "sip", "cagr", "roi", "roas", "cpc",
    "cpm", "cpa", "ctc", "hra", "epf", "ltv", "cac", "ebitda", "ebit", "arr",
    "mrr", "arpu", "aov", "rto", "bmi", "irr", "moic", "roce", "sam", "som",
    "tam", "esop", "mrp", "upi", "d2c",
}


def slugify(name: str) -> str:
    s = name.lower().replace("&", " and ").replace("%", " percent ")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return re.sub(r"-{2,}", "-", s)


def title_for(c: dict, extra: str = "") -> str:
    """Build a title that stays inside the ~60 chars Google shows.

    The suffix is dropped in steps rather than truncated, so the tool name is
    never cut mid-word.
    """
    name = c["name"] + extra
    for suffix in (" — Free Online Calculator | Tank Metrics",
                   " — Free Calculator | Tank Metrics",
                   " | Tank Metrics"):
        out = name + suffix
        if len(out) <= 60:
            return out
    return out


def build_titles(calcs: list[dict]) -> dict[str, str]:
    """One unique title per page.

    Two calculators share the name "GST Calculator", so the plain title_for()
    would hand two pages the same <title>. Append the category to the ones
    that collide.
    """
    catnames = {x["id"]: x["name"] for x in DATA["cats"]}
    counts: dict[str, int] = {}
    for c in calcs:
        counts[c["name"]] = counts.get(c["name"], 0) + 1
    out = {}
    for c in calcs:
        extra = ""
        if counts[c["name"]] > 1:
            extra = f" ({catnames.get(c['cat'], c['cat'])})"
        out[c["id"]] = title_for(c, extra)
    return out


def desc_for(c: dict) -> str:
    d = re.sub(r"\s+", " ", c["desc"]).strip()
    extra = " Free, instant and private — it runs in your browser, no sign-up needed."
    out = d + extra
    if len(out) > 158:
        out = out[:155].rsplit(" ", 1)[0] + "..."
    # The description is interpolated into a double-quoted attribute, and one
    # source string contains a literal quote ("50 lakh for 5%"). Unescaped it
    # closed the attribute early and left the rest as junk markup.
    return html.escape(out, quote=True)


def faqs(c: dict) -> list[tuple[str, str]]:
    """Three honest, useful questions per tool — the base of FAQPage schema."""
    name = c["name"]
    d = re.sub(r"\s+", " ", c["desc"]).strip()
    cat = next((x["name"] for x in DATA["cats"] if x["id"] == c["cat"]), "")
    q = [
        (f"What does the {name} do?",
         f"{d} It is one of the {cat} tools in the free Tank Metrics collection."),
        (f"Is the {name} free to use?",
         "Yes. Every Tank Metrics calculator is free, needs no account and shows no paywall."),
        (f"Is my data saved when I use the {name}?",
         "No. The calculation runs entirely in your browser, so the numbers you type are never sent to a server."),
    ]
    if c["bench"]:
        b = re.sub(r"\s+", " ", c["bench"]).strip()
        q.append((f"Any tip for getting the {name} right?", b))
    return q


def field_html(calcd_id: str, inp: dict) -> str:
    """Mirror the exact field markup that index.html's fieldHTML() produces."""
    fid = f"{calcd_id}_{inp['k']}"
    ftype = inp.get("type", "number")
    # A native number field refuses anything but digits, so "1 Crore" cannot be
    # typed into one. Amount fields are text; parseAmount() in the shared
    # helpers turns the words into a number.
    html_type = "text" if ftype == "number" else ftype
    ph = inp.get("ph") or ("" if ftype == "date" else "0")
    unit = f'<span class="unit">{inp["u"]}</span>' if inp.get("u") else ""
    classes = "field" + (" full" if inp.get("full") else "") + (
        " rupee-field" if inp.get("u") == "₹" else "")
    return (
        f'<div class="{classes}"><label for="{fid}">{inp["l"]}</label>'
        f'<div class="row"><input type="{html_type}" id="{fid}" '
        f'placeholder="{ph}" data-k="{inp["k"]}" data-unit="{inp.get("u") or ""}">'
        f'{unit}</div></div>'
    )


def guide_for(c: dict) -> dict:
    """Long-form copy for one calculator.

    A hand-written entry in tool_guides.json wins. Anything not yet written
    falls back to the category template, so every page carries the worked
    example, the formula and the mistakes section rather than a bare card.
    """
    g = GUIDES["calcs"].get(c["id"])
    if g:
        return g
    cat = GUIDES["cats"].get(c["cat"], {})
    return {
        "what": cat.get("what", "").replace("{name}", c["name"]).replace("{desc}", c["desc"]),
        "formula": cat.get("formula", "").replace("{name}", c["name"]),
        "mistakes": cat.get("mistakes", []),
        "when": cat.get("when", []),
    }


def guide_for_hinglish(c: dict) -> dict:
    """The same guide copy in Hinglish.

    The blog posts already carry a Hinglish block; the calculator pages did not,
    and Sir wants the translate button there too. A hand-written entry in
    tool_guides_hinglish.json wins, otherwise the category template covers it,
    so all 101 tools get a real Hinglish block instead of a bare English page.
    """
    g = HGUIDES["calcs"].get(c["id"])
    if g:
        return g
    cat = HGUIDES["cats"].get(c["cat"], {})
    return {
        "what": cat.get("what", "").replace("{name}", c["name"]).replace("{desc}", c["desc"]),
        "formula": cat.get("formula", "").replace("{name}", c["name"]),
        "when": cat.get("when", []),
        "mistakes": cat.get("mistakes", []),
    }


def guide_html_hinglish(c: dict) -> str:
    g = guide_for_hinglish(c)
    parts = []
    if g.get("what"):
        parts.append("<h2>Ye calculator kis kaam ka hai</h2>")
        parts.append(f'<p>{g["what"]}</p>')
    if g.get("formula"):
        parts.append("<h2>Ganit kaise chalta hai</h2>")
        parts.append(f'<p>{g["formula"]}</p>')
    if g.get("when"):
        items = "".join(f"<li>{w}</li>" for w in g["when"])
        parts.append("<h2>Kab use karein</h2>")
        parts.append(f'<ul class="plain-list">{items}</ul>')
    if g.get("mistakes"):
        items = "".join(f"<li>{m}</li>" for m in g["mistakes"])
        parts.append("<h2>Aam galtiyan</h2>")
        parts.append(f'<ul class="plain-list">{items}</ul>')
    return "".join(parts)


def example_html_hinglish(c: dict) -> str:
    ex = EXAMPLES.get(c["id"])
    if not ex:
        return ""
    inputs = "".join(
        f'<li><strong>{k}:</strong> {v}</li>' for k, v in ex["inputs"].items()
    )
    results = "".join(
        f'<li><strong>{r["l"]}:</strong> {r["v"]}</li>' for r in ex["rows"]
    )
    return (
        f'<h2>Ek worked example</h2>'
        f'<p>Maano aapko bina spreadsheet kholne ke jaldi jawab chahiye. Yahi wahi '
        f'ganit hai jo upar wala tool karta hai, ek set numbers ke saath.</p>'
        f'<div class="worked"><div class="worked-col"><h3>Aap kya daalte ho</h3>'
        f'<ul>{inputs}</ul></div><div class="worked-col"><h3>Aapko kya milta hai</h3>'
        f'<ul>{results}</ul></div></div>'
        f'<p>Upar koi bhi input badlo aur jawab type karte hi update ho jaata hai. '
        f'Kuch bhi kahin nahi bheja jaata — ganit aapke browser me hi hota hai.</p>'
    )


LANG_TOGGLE = (
    '<button class="lang-toggle" id="langToggle" type="button" '
    'aria-pressed="false" title="Hinglish me padhein">'
    '<span class="lang-badge" aria-hidden="true">H</span>'
    '<span class="lang-toggle-label">Hinglish</span></button>'
)

LANG_SCRIPT = """<script>(function(){
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
    b.title=hinglish?"Read in English":"Hinglish me padhein";
    document.documentElement.lang=hinglish?"hi-Latn":"en";
    b.setAttribute("aria-pressed",hinglish?"true":"false");
  }
  b.addEventListener("click",function(){hinglish=!hinglish;render();});
})();</script>"""


def example_html(c: dict) -> str:
    """A worked example whose numbers come from the calculator's own COMPUTE."""
    ex = EXAMPLES.get(c["id"])
    if not ex:
        return ""
    inputs = "".join(
        f'<li><strong>{k}:</strong> {v}</li>' for k, v in ex["inputs"].items()
    )
    results = "".join(
        f'<li><strong>{r["l"]}:</strong> {r["v"]}</li>' for r in ex["rows"]
    )
    return (
        f'<h2>Worked example</h2>'
        f'<p>{ex["intro"]}</p>'
        f'<div class="worked"><div class="worked-col"><h3>What you enter</h3>'
        f'<ul>{inputs}</ul></div><div class="worked-col"><h3>What you get</h3>'
        f'<ul>{results}</ul></div></div>'
        f'<p>{ex["outro"]}</p>'
    )


def guide_html(c: dict) -> str:
    g = guide_for(c)
    parts = []
    if g.get("what"):
        parts.append("<h2>What this calculator is for</h2>")
        parts.append(f'<p>{g["what"]}</p>')
    if g.get("formula"):
        parts.append("<h2>How the maths works</h2>")
        parts.append(f'<p>{g["formula"]}</p>')
    if g.get("when"):
        items = "".join(f"<li>{w}</li>" for w in g["when"])
        parts.append("<h2>When to reach for it</h2>")
        parts.append(f"<ul class=\"plain-list\">{items}</ul>")
    if g.get("mistakes"):
        items = "".join(f"<li>{m}</li>" for m in g["mistakes"])
        parts.append("<h2>Common mistakes</h2>")
        parts.append(f"<ul class=\"plain-list\">{items}</ul>")
    return "".join(parts)


def related_html(c: dict, slugs: dict[str, str]) -> str:
    """Same-category calculators, so a visitor who needs the next step finds it
    and Google gets a real topical cluster instead of 101 orphan pages."""
    cat = c["cat"]
    sibs = [x for x in DATA["calcs"] if x["cat"] == cat and x["id"] != c["id"]]
    if len(sibs) < 2:
        sibs = [x for x in DATA["calcs"] if x["id"] != c["id"]][:8]
    sibs = sibs[:8]
    links = "".join(
        f'<li><a href="/{slugs[x["id"]]}">{x["name"]}</a></li>' for x in sibs
    )
    catname = next((x["name"] for x in DATA["cats"] if x["id"] == cat), "Tank Metrics")
    return (
        f'<section class="related-tools"><h2>More {catname} calculators</h2>'
        f'<ul class="related-list">{links}</ul></section>'
    )


# Official Indian sources, one line each. Every URL was checked live (HTTP 200)
# in a real browser before being added: an outbound link to a dead government
# page is worse than no link at all. These are the E-E-A-T signal Google looks
# for on a finance site - a calculator that cites the Income Tax Department or
# RBI is a different thing from one that cites nobody. Keys are calculator ids.
#
# Skipped on purpose: epfindia.gov.in (redirects to epfo.gov.in), mca.gov.in and
# cbic.gov.in (both answer 403 / a JavaScript-only shell to non-browser clients).
# Do not add them back without re-checking them in a browser.
SOURCES: dict[str, list[tuple[str, str]]] = {
    "incometax": [("Income Tax Department e-filing portal", "https://www.incometax.gov.in/iec/foportal/")],
    "hra": [("Income Tax Department e-filing portal", "https://www.incometax.gov.in/iec/foportal/")],
    "depreciation": [("Income Tax Department e-filing portal", "https://www.incometax.gov.in/iec/foportal/")],
    "gst": [("GST Portal, Government of India", "https://www.gst.gov.in/")],
    "gst_taxwealth": [("GST Portal, Government of India", "https://www.gst.gov.in/")],
    "nps": [("National Pension System Trust", "https://www.npstrust.org.in/")],
    "sip": [("Association of Mutual Funds in India (AMFI)", "https://www.amfiindia.com/")],
    "ppf": [("India Post - Small Savings Schemes", "https://www.indiapost.gov.in/")],
    "fd": [("Reserve Bank of India", "https://www.rbi.org.in/")],
    "rd": [("Reserve Bank of India", "https://www.rbi.org.in/")],
    "emi": [("Reserve Bank of India", "https://www.rbi.org.in/")],
    "homeemi": [("Reserve Bank of India", "https://www.rbi.org.in/")],
    "propertyvalue": [("Reserve Bank of India", "https://www.rbi.org.in/")],
    "rentalyield": [("Reserve Bank of India", "https://www.rbi.org.in/")],
    "rentbuy": [("Reserve Bank of India", "https://www.rbi.org.in/")],
    "gratuity": [("Ministry of Labour and Employment", "https://www.labour.gov.in/")],
    "stampduty": [("National Portal of India", "https://www.india.gov.in/")],
    "impval": [("SEBI", "https://www.sebi.gov.in/")],
    "prepost": [("SEBI", "https://www.sebi.gov.in/")],
    "revmul": [("SEBI", "https://www.sebi.gov.in/")],
    "ebitdamul": [("SEBI", "https://www.sebi.gov.in/")],
    "marketshare": [("Ministry of Statistics and Programme Implementation", "https://www.mospi.gov.in/")],
    "bmi": [("Ministry of Health and Family Welfare", "https://www.mohfw.gov.in/")],
    "agefun": [("UIDAI", "https://www.uidai.gov.in/")],
}


def sources_html(c: dict) -> str:
    """Cite the official body behind the number. Nofollow is deliberate: the
    point is to show where the rule comes from, not to pass equity outward."""
    rows = SOURCES.get(c["id"])
    if not rows:
        return ""
    items = "".join(
        f'<li><a href="{url}" rel="noopener nofollow" target="_blank">{name}</a></li>'
        for name, url in rows
    )
    return (
        '<section class="tool-sources"><h2>Official source</h2>'
        f'<ul>{items}</ul>'
        '<p class="sources-note">Rules and rates change. Confirm the current '
        'figure with the official body before you act on a result.</p></section>'
    )


def page(c: dict, prev: dict, nxt: dict, slugs: dict[str, str],
         titles: dict[str, str]) -> str:
    slug = slugs[c["id"]]
    accent = ACCENTS.get(
        next((x["color"] for x in DATA["cats"] if x["id"] == c["cat"]), "blue"), "#4285F4")
    cat = next((x for x in DATA["cats"] if x["id"] == c["cat"]), {"name": "", "id": ""})
    fields = "".join(field_html(c["id"], i) for i in c["inputs"])
    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faqs(c)
        ],
    }
    app_ld = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": c["name"],
        "applicationCategory": "FinanceApplication",
        "operatingSystem": "Any",
        "url": f"{BASE}/site/tools/{slug}.html",
        "description": re.sub(r"\s+", " ", c["desc"]).strip(),
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "INR"},
        "isPartOf": {"@type": "WebSite", "name": "Tank Metrics", "url": BASE},
    }
    bc_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": cat["name"],
             "item": f"{BASE}/#{'cat_' + cat['id']}"},
            {"@type": "ListItem", "position": 3, "name": c["name"],
             "item": f"{BASE}/site/tools/{slug}.html"},
        ],
    }
    faq_html = "".join(
        f"<h3>{q}</h3><p>{a}</p>" for q, a in faqs(c)
    )
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><link rel="icon" href="/site/favicon.ico" sizes="any"><link rel="icon" href="/site/favicon.svg" type="image/svg+xml"><link rel="icon" href="/site/favicon.png" type="image/png" sizes="192x192"><link rel="apple-touch-icon" href="/site/favicon.png" sizes="192x192"><link rel="manifest" href="/site/manifest.webmanifest"><meta name="google-site-verification" content="CyIhu9CYYQapfzYJOeSLTP_XY_HWq0McbmY4uX342o4"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{titles[c["id"]]}</title>
<meta name="description" content="{desc_for(c)}">
<link rel="canonical" href="{BASE}/site/tools/{slug}.html">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<meta name="theme-color" content="#FF9933">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Gloock&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet"><link rel="stylesheet" href="/site/style.css">
<meta property="og:type" content="website"><meta property="og:title" content="{titles[c['id']]}"><meta property="og:description" content="{desc_for(c)}"><meta property="og:url" content="{BASE}/site/tools/{slug}.html"><meta property="og:image" content="{BASE}/og-image.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:site_name" content="Tank Metrics"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{titles[c['id']]}"><meta name="twitter:description" content="{desc_for(c)}"><meta name="twitter:image" content="{BASE}/og-image.png">
<script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(app_ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(bc_ld, ensure_ascii=False)}</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-MHZ0V6HFC6"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-MHZ0V6HFC6');</script>
</head><body><div class="tricolor"></div><div class="topbar"><div class="topbar-inner"><button class="menu-btn" id="menuBtn" aria-label="Menu" style="visibility:hidden">☰</button><div class="brand"><a href="/" style="display:flex;align-items:center;gap:11px;text-decoration:none;color:inherit"><div class="brand-mark"><span class="rs">₹</span></div><div class="brand-text"><span class="brand-name">Tank Metrics</span><p>Simple money calculators, made for beginners</p></div></a></div><nav class="toplinks"><a href="/">Home</a> <a href="/site/blog.html">Blog</a> <a href="/site/about.html">About</a> <a href="/site/contact.html">Contact</a></nav></div></div>
<div class="main" style="max-width:1280px;margin:0 auto">
<div class="page-hero"><div class="tag">🧮 {cat['name']}</div><h1>{c['name']}</h1><p>{c['desc']}</p></div>
<div class="page-wrap">
<div class="card" style="--accent:{accent}"><div class="card-title"><h2>{c['name']}</h2><button class="clear-btn" id="clearBtn" type="button">Clear</button></div><div class="inputs">{fields}</div><div class="readout" id="out"></div></div>
<div class="tool-meta">{LANG_TOGGLE}</div>
<div class="post-lang" data-lang="en">
<h2>How this calculator works</h2>
<p>{c['desc']} Enter your numbers above and the result appears instantly — nothing is stored or sent anywhere.</p>
{f'<p><strong>Good to know:</strong> {c["bench"]}</p>' if c['bench'] else ''}
{example_html(c)}
{guide_html(c)}
</div>
<div class="post-lang" data-lang="hinglish" lang="hi-Latn" hidden>
{example_html_hinglish(c)}
{guide_html_hinglish(c)}
</div>
<h2>Frequently asked questions</h2>
{faq_html}
<div class="cta-inline"><p>Want all 100 calculators in one place?</p><a class="btn-primary" href="/#{'card_' + c['id']}">Open on the home page →</a></div>
{related_html(c, slugs)}
{sources_html(c)}
<nav class="tool-nav"><a href="/{slugs[prev['id']]}">← {prev['name']}</a><a href="/{slugs[nxt['id']]}">{nxt['name']} →</a></nav>
<p><a href="/">← All 100 Tank Metrics calculators</a></p>
</div></div>
<footer class="site-footer"><div class="footer-grid"><div class="footer-col"><h4>Tank Metrics</h4><p>100 free business calculators for entrepreneurs, students and small business owners. Everything is calculated right in your browser — nothing you type is ever sent anywhere.</p></div><div class="footer-col"><h4>Company</h4><ul><li><a href="/site/about.html">About Us</a></li><li><a href="/site/blog.html">Blog</a></li><li><a href="/site/contact.html">Contact Us</a></li></ul></div><div class="footer-col"><h4>Legal</h4><ul><li><a href="/site/privacy-policy.html">Privacy Policy</a></li><li><a href="/site/terms-and-conditions.html">Terms and Conditions</a></li><li><a href="/site/disclaimer.html">Disclaimer</a></li></ul></div><div class="footer-col"><h4>Popular</h4><ul><li><a href="/#cat_val">Valuation &amp; Deals</a></li><li><a href="/#cat_cust">Unit Economics</a></li><li><a href="/#cat_everyday">Everyday Money</a></li></ul></div><div class="footer-col"><h4>Digital Products</h4><ul><li><a href="/digital-products/indian-business-financial-model">Indian Business Financial Model</a></li></ul></div></div><div class="footer-bottom"><span>© 2026 Tank Metrics. Built for learning and quick estimates — for big decisions, always check with a qualified accountant or financial advisor.</span> <span>Made with <svg class="footer-heart" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg> in Bangalore, India</span></div></footer>
<script>{DATA['helpers']}
var COMPUTE={c['compute']};
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
</script>
{LANG_SCRIPT}
</body></html>
"""


def build_slugs(calcs: list[dict]) -> dict[str, str]:
    """Map each calculator id to a unique slug.

    Two tools can share a name (for example a GST Calculator in two categories),
    so disambiguate a collision with the category name instead of overwriting
    a page.
    """
    seen: dict[str, int] = {}
    out: dict[str, str] = {}
    catnames = {x["id"]: x["name"] for x in DATA["cats"]}
    for c in calcs:
        slug = slugify(c["name"])
        if slug in seen:
            seen[slug] += 1
            slug = f"{slug}-{slugify(catnames.get(c['cat'], c['cat']))}"
        else:
            seen[slug] = 1
        out[c["id"]] = slug
    return out


def main() -> None:
    TOOLS.mkdir(parents=True, exist_ok=True)
    calcs = DATA["calcs"]
    slugs = build_slugs(calcs)
    titles = build_titles(calcs)
    written = []
    for idx, c in enumerate(calcs):
        prev = calcs[idx - 1]
        nxt = calcs[(idx + 1) % len(calcs)]
        (TOOLS / f"{slugs[c['id']]}.html").write_text(
            page(c, prev, nxt, slugs, titles), encoding="utf-8")
        written.append((slugs[c["id"]], c["name"], c["cat"]))
    unique = len({s for s, _, _ in written})
    print(f"wrote {len(written)} tool pages ({unique} unique slugs)")
    return written


def _apply_pwa() -> None:
    """Re-apply the per-page extras the generator would otherwise drop.

    This writes each tool page from scratch, so anything added to those pages by
    a separate step disappears on a plain run: the PWA block (offline support)
    and the blog back-links (`wire_blog_tools.py`). Both are re-applied here so
    a regeneration cannot silently undo them.
    """
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import add_pwa
    import wire_blog_tools

    add_pwa.main()
    wire_blog_tools.main()


if __name__ == "__main__":
    main()
    _apply_pwa()
