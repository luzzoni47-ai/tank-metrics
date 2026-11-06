#!/usr/bin/env python3
"""Build the home page from Sir's design, without losing any SEO surface.

Sir handed over a complete home page design (Plus Jakarta Sans, aurora hero,
chakra watermark, toolkit grid, live calculators). It was pasted into chat and
never written to a file, so the site kept the old page. This turns that design
into a generator, so the page can be rebuilt instead of hand-edited.

Four things the design does NOT carry, and this adds back:

1. **The head.** The design has a bare `<head>`. The real one needs the Google
   and Bing verification tags, the canonical, the OG/Twitter tags, the PWA
   block, the favicon set and the `@graph` JSON-LD (Organization + WebSite +
   SoftwareApplication + FAQPage). `tools/home_head.html` holds that verbatim
   from the page that passed Search Console, so the crawl surface is unchanged;
   only the fonts and the stylesheet are swapped.

2. **The crawler-visible catalogue.** The old page carried every tool with its
   description in the HTML (`.seo-cat`), which is what a crawler that runs no JS
   sees. The design has 13 toolkit cards and three demos, so the tool names
   would have vanished from the home page. `build_catalogue()` writes that block
   from `calcs.json`, hidden behind the design, so it cannot list a calculator
   the site no longer has.

3. **The site footer.** The design's footer has placeholder `#` links. The
   footer every other page carries holds the product column and the full Legal
   column, and `test_products.py` / `test_layout.py` assert it.

4. **The mobile overlay.** The home page's demo calculators keep the
   tap-to-enlarge behaviour and its close button, because `test_layout.py`
   drives that exact interaction against `/site/index.html`.

Why the design's CSS is inlined instead of added to `style.css`: the two sheets
collide on `.hero`, `.field`, `.cat`, `.flag`, `.dot`, `.tricolor` and
`.btn-primary`, and `style.css` ends with `.hero{padding-bottom:14px!important}`
and `.hero h1{font-size:28px}` - both would flatten the design's hero. Rather
than fight that with a pile of `!important` overrides, the home page carries the
design's own sheet plus the shared rules it still needs (nav drawer, PWA banner,
site footer, menu button, mobile overlay). The other pages keep `style.css`
untouched.

Run from `tools/rebuild.sh`, before `wire_crawl_graph.py` (which needs the
catalogue headings) and before `clean_urls.py`.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "public" / "site"
TOOLS = ROOT / "tools"

TEMPLATE = TOOLS / "home_template.html"
HEAD = TOOLS / "home_head.html"
FOOTER = TOOLS / "home_footer.html"

DATA = json.loads((TOOLS / "calcs.json").read_text(encoding="utf-8"))

sys.path.insert(0, str(TOOLS))
from gen_category_pages import slug_for as cat_slug, tools_of  # noqa: E402
from gen_tool_pages import build_slugs as tool_slugs  # noqa: E402
from design import (  # noqa: E402
    FONT_LINK,
    HOME_DARK_CSS,
    MENU_BTN,
    SHARED_CSS,
    VIDEO,
    design_css,
)

SLUGS = tool_slugs(DATA["calcs"])

# The toolkit card is part of the design: its colour pair, icon and one-line
# lead were drawn by hand. Only the count is derived, so a category that gains
# or loses a tool cannot leave a wrong number on the page.
CARD = {
    "everyday": ("c-blue", "\U0001f4b8",
                 "--accent:var(--blue);--accent-2:var(--blue-l);--accent-glow:rgba(66,133,244,.5);--tint:rgba(66,133,244,.14);--border:rgba(66,133,244,.4)",
                 "Percentage, interest, EMI, savings goals, salary &amp; bill splitting.",
                 "everyday money basics percentage interest emi savings salary"),
    "profit": ("c-green", "\U0001f4c8",
               "--accent:var(--green);--accent-2:var(--green-l);--accent-glow:rgba(52,168,83,.5);--tint:rgba(52,168,83,.14);--border:rgba(52,168,83,.4)",
               "Gross, EBITDA, operating and net margins \u2014 plus ROI and ROCE.",
               "profit margins gross ebitda operating net contribution markup roi roce"),
    "val": ("c-red", "\U0001f988",
            "--accent:var(--red);--accent-2:var(--red-l);--accent-glow:rgba(234,67,53,.5);--tint:rgba(234,67,53,.14);--border:rgba(234,67,53,.4)",
            "Implied valuation, dilution, debt + equity splits and royalty deals.",
            "valuation deals implied pre-money post-money multiple dilution ask royalty cap table esop equity shark tank dscr"),
    "cust": ("c-yellow", "\U0001f3af",
             "--accent:var(--yellow);--accent-2:var(--yellow-l);--accent-glow:rgba(251,188,5,.5);--tint:rgba(251,188,5,.2);--border:rgba(251,188,5,.5)",
             "CAC, LTV, payback, retention, churn and every funnel cost.",
             "customers unit economics cac ltv aov retention churn roas cpc cpl cpa arpu mrr arr"),
    "growth": ("c-blue", "\U0001f680",
               "--accent:var(--blue);--accent-2:var(--blue-l);--accent-glow:rgba(66,133,244,.5);--tint:rgba(66,133,244,.14);--border:rgba(66,133,244,.4)",
               "Run rate, CAGR, burn, runway, break-even and cash cycles.",
               "growth cash run rate cagr burn runway break-even working capital depreciation inventory turnover"),
    "pricing": ("c-saffron", "\U0001f3f7\ufe0f",
                "--accent:var(--saffron);--accent-2:var(--yellow-l);--accent-glow:rgba(255,153,51,.5);--tint:rgba(255,153,51,.2);--border:rgba(255,153,51,.5)",
                "MRP reverse, GST, landed cost, marketplace fees and RTO losses.",
                "pricing selling mrp distributor retailer gst landed cost marketplace cod rto discount duty customs"),
    "ops": ("c-navy", "\U0001f465",
            "--accent:var(--navy);--accent-2:#2F2FB8;--accent-glow:rgba(6,3,141,.4);--tint:rgba(6,3,141,.1);--border:rgba(6,3,141,.3)",
            "Employee CTC, freelancer rates, store payback and revenue per head.",
            "team ctc employee freelancer hourly rate franchise store roi salary revenue per employee"),
    "investor": ("c-green", "\U0001f3e6",
                 "--accent:var(--green);--accent-2:var(--green-l);--accent-glow:rgba(52,168,83,.5);--tint:rgba(52,168,83,.14);--border:rgba(52,168,83,.4)",
                 "MOIC, IRR, exit payouts, TAM / SAM / SOM sizing and WACC.",
                 "investor view moic irr exit tam sam som wacc cost of capital"),
    "bonus": ("c-red", "\U0001f3a4",
              "--accent:var(--red);--accent-2:var(--red-l);--accent-glow:rgba(234,67,53,.5);--tint:rgba(234,67,53,.14);--border:rgba(234,67,53,.4)",
              "See exactly which numbers the Sharks are likely to question.",
              "pitch check shark tank valuation revenue ltv cac runway margin"),
    "agency": ("c-blue", "\U0001f4e3",
               "--accent:var(--blue);--accent-2:var(--blue-l);--accent-glow:rgba(66,133,244,.5);--tint:rgba(66,133,244,.14);--border:rgba(66,133,244,.4)",
               "ROAS, CPM\u2192CPC, client CAC, LTV, margins and utilization.",
               "ad agency roas cpm cpc cpa break-even ad spend client cac ltv margin utilization churn"),
    "realestate": ("c-yellow", "\U0001f3e0",
                   "--accent:var(--yellow);--accent-2:var(--yellow-l);--accent-glow:rgba(251,188,5,.5);--tint:rgba(251,188,5,.2);--border:rgba(251,188,5,.5)",
                   "Property value, home loan EMI, rental yield, stamp duty and more.",
                   "real estate property valuation home loan emi rental yield rent vs buy stamp duty brokerage roi down payment carpet area"),
    "taxwealth": ("c-green", "\U0001f9fe",
                  "--accent:var(--green);--accent-2:var(--green-l);--accent-glow:rgba(52,168,83,.5);--tint:rgba(52,168,83,.14);--border:rgba(52,168,83,.4)",
                  "Old vs new regime, HRA, SIP, PPF, FD, EPF, NPS and gratuity.",
                  "tax wealth income tax hra sip ppf fd rd epf gratuity nps gst"),
    "dailyfun": ("c-saffron", "\U0001f3b2",
                 "--accent:var(--saffron);--accent-2:var(--yellow-l);--accent-glow:rgba(255,153,51,.5);--tint:rgba(255,153,51,.2);--border:rgba(255,153,51,.5)",
                 "Age, love, numerology, zodiac, BMI and date difference tools.",
                 "daily fun age love numerology zodiac rashi baby name lucky number compatibility bmi days between"),
}

SEE_ALL = ("c-navy", "\u26a1",
           "--accent:var(--navy);--accent-2:#2F2FB8;--accent-glow:rgba(6,3,141,.4);--tint:rgba(6,3,141,.1);--border:rgba(6,3,141,.3)",
           "Every single tool in one place \u2014 search, filter and jump right in.",
           "all tools everything calculators")

CARD_ARROW = (
    'Open toolkit\n          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M5 12h14M13 6l6 6-6 6"/></svg>')

# Nine catalogue entries were written shorter than the tool page's own
# description, and the home page has been indexed with that wording. Keep it.
SHORT_DESC = {
    "gross-profit-and-margin": "See how much money is left after covering the direct cost of what you sold.",
    "ebitda-and-margin": "Your core operating profit, before interest, tax, depreciation and amortization.",
    "contribution-margin": "How much each unit you sell contributes towards covering your fixed costs.",
    "dilution-calculator": "Find out how much ownership a founder keeps after giving away equity in a deal.",
    "ask-calculator": "If you know how much money you need, see how much equity that means at your valuation.",
    "customer-lifetime-value-ltv": "The total profit one customer is expected to bring over their whole relationship with you.",
    "distributor-and-retailer-margin": "From your manufacturer price, distributor price and MRP, see each stage's margin %.",
    "property-roi-calculator": "Estimate your property return from rental income and change in value.",
    "epf-calculator": "Estimate EPF accumulation from employee contribution, employer contribution, and interest.",
}

CATALOGUE_INTRO = (
    "Tank Metrics has {n} instant calculators across {c} categories \u2014 startup "
    "valuation, EBITDA and margins, LTV:CAC and unit economics, burn rate and "
    "runway, EMI and loans, pricing, tax, real estate and everyday money. Every "
    "tool runs in your browser: no sign-up, no data leaves your device.")

def design_body() -> str:
    t = TEMPLATE.read_text(encoding="utf-8")
    body = t[t.index("<body>") + len("<body>"):t.rindex("</body>")]
    # The template's script is replaced wholesale: the card engine, the
    # counters and the marquee all move into scripts(), which also carries the
    # wiring the design never had.
    return re.sub(r"<script>.*?</script>", "", body, flags=re.S)


def card_html(cid: str, count: int) -> str:
    ico, icon, style, lead, data_name = CARD[cid]
    cat = next(c for c in DATA["cats"] if c["id"] == cid)
    word = "tool" if count == 1 else "tools"
    return (
        f'\n      <div class="cat" id="cat_{cid}" style="{style}" data-name="{data_name}">\n'
        f'        <div class="cat-top">\n'
        f'          <div class="cat-ico {ico}">{icon}</div>\n'
        f'          <div class="cat-count">{count} {word}</div>\n'
        f'        </div>\n'
        f'        <div>\n'
        f'          <h3><a class="cat-link" href="/{cat_slug(cat)}">'
        f'{html.escape(cat["name"], quote=False)}</a></h3>\n'
        f'          <p>{lead}</p>\n'
        f'        </div>\n'
        f'        <div class="cat-arrow">{CARD_ARROW}\n        </div>\n'
        f'      </div>\n')


def build_grid(body: str) -> str:
    """Write the toolkit grid from calcs.json instead of freezing it.

    The design's 13 cards carried hand-typed tool counts ("10 tools") and a
    `data-name` search string. Both go stale the moment a category gains or
    loses a calculator, and a frozen grid is how the home page came to advertise
    a toolkit that no longer had any tools in it. The colour, icon and lead line
    stay hand-drawn; the count and the link are derived.
    """
    start = body.index('<div class="cat-grid reveal-stagger" id="catGrid">')
    start = body.index(">", start) + 1
    end = body.index('<div class="no-results"', start)
    counts = {c["id"]: len(tools_of(c)) for c in DATA["cats"]}
    cards = "".join(card_html(c["id"], counts[c["id"]]) for c in DATA["cats"])
    ico, icon, style, lead, data_name = SEE_ALL
    cards += (
        f'\n      <div class="cat" style="{style}" data-name="{data_name}">\n'
        f'        <div class="cat-top">\n'
        f'          <div class="cat-ico {ico}">{icon}</div>\n'
        f'          <div class="cat-count">{len(DATA["calcs"])} tools</div>\n'
        f'        </div>\n'
        f'        <div>\n'
        f'          <h3><a class="cat-link" href="#tools">See All Calculators</a></h3>\n'
        f'          <p>{lead}</p>\n'
        f'        </div>\n'
        f'        <div class="cat-arrow">Browse all\n          '
        f'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="M5 12h14M13 6l6 6-6 6"/></svg>\n        </div>\n      </div>\n'
        f'\n\n    </div>\n\n\n    ')
    return body[:start] + cards + body[end:]


def build_catalogue() -> str:
    """The crawler-visible list of every calculator, built from calcs.json.

    A crawler that runs no JS sees only this block, so it has to name every tool
    and link it. Links are written in the raw `/site/...` form on purpose:
    `clean_urls.py` is the single place that turns those into public URLs, and
    `wire_crawl_graph.py` skips a heading that is already a link.
    """
    cats = {c["id"]: c for c in DATA["cats"]}
    out = [
        '<div id="content"><div class="seo-catalogue" id="seoCatalogue">'
        f'<h2>All {len(DATA["calcs"])} free business &amp; money calculators</h2>'
        f'<p>{CATALOGUE_INTRO.format(n=len(DATA["calcs"]), c=len(DATA["cats"]))}</p>'
    ]
    for cat in DATA["cats"]:
        tools = tools_of(cat)
        word = "calculator" if len(tools) == 1 else "calculators"
        items = []
        for c in tools:
            slug = SLUGS[c["id"]]
            desc = SHORT_DESC.get(slug, c["desc"])
            items.append(
                f'<li><h3><a href="/site/tools/{slug}.html">'
                f'{html.escape(c["name"], quote=False)}</a></h3>'
                f'<p>{html.escape(desc, quote=False)}</p></li>')
        out.append(
            f'<section class="seo-cat" id="seo-{cat["id"]}">'
            f'<h2><a href="/site/{cat_slug(cat)}.html">'
            f'{html.escape(cat["name"], quote=False)} ({len(tools)} {word})</a></h2>'
            f'<ul>{"".join(items)}</ul></section>')
    out.append("</div></div>")
    return "".join(out)


def fix_counts(body: str) -> str:
    """Make the toolkit count honest.

    The design was drawn with 14 toolkits; the site has 13. The calculator
    count stays at 100 to match the wording on the other pages, but both numbers
    are read off `calcs.json` rather than typed in, so they cannot drift.
    """
    cats, calcs = len(DATA["cats"]), len(DATA["calcs"])
    body = re.sub(r'<b data-count="\d+">0</b><span>Toolkits</span>',
                  f'<b data-count="{cats}">0</b><span>Toolkits</span>', body)
    body = re.sub(r'<b data-count="\d+">0</b><span>Free Calculators</span>',
                  f'<b data-count="{calcs}">0</b><span>Free Calculators</span>', body)
    body = re.sub(r'\d+ Toolkits · \d+ Calculators',
                  f'{cats} Toolkits · {calcs} Calculators', body)
    return body


def wire(body: str) -> str:
    """Point the design's placeholder links at real pages."""
    body = fix_counts(body)
    body = body.replace('<a href="#" class="logo">',
                        '<a href="/" class="logo" aria-label="Tank Metrics home">', 1)
    body = body.replace('<a href="#">Blog</a>', '<a href="/blog">Blog</a>', 1)
    body = body.replace('<a href="#categories" class="btn btn-ghost">Read the Blog</a>',
                        '<a href="/blog" class="btn btn-ghost">Read the Blog</a>', 1)
    body = build_grid(body)
    body = tag_demo_cards(body)
    # The menu button nav.js needs, so a phone visitor can reach the drawer.
    body = body.replace("</nav>", "</nav>\n    " + MENU_BTN, 1)
    return body


def tag_demo_cards(body: str) -> str:
    """Mark the three demo calculators as `.card` and give each a tip line.

    `test_layout.py` drives the home page's mobile overlay directly: it clicks
    the first `.card`, then measures the close button against the `.benchmark`
    tip inside that same card. The design calls these blocks `.tool` and has no
    tip, so both are added rather than rewriting the test.
    """
    tips = {
        "pctOut": "A percentage is just a fraction of 100, so 18% of 2,50,000 is 45,000.",
        "valOut": "An investor putting in \u20b950 lakh for 5% implies a \u20b910 crore company.",
        "billOut": "Add the tip before you split, then divide by the number of people.",
    }
    for out_id, tip in tips.items():
        m = re.search(
            r'(<div class="tool"[^>]*>.*?<div class="tool-out">.*?<strong id="' + out_id
            + r'">.*?</strong>\s*</div>)', body, re.S)
        if not m:
            continue
        block = m.group(1)
        body = body.replace(
            block, block + f'<div class="benchmark"><b>Tip:</b> {tip}</div>', 1)
    return body.replace('<div class="tool" style=', '<div class="tool card" style=')


def scripts() -> str:
    cats_js = "var CATSLUGS=" + json.dumps(
        {c["id"]: cat_slug(c) for c in DATA["cats"]}, separators=(",", ":")) + ";"
    return (
        "<script>" + DATA["helpers"] + cats_js + """
(function(){var nav=document.getElementById('nav');
if(nav)window.addEventListener('scroll',function(){nav.classList.toggle('scrolled',window.scrollY>30)},{passive:true});

/* Counters in the hero stats. */
function animateCount(el){var target=+el.dataset.count,prefix=el.dataset.prefix||'';
var start=performance.now(),dur=1500;
function step(now){var p=Math.min((now-start)/dur,1),eased=1-Math.pow(1-p,3);
el.textContent=prefix+Math.round(target*eased);if(p<1)requestAnimationFrame(step);}
requestAnimationFrame(step);}
if('IntersectionObserver' in window){var counterObs=new IntersectionObserver(function(es){
es.forEach(function(e){if(e.isIntersecting){animateCount(e.target);counterObs.unobserve(e.target)}})},
{threshold:.5});
document.querySelectorAll('.stat b[data-count]').forEach(function(el){counterObs.observe(el)});}

/* The three demo calculators in the "Answers in seconds" band. */
var inr=function(n){return '\\u20b9'+Number(n||0).toLocaleString('en-IN',{maximumFractionDigits:0})};
var num=function(el){return el?parseFloat(el.value)||0:0};
var pctA=document.getElementById('pctA'),pctB=document.getElementById('pctB'),pctOut=document.getElementById('pctOut');
if(pctOut){var calcPct=function(){pctOut.textContent=inr(num(pctA)*num(pctB)/100)};
[pctA,pctB].forEach(function(i){i.addEventListener('input',calcPct)});calcPct();}
var valA=document.getElementById('valA'),valB=document.getElementById('valB'),valOut=document.getElementById('valOut');
if(valOut){var calcVal=function(){var eq=num(valB);valOut.textContent=eq>0?inr(num(valA)/(eq/100)):'\\u2014'};
[valA,valB].forEach(function(i){i.addEventListener('input',calcVal)});calcVal();}
var billA=document.getElementById('billA'),billB=document.getElementById('billB'),billOut=document.getElementById('billOut');
if(billOut){var calcBill=function(){var p=num(billB);billOut.textContent=p>0?inr(num(billA)/p):'\\u2014'};
[billA,billB].forEach(function(i){i.addEventListener('input',calcBill)});calcBill();}

/* Search filters the toolkit cards; '/' focuses the box. */
var searchInput=document.getElementById('searchInput');
var catCards=[].slice.call(document.querySelectorAll('.cat'));
var noResults=document.getElementById('noResults');
function filterCats(){if(!searchInput)return;var q=(searchInput.value||'').toLowerCase().trim(),visible=0;
catCards.forEach(function(c){var hay=(c.dataset.name+' '+c.textContent).toLowerCase();
var match=!q||hay.indexOf(q)>-1;c.style.display=match?'':'none';if(match)visible++;});
if(noResults)noResults.style.display=(visible===0)?'block':'none';}
if(searchInput){searchInput.addEventListener('input',filterCats);
document.addEventListener('keydown',function(e){
if(e.key==='/'&&document.activeElement!==searchInput){e.preventDefault();searchInput.focus();}});}
document.querySelectorAll('.chip').forEach(function(chip){chip.addEventListener('click',function(){
if(!searchInput)return;searchInput.value=chip.textContent.trim();filterCats();
var c=document.getElementById('categories');if(c)c.scrollIntoView({behavior:'smooth',block:'start'});});});

var track=document.getElementById('mqTrack');if(track)track.innerHTML+=track.innerHTML;

if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(en){
if(en.isIntersecting){en.target.classList.add('in');io.unobserve(en.target)}})},
{threshold:.1,rootMargin:'0px 0px -40px 0px'});
document.querySelectorAll('.reveal,.reveal-stagger').forEach(function(el){io.observe(el)});}
document.querySelectorAll('.reveal-stagger').forEach(function(parent){
[].slice.call(parent.children).forEach(function(child,i){child.style.transitionDelay=(i*70)+'ms';});});

/* Mobile: a tapped demo card lifts into a full-screen overlay. Deliberately no
   scrollIntoView - the card is position:fixed by then, so scrolling it into
   view scrolls the *document* and every keystroke threw the page to the top.
   `test_layout.py` guards this. */
function focusCard(card){if(!card)return;card.classList.add('calculator-focused');}
(function(){if(!window.matchMedia('(max-width:760px)').matches)return;var active=null;
function closeCard(c){if(!c)return;c.classList.remove('calculator-focused');
var b=c.querySelector('.calculator-focus-close');if(b)b.remove();
if(c._focusPlaceholder){c._focusPlaceholder.replaceWith(c);c._focusPlaceholder=null}
document.body.style.overflow='';active=null}
function openCard(c){if(active&&active!==c)closeCard(active);active=c;
if(!c._focusPlaceholder){c._focusPlaceholder=document.createComment('calculator-focus-placeholder');
c.before(c._focusPlaceholder);document.body.appendChild(c)}
c.classList.add('calculator-focused');
if(!c.querySelector('.calculator-focus-close')){var b=document.createElement('button');
b.type='button';b.className='calculator-focus-close';b.setAttribute('aria-label','Close calculator');
b.textContent='\\u00d7';b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();closeCard(c)});
c.appendChild(b)}document.body.style.overflow='hidden'}
document.querySelectorAll('.card').forEach(function(c){c.addEventListener('click',function(e){
if(!e.target.closest('.calculator-focus-close'))openCard(c)})});
window.addEventListener('keydown',function(e){if(e.key==='Escape')closeCard(active)});})();

/* The shark clip keeps the half speed it always ran at, and stays a loop. */
(function(){var v=document.querySelector('.hero-shark-video');if(!v)return;
v.playbackRate=0.5;v.currentTime=0;var p=v.play();if(p&&p.catch)p.catch(function(){});})();
})();
</script>
<script defer src="/site/nav.js"></script>
"""
    )


def assemble() -> str:
    head = HEAD.read_text(encoding="utf-8")
    head = re.sub(r'<link href="https://fonts\.googleapis\.com/css2\?[^"]*" rel="stylesheet">',
                  FONT_LINK, head, count=1)

    # Keep the head up to the stylesheet link, swap in the design's sheet, then
    # keep everything from the analytics script onward. The three inline
    # <style> blocks in between target the old markup (.topbar, .sidebar, and a
    # `.hero{padding-bottom:14px!important}` that would flatten the new hero),
    # so they are dropped rather than carried over.
    cut = head.index('<link rel="stylesheet" href="/site/style.css">')
    tail_at = head.index('<script async src="https://www.googletagmanager.com')
    head = (head[:cut]
            + "<style>" + design_css() + SHARED_CSS + HOME_DARK_CSS + "</style>"
            + head[tail_at:])

    body = wire(design_body())

    # The clip goes in first, so the aurora and the chakra paint over it.
    body = body.replace(
        '<div class="aurora" aria-hidden="true"><b></b><b></b><b></b></div>',
        VIDEO + '\n<div class="aurora" aria-hidden="true"><b></b><b></b><b></b></div>', 1)

    body = re.sub(r"<footer>.*?</footer>", FOOTER.read_text(encoding="utf-8"),
                  body, count=1, flags=re.S)
    body = body.rstrip() + "\n" + build_catalogue() + "\n"

    return ('<!DOCTYPE html><html lang="en"><head>' + head + "</head><body>"
            + body + scripts() + "</body></html>\n")


def main() -> None:
    page = assemble()
    (SITE / "index.html").write_text(page, encoding="utf-8")
    cards = len(re.findall(r'<a class="cat-link" href="/', page))
    tools = len(re.findall(r'<section class="seo-cat" id="seo-', page))
    print(f"home page rebuilt from the design: {len(page)} bytes, "
          f"{cards} toolkit cards linked, {tools} catalogue sections")


if __name__ == "__main__":
    main()
