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

2. **The crawler-visible catalogue.** The old page carried all 101 tools with
   their descriptions in the HTML (`.seo-cat`), which is what a crawler that
   runs no JS sees. The design has 13 toolkit cards and three demos, so the
   tool names would have vanished from the home page. `tools/home_catalogue.html`
   is that block, kept hidden behind the design.

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
CATALOGUE = TOOLS / "home_catalogue.html"
FOOTER = TOOLS / "home_footer.html"

DATA = json.loads((TOOLS / "calcs.json").read_text(encoding="utf-8"))

sys.path.insert(0, str(TOOLS))
from gen_category_pages import slug_for as cat_slug  # noqa: E402

FONT_LINK = (
    '<link href="https://fonts.googleapis.com/css2'
    '?family=Plus+Jakarta+Sans:wght@600;700;800'
    '&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">'
)

MENU_BTN = ('<button class="menu-btn" id="menuBtn" type="button" '
            'aria-label="Open menu" aria-expanded="false">\u2022\u2022\u2022</button>')

# Sir asked the shark clip to stay behind the hero heading, at the speed it
# already ran. It goes in before the aurora and the chakra, so both paint over
# it and it reads as a moving shadow behind "Know Your Numbers." rather than a
# player sitting on the page.
VIDEO = ('<video class="hero-shark-video" autoplay muted loop playsinline '
         'preload="auto" aria-hidden="true">'
         '<source src="/site/shark-hero.mp4" type="video/mp4"></video>')

SHARED_CSS = """
/* ---- shared chrome: menu button, nav drawer, PWA banner, site footer ---- */
.menu-btn{display:none;align-items:center;justify-content:center;width:38px;height:38px;
  flex:none;background:var(--soft);border:1px solid var(--line);color:var(--ink);
  border-radius:10px;font-size:16px;cursor:pointer}
.nav-drawer{position:fixed;left:0;top:0;bottom:0;z-index:60;width:min(88vw,340px);background:#fff;
  transform:translateX(-102%);transition:transform .24s cubic-bezier(.4,0,.2,1);display:flex;
  flex-direction:column;padding:calc(14px + env(safe-area-inset-top,0px)) 0 0;
  box-shadow:18px 0 44px rgba(32,33,36,.16)}
.nav-drawer.open{transform:translateX(0)}
.nav-drawer-head{display:flex;align-items:center;gap:11px;padding:4px 18px 14px;border-bottom:1px solid var(--line)}
.nav-drawer-mark{width:34px;height:34px;flex:none;border-radius:50%;display:flex;align-items:center;
  justify-content:center;background:conic-gradient(var(--blue) 0 25%,var(--red) 25% 50%,var(--yellow) 50% 75%,var(--green) 75% 100%);position:relative}
.nav-drawer-mark::after{content:"";position:absolute;inset:4px;background:#fff;border-radius:50%}
.nav-drawer-mark i{position:relative;z-index:1;font-style:normal;font-weight:700;font-size:15px;color:var(--ink)}
.nav-drawer-head b{display:block;font-family:'Plus Jakarta Sans',sans-serif;font-size:14.5px;color:var(--ink)}
.nav-drawer-head small{display:block;font-size:11px;color:var(--muted)}
.nav-drawer-links{display:flex;flex-direction:column;padding:10px 10px 4px}
.nav-drawer-links a{padding:11px 12px;border-radius:10px;text-decoration:none;color:var(--ink);font-size:14.5px;font-weight:500}
.nav-drawer-links a:hover{background:var(--soft)}
.nav-drawer-links a.active{background:#e8f0fe;color:var(--blue)}
.nav-drawer-label{margin:8px 18px 6px;font-size:10.5px;font-weight:700;text-transform:uppercase;
  letter-spacing:.6px;color:var(--muted-2)}
.nav-drawer-tools{display:flex;flex-direction:column;padding:0 10px;overflow-y:auto;flex:1}
.nav-drawer-tools a{padding:9px 12px;border-radius:9px;text-decoration:none;color:var(--muted);font-size:13px}
.nav-drawer-tools a:hover{background:var(--soft);color:var(--ink)}
.nav-drawer-foot{margin-top:auto;padding:10px 14px calc(14px + env(safe-area-inset-bottom,0px));border-top:1px solid var(--line)}
.nav-drawer-close{width:100%;display:flex;align-items:center;justify-content:center;gap:8px;
  background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:12px;
  font-family:inherit;font-size:14px;font-weight:600;color:var(--ink);cursor:pointer}
.nav-drawer-close:hover{border-color:var(--red);color:var(--red)}
.nav-drawer-close span{font-size:13px}
.nav-scrim{position:fixed;inset:0;z-index:55;background:rgba(32,33,36,.42);opacity:0;visibility:hidden;
  transition:opacity .2s ease,visibility .2s ease}
.nav-scrim.open{opacity:1;visibility:visible}
html.nav-open,html.nav-open body{overflow:hidden}

.pwa-banner{position:fixed;left:50%;transform:translateX(-50%) translateY(140%);bottom:18px;z-index:9999;
  display:flex;align-items:center;gap:13px;width:min(430px,calc(100vw - 26px));
  background:linear-gradient(#fff,#fdfdff);border:1px solid rgba(32,33,36,.07);border-radius:20px;
  padding:14px 15px 14px 14px;font-size:13px;line-height:1.42;color:var(--ink);
  box-shadow:0 2px 6px rgba(32,33,36,.06),0 22px 48px -14px rgba(32,33,36,.4);opacity:0;
  animation:pwaIn .62s cubic-bezier(.2,1.1,.28,1) forwards;overflow:hidden}
.pwa-banner::before{content:"";position:absolute;inset:0 0 auto;height:4px;
  background:linear-gradient(90deg,var(--blue) 0 25%,var(--red) 25% 50%,var(--yellow) 50% 75%,var(--green) 75% 100%)}
.pwa-banner.pwa-out{animation:pwaOut .32s ease forwards}
.pwa-banner .pwa-mark{flex:none;width:42px;height:42px;border-radius:13px;
  background:conic-gradient(var(--blue) 0 25%,var(--red) 25% 50%,var(--yellow) 50% 75%,var(--green) 75% 100%);
  display:flex;align-items:center;justify-content:center;position:relative;box-shadow:0 6px 14px -4px rgba(66,133,244,.5)}
.pwa-banner .pwa-mark::after{content:"";position:absolute;inset:5px;background:#fff;border-radius:9px}
.pwa-banner .pwa-mark i{position:relative;z-index:1;font-style:normal;font-size:16px;color:var(--navy);line-height:1}
.pwa-banner .pwa-copy{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}
.pwa-banner .pwa-copy b{font-size:13.5px;font-weight:600}
.pwa-banner .pwa-copy small{font-size:11.5px;color:var(--muted);line-height:1.4}
.pwa-banner button{flex:none;border:0;border-radius:11px;cursor:pointer;font-family:inherit;font-size:12px;
  font-weight:600;padding:10px 15px;background:linear-gradient(120deg,var(--blue) 0,var(--red) 40%,var(--yellow) 72%,var(--green) 100%);
  color:#fff;box-shadow:0 6px 16px -6px rgba(66,133,244,.65);transition:transform .18s ease;white-space:nowrap}
.pwa-banner button:hover{transform:translateY(-2px) scale(1.03)}
.pwa-banner .pwa-x{position:absolute;top:6px;right:8px;background:transparent;box-shadow:none;color:#c3c7cd;
  font-size:15px;font-weight:400;padding:2px 6px;border-radius:8px;line-height:1}
.pwa-banner .pwa-x:hover{background:var(--soft);color:var(--muted);transform:none;box-shadow:none}
@keyframes pwaIn{from{opacity:0;transform:translateX(-50%) translateY(140%)}to{opacity:1;transform:translateX(-50%) translateY(0)}}
@keyframes pwaOut{to{opacity:0;transform:translateX(-50%) translateY(140%)}}

.site-footer{max-width:1280px;margin:0 auto;padding:40px 28px 30px;border-top:1px solid var(--line)}
.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr;gap:24px;margin-bottom:26px}
.footer-col h4{margin:0 0 12px;font-size:13px;font-weight:600;color:var(--ink)}
.footer-col p{color:var(--muted);font-size:12px;line-height:1.7;margin:0 0 10px}
.footer-col ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:9px}
.footer-col a{color:var(--muted);font-size:12.5px;text-decoration:none;transition:color .15s ease}
.footer-col a:hover{color:var(--blue)}
.footer-flag{display:inline-flex;height:4px;width:52px;border-radius:3px;overflow:hidden;margin:10px 0 0}
.footer-flag span{flex:1}
.footer-flag .s{background:var(--saffron)}
.footer-flag .w{background:#fff;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.footer-flag .g{background:var(--india-green)}
.footer-heart{width:12px;height:12px;fill:var(--red);vertical-align:-1px}
.footer-bottom{border-top:1px solid var(--line);padding-top:18px;display:flex;flex-wrap:wrap;
  justify-content:space-between;gap:10px;color:var(--muted);font-size:11.5px;line-height:1.6}
@media (max-width:880px){.footer-grid{grid-template-columns:1fr 1fr}}
@media (max-width:520px){.footer-grid{grid-template-columns:1fr}}

/* ---- the toolkit card is a div with a stretched link, so the whole card
   stays clickable now that the outer element is not an anchor ---- */
.cat{position:relative;cursor:pointer}
.cat-link::after{content:'';position:absolute;inset:0;z-index:2}
.cat-link{color:inherit;text-decoration:none}
.cat-link:hover{text-decoration:underline}
.cat-arrow{pointer-events:none}

/* ---- the crawler catalogue: every tool named and linked, hidden from view ---- */
.seo-catalogue{display:none}

/* ---- the shark clip sits under the aurora, behind the hero copy ---- */
.hero .hero-shark-video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
  object-position:center;opacity:.2;pointer-events:none;z-index:0;mix-blend-mode:multiply}

/* ---- mobile: a tapped demo card lifts into a full-screen overlay ---- */
@media (max-width:760px){
  .menu-btn{display:flex}
  .card.calculator-focused{position:fixed!important;top:0!important;right:0!important;bottom:0!important;
    left:0!important;width:100vw!important;height:100dvh!important;max-width:none!important;margin:0!important;
    z-index:900!important;overflow-y:auto!important;border-radius:0!important;box-sizing:border-box!important;
    background:#fff;padding:22px 18px 30px!important;transform:none!important}
}
.card>.calculator-focus-close{position:relative;display:block;align-self:center;margin:14px auto 0;z-index:5;
  width:44px;height:38px;border:0;border-radius:12px;background:var(--accent,#4285f4);color:#fff;
  box-shadow:0 4px 14px rgba(24,45,70,.18);font-size:22px;line-height:1;cursor:pointer}
.card>.calculator-focus-close:hover{filter:brightness(.9)}
.card .benchmark{margin-top:12px;font-size:11.5px;color:var(--muted);border-top:1px dashed var(--line);padding-top:10px}
.card .benchmark b{color:var(--india-green);font-weight:600}
"""


def design_css() -> str:
    m = re.search(r"<style>(.*?)</style>", TEMPLATE.read_text(encoding="utf-8"), re.S)
    if not m:
        raise SystemExit("home_template.html has no <style> block")
    return m.group(1)


def design_body() -> str:
    t = TEMPLATE.read_text(encoding="utf-8")
    body = t[t.index("<body>") + len("<body>"):t.rindex("</body>")]
    # The template's script is replaced wholesale: the card engine, the
    # counters and the marquee all move into scripts(), which also carries the
    # wiring the design never had.
    return re.sub(r"<script>.*?</script>", "", body, flags=re.S)


def tag_cards(body: str) -> str:
    """Give every toolkit card a real link and the old `#cat_<id>` anchor.

    The card becomes a `<div>` holding `<h3><a class="cat-link" href=...>`, and
    the anchor is stretched over the card with `::after`, so the whole card is
    still clickable without nesting anchors. `wire_crawl_graph.py` and
    `test_category_pages.py` both expect a `.cat-link` on the home page, and the
    `#cat_<id>` ids matter because the footer on every page links to them.
    """
    matches = list(re.finditer(r'<a class="cat"([^>]*)>(.*?)</a>', body, re.S))
    if not matches:
        return body
    out, last = [], 0
    for m in matches:
        card = m.group(0)
        attrs, inner = m.group(1), m.group(2)
        name_m = re.search(r"<h3>(.*?)</h3>", inner, re.S)
        out.append(body[last:m.start()])
        if not name_m:
            out.append(card)
            last = m.end()
            continue
        # The template writes `&amp;`, calcs.json writes `&`, so unescape before
        # matching or every toolkit with an ampersand silently stays unlinked.
        label = html.unescape(re.sub(r"<[^>]+>", "", name_m.group(1))).strip()
        cat = next((c for c in DATA["cats"] if c["name"] == label), None)
        if cat:
            anchor = f' id="cat_{cat["id"]}"'
            href = f'/{cat_slug(cat)}'
        else:
            anchor, href = "", "#tools"
        heading = (f'<h3><a class="cat-link" href="{href}">{name_m.group(1)}</a></h3>')
        out.append(f'<div class="cat"{anchor}{attrs}>{inner.replace(name_m.group(0), heading, 1)}</div>')
        last = m.end()
    out.append(body[last:])
    return "".join(out)


def fix_counts(body: str) -> str:
    """Make the toolkit count honest.

    The design was drawn with 14 toolkits; the site has 13. The calculator
    count stays at 100 to match the wording on the other 199 pages - the
    catalogue itself lists all 101 - but the toolkit number is on screen as a
    hero stat, so it is read off `calcs.json` rather than typed in.
    """
    n = len(DATA["cats"])
    body = re.sub(r'<b data-count="\d+">0</b><span>Toolkits</span>',
                  f'<b data-count="{n}">0</b><span>Toolkits</span>', body)
    body = re.sub(r'\d+ Toolkits · ', f'{n} Toolkits · ', body)
    return body


def wire(body: str) -> str:
    """Point the design's placeholder links at real pages."""
    body = fix_counts(body)
    body = body.replace('<a href="#" class="logo">',
                        '<a href="/" class="logo" aria-label="Tank Metrics home">', 1)
    body = body.replace('<a href="#">Blog</a>', '<a href="/blog">Blog</a>', 1)
    body = body.replace('<a href="#categories" class="btn btn-ghost">Read the Blog</a>',
                        '<a href="/blog" class="btn btn-ghost">Read the Blog</a>', 1)
    body = tag_cards(body)
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
            + "<style>" + design_css() + SHARED_CSS + "</style>"
            + head[tail_at:])

    body = wire(design_body())

    # The clip goes in first, so the aurora and the chakra paint over it.
    body = body.replace(
        '<div class="aurora" aria-hidden="true"><b></b><b></b><b></b></div>',
        VIDEO + '\n<div class="aurora" aria-hidden="true"><b></b><b></b><b></b></div>', 1)

    body = re.sub(r"<footer>.*?</footer>", FOOTER.read_text(encoding="utf-8"),
                  body, count=1, flags=re.S)
    body = body.rstrip() + "\n" + CATALOGUE.read_text(encoding="utf-8") + "\n"

    return ('<!DOCTYPE html><html lang="en"><head>' + head + "</head><body>"
            + body + scripts() + "</body></html>\n")


def main() -> None:
    page = assemble()
    (SITE / "index.html").write_text(page, encoding="utf-8")
    cards = len(re.findall(r'<a class="cat" href="/', page))
    print(f"home page rebuilt from the design: {len(page)} bytes, "
          f"{cards} toolkit cards linked, catalogue kept")


if __name__ == "__main__":
    main()
