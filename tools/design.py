#!/usr/bin/env python3
"""The shared visual language of the site.

`gen_home.py` builds the home page from Sir's design; `gen_category_pages.py`
builds one page per toolkit. Both have to look like the same site, so the design
sheet, the font link, the menu button and the shared chrome (nav drawer, PWA
banner, site footer, mobile overlay) live here and are imported by both. With
the design in one place, a change to the hero or to a toolkit card cannot land
on the home page and quietly miss the 13 toolkit pages.

`design_css()` reads the sheet out of `home_template.html`, which stays the one
file Sir's design was pasted into.
"""
from __future__ import annotations

import re
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
TEMPLATE = TOOLS / "home_template.html"

FONT_LINK = (
    '<link href="https://fonts.googleapis.com/css2'
    '?family=Plus+Jakarta+Sans:wght@600;700;800'
    '&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">'
)

# The font link every non-home page carries. Sir asked the whole site to wear
# the home page's typography, so the generator font links point here instead of
# loading Poppins + Gloock. `style.css` names the same two families, so the
# page and its stylesheet agree.
SITE_FONT_LINK = FONT_LINK

# Poppins + Gloock, the pair the inner pages loaded before. Replaced by
# SITE_FONT_LINK in every generator; kept here so the swap is a one-liner.
OLD_FONT_LINK = (
    '<link href="https://fonts.googleapis.com/css2'
    '?family=Gloock&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">'
)

# The home page's colour and type, for the inner pages. Appended to style.css so
# every page that loads the shared sheet - tool, category, blog, news, about -
# picks up the same tokens and the same motion. Scoped to tokens and small
# touches only: the inner pages keep their own layout rules, because they are
# denser than the home page and a full restyle would break their grids.
THEME_CSS = """
/* ============================================================
   The home page's colour, type and motion, applied site-wide.
   Sir asked the whole site to feel like the home page. The tokens
   below match home_template.html, and the motion rules are the
   home page's own keyframes, reused rather than reinvented.
   ============================================================ */
:root{
  --blue:#4285F4;--red:#EA4335;--yellow:#FBBC05;--green:#34A853;
  --blue-l:#6BA6FF;--red-l:#FF6B5B;--yellow-l:#FFD54F;--green-l:#5BC47A;
  --saffron:#FF9933;--india-green:#138808;--navy:#06038D;--chakra:#06038D;
  --ink:#080B12;--ink-2:#1A2233;--muted:#5B6474;--muted-2:#8A94A6;
  --text:#080B12;--text-dim:#5B6474;
  --line:#EAEDF3;--line-2:#DFE4EE;--soft:#F6F8FC;--panel:#F6F8FC;
  --bg:#fff;
  --shadow-m:0 14px 40px -14px rgba(8,11,18,.18);
  --shadow-l:0 32px 80px -28px rgba(8,11,18,.28);
  --r:24px;--r-sm:16px;
  --ease:cubic-bezier(.2,.7,.3,1);
  --ease-out:cubic-bezier(.16,1,.3,1);
  --spring:cubic-bezier(.34,1.56,.64,1);
}
body{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif;
  color:var(--ink);background:var(--bg);
  -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
h1,h2,h3,h4,.disp{font-family:'Plus Jakarta Sans',sans-serif;font-weight:800;
  letter-spacing:-.03em}
.brand-text h1,.brand-text p,.toplinks a,.menu-btn,.btn-primary,.btn-secondary,
.field input,.field select,.sb-search,.card-title h3,.seo-cat h2,.seo-cat h3,
.blog-card h2,.cta-inline p{font-family:'Inter',system-ui,sans-serif}
.brand-mark .rs,.pwa-banner .pwa-mark i,.hero .tag,.category-head h2{
  font-family:'Plus Jakarta Sans',sans-serif;font-weight:800}

/* The home page's aurora wash, on the inner hero. Low opacity, painted behind
   the copy, so a tool page opens with the same colour as the home page. */
.hero{position:relative;overflow:hidden}
.hero::before{
  content:'';position:absolute;inset:-40% -10% auto;height:150%;pointer-events:none;z-index:0;
  background:
    radial-gradient(520px 320px at 12% 0%,rgba(66,133,244,.10),transparent 62%),
    radial-gradient(480px 300px at 88% 4%,rgba(255,153,51,.10),transparent 62%),
    radial-gradient(540px 320px at 50% 116%,rgba(52,168,83,.09),transparent 66%);
}
.hero>*{position:relative;z-index:1}

/* The home page's card lift, on the inner cards. The lift only: style.css
   already owns the card's focus ring and its ::after, so a gradient here would
   be overridden by a higher-specificity rule and only add weight. */
.card{transition:box-shadow .45s var(--ease),transform .45s var(--ease),
  border-color .45s var(--ease)}
.card:hover{transform:translateY(-6px);
  box-shadow:0 40px 90px -32px rgba(8,11,18,.28)}

/* The home page's gradient headline treatment, for section heads. */
.seo-cat h2,.category-head h2{letter-spacing:-.03em}

/* The home page's entrance, on the inner pages, without a line of JavaScript.
   Scroll-driven animations are gated behind @supports, so a browser that does
   not know the property renders the page exactly as before. Only block-level
   elements are animated: `.card` carries a hover transform and an animation
   would beat it once the range finished. */
@supports (animation-timeline: view()){
  @media (prefers-reduced-motion: no-preference){
    .page-hero,.cat-intro,.cat-tools,.cat-siblings,.blog-tabs,.blog-grid,
    .founder-card,.worked,.related-tools,.tool-sources,.cta-inline{
      animation:tmRevealUp linear both;
      animation-timeline: view();
      animation-range: entry 0% entry 55%;
    }
  }
}
@keyframes tmRevealUp{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}

/* Reveal-on-scroll, matching the home page's .reveal. */
.reveal,.reveal-stagger{opacity:0;transform:translateY(26px);
  transition:opacity .7s var(--ease-out),transform .7s var(--ease-out)}
.reveal.in,.reveal-stagger.in{opacity:1;transform:none}
.reveal-stagger>*{opacity:0;transform:translateY(22px);
  transition:opacity .6s var(--ease-out),transform .6s var(--ease-out)}
.reveal-stagger.in>*{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){
  .reveal,.reveal-stagger,.reveal-stagger>*{opacity:1!important;transform:none!important;
    transition:none!important}
  .card:hover{transform:none}
}
"""


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

/* ---- phone: the toolkit cards and the "why" points stay two-up. A single
   column made the visitor scroll past one card at a time; Sir asked for
   left-right, then the next row, then the next. The demo calculators
   (`.live-grid`) keep one column, because their input fields need the width.
   This sits after the design sheet on purpose, so it wins the cascade at phone
   widths without editing the template. ---- */
@media (max-width:768px){
  .cat-grid,.why-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
  .cat{padding:18px 16px;min-height:0;gap:12px;border-radius:18px}
  .cat-ico{width:46px;height:46px;font-size:20px;border-radius:14px}
  .cat h3{font-size:15px}
  .cat p{font-size:12px;line-height:1.5}
  .cat-count{font-size:10.5px;padding:4px 9px}
  .feat{padding:20px 16px;border-radius:18px}
  .feat-ico{width:44px;height:44px;font-size:20px;border-radius:13px;margin-bottom:14px}
  .feat h3{font-size:15px;margin-bottom:8px}
  .feat p{font-size:12.5px;line-height:1.5}
}
@media (max-width:420px){
  .cat-grid,.why-grid{gap:10px}
  .cat{padding:15px 13px}
  .cat-ico{width:40px;height:40px;font-size:18px}
  .cat h3{font-size:14px}
  .feat{padding:17px 13px}
  .feat-ico{width:38px;height:38px;font-size:18px}
}"""


def design_css() -> str:
    m = re.search(r"<style>(.*?)</style>", TEMPLATE.read_text(encoding="utf-8"), re.S)
    if not m:
        raise SystemExit("home_template.html has no <style> block")
    return m.group(1)

# ---------------------------------------------------------------------------
# Dark mode. Sir asked for the whole site to match the home page; the home page
# is a light design, so dark is an addition rather than a copy, and it has to
# cover every page, not just the ones a generator writes.
#
# The switch is an attribute on <html>, not a media query, so the visitor's
# choice wins over the OS. `theme.js` writes it and a tiny inline script in the
# head applies it before the first paint, which is what stops the white flash.
#
# Only tokens are redefined here. Every rule in style.css already reads a
# variable, so redefining the variables repaints the whole site.
# ---------------------------------------------------------------------------
DARK_CSS = """
html[data-theme="dark"]{
  color-scheme:dark;
  --ink:#EEF1F7;--ink-2:#DDE3EE;--muted:#A3ACBE;--muted-2:#8B94A7;
  --text:#EEF1F7;--text-dim:#A3ACBE;
  --line:#262B36;--line-2:#2F3542;--soft:#171A21;--panel:#171A21;
  --bg:#0E1116;
  --shadow-m:0 14px 40px -14px rgba(0,0,0,.6);
  --shadow-l:0 32px 80px -28px rgba(0,0,0,.7);
  --blue-l:#6BA6FF;--red-l:#FF7A6B;--yellow-l:#FFD54F;--green-l:#5BC47A;
  --india-green:#4FBF6A;
}
html[data-theme="dark"] body{background:var(--bg);color:var(--ink)}
html[data-theme="dark"] .topbar,
html[data-theme="dark"] .nav-drawer,
html[data-theme="dark"] .pwa-banner{background:#141821;border-color:var(--line)}
html[data-theme="dark"] .nav-drawer-head{border-color:var(--line)}
html[data-theme="dark"] .nav-drawer-mark::after,
html[data-theme="dark"] .pwa-banner .pwa-mark::after{background:#141821}
html[data-theme="dark"] .nav-drawer-links a.active{background:#1D2635;color:var(--blue-l)}
html[data-theme="dark"] .nav-drawer-close{background:var(--soft);border-color:var(--line);color:var(--ink)}
html[data-theme="dark"] .card,
html[data-theme="dark"] .cat,
html[data-theme="dark"] .feat,
html[data-theme="dark"] .blog-card,
html[data-theme="dark"] .tcard,
html[data-theme="dark"] .founder-card{background:#141821;border-color:var(--line)}
html[data-theme="dark"] .card .readout,
html[data-theme="dark"] .worked,
html[data-theme="dark"] .worked-col,
html[data-theme="dark"] .benchmark{background:#11151C;border-color:var(--line)}
html[data-theme="dark"] .page-hero{
  background:linear-gradient(135deg,#1A2130,#141821 45%,#152018);border-color:var(--line)}
html[data-theme="dark"] .site-footer{background:#0B0E13;border-color:var(--line)}
html[data-theme="dark"] .field input,
html[data-theme="dark"] .field select,
html[data-theme="dark"] .sb-search{background:#11151C;border-color:var(--line);color:var(--ink)}
html[data-theme="dark"] .legal-page,
html[data-theme="dark"] .seo-cat li,
html[data-theme="dark"] .clear-btn,
html[data-theme="dark"] .lang-toggle,
html[data-theme="dark"] .blog-tabs,
html[data-theme="dark"] .calculator-focus-close,
html[data-theme="dark"] .sidebar-close{background:#141821;border-color:var(--line);color:var(--ink)}
html[data-theme="dark"] .btn-secondary{background:#141821;border-color:var(--india-green);color:var(--green-l)}
html[data-theme="dark"] .brand-mark::after,
html[data-theme="dark"] .page-num::after,
html[data-theme="dark"] .footer-flag .w{background:#141821}
html[data-theme="dark"] img{filter:brightness(.92)}
html[data-theme="dark"] .hero-shark-video{opacity:.35}

/* The theme switch, in the top bar. A 3-state button is honest about what a
   tap will do next, so the label is the state the visitor is moving to. */
.theme-btn{display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;
  flex:none;background:var(--soft);border:1px solid var(--line);color:var(--ink);
  border-radius:10px;font-size:16px;line-height:1;cursor:pointer}
.theme-btn:hover{border-color:var(--blue)}
.theme-btn svg{width:17px;height:17px;display:block}
html[data-theme="dark"] .theme-btn{background:#1D2331;border-color:var(--line)}

/* Scroll progress: the home page's idea, site-wide. Sits above everything and
   is driven by one rAF loop in theme.js. */
.scroll-progress{position:fixed;top:0;left:0;right:0;height:2px;z-index:80;pointer-events:none}
.scroll-progress i{display:block;height:100%;width:0;
  background:linear-gradient(90deg,var(--blue),var(--saffron),var(--green));
  transition:width .1s linear}
"""


# ---------------------------------------------------------------------------
# Dark mode for the home page.
#
# The home page is the one page whose sheet is not `style.css`: `gen_home.py`
# inlines its own CSS so the design's rules cannot be overridden by the shared
# sheet. That means the dark block above, which only ever lands in style.css,
# never reached the home page, and the home page stayed white while every inner
# page went dark.
#
# The class names are the home page's own (`.nav`, `.cat`, `.tool`, `.feat`),
# not the shared sheet's, so the rules are written against those. Tokens are
# redefined first and the handful of literal `#fff` surfaces follow.
# ---------------------------------------------------------------------------
HOME_DARK_CSS = """
html[data-theme="dark"]{
  --ink:#EEF1F7;--ink-2:#DDE3EE;--muted:#A3ACBE;--muted-2:#8B94A7;
  --line:#262B36;--line-2:#2F3542;--soft:#171A21;--white:#0E1116;
  --shadow-m:0 14px 40px -14px rgba(0,0,0,.6);
  --shadow-l:0 32px 80px -28px rgba(0,0,0,.7);
  --blue-l:#6BA6FF;--red-l:#FF7A6B;--yellow-l:#FFD54F;--green-l:#5BC47A;
  color-scheme:dark;
}
html[data-theme="dark"] body{background:var(--white);color:var(--ink)}
html[data-theme="dark"] .nav{background:rgba(14,17,22,.92)}
html[data-theme="dark"] .badge,
html[data-theme="dark"] .search,
html[data-theme="dark"] .chip,
html[data-theme="dark"] .mq,
html[data-theme="dark"] .cat,
html[data-theme="dark"] .tool,
html[data-theme="dark"] .feat,
html[data-theme="dark"] .field input:focus{background:#141821;border-color:var(--line-2)}
html[data-theme="dark"] .badge .flag i:nth-child(2),
html[data-theme="dark"] .foot-bottom .flag-mini i:nth-child(2){background:#141821}
html[data-theme="dark"] .logo-mark::before{background:linear-gradient(140deg,#1A2130,#141821)}
html[data-theme="dark"] .marquee{background:linear-gradient(180deg,#141821,var(--soft))}
html[data-theme="dark"] .cat-count,
html[data-theme="dark"] .search .kbd,
html[data-theme="dark"] .field input{background:var(--soft);border-color:var(--line)}
html[data-theme="dark"] .nav-links a:hover{background:var(--soft)}
html[data-theme="dark"] .nav-drawer{background:#141821;border-color:var(--line)}
html[data-theme="dark"] .nav-drawer-mark::after,
html[data-theme="dark"] .pwa-banner .pwa-mark::after{background:#141821}
html[data-theme="dark"] .footer-flag .w{background:#141821}
html[data-theme="dark"] .card.calculator-focused{background:#141821;border-color:var(--line-2)}
html[data-theme="dark"] .tricolor::before{background:linear-gradient(90deg,transparent,rgba(255,255,255,.28),transparent)}
html[data-theme="dark"] .cta::after{background:linear-gradient(90deg,var(--saffron) 0 33.3%,#141821 33.3% 66.6%,var(--india-green) 66.6% 100%)}
html[data-theme="dark"] footer::before{background:linear-gradient(90deg,var(--saffron) 0 33.3%,#141821 33.3% 66.6%,var(--india-green) 66.6% 100%)}
html[data-theme="dark"] .btn-primary{background:#EEF1F7;color:#0E1116}
html[data-theme="dark"] .theme-btn{background:var(--soft);border-color:var(--line);color:var(--ink)}
html[data-theme="dark"] .scroll-progress{background:linear-gradient(90deg,var(--blue-l),var(--saffron),var(--green-l))}
html[data-theme="dark"] img{filter:brightness(.92)}
html[data-theme="dark"] .hero-shark-video{opacity:.35}
"""


# ---------------------------------------------------------------------------
# The rating card. Lives here rather than in style.css so a generator and the
# static pages get the identical sheet, and so it can read the same tokens the
# dark block above redefines.
# ---------------------------------------------------------------------------
RATING_CSS = """
.tmr{position:relative;width:min(640px,calc(100% - 32px));margin:26px auto;
  padding:1.5px;border-radius:26px;background:conic-gradient(from var(--tmr-a),
    rgba(66,133,244,.85),rgba(255,153,51,.65) 22%,rgba(66,133,244,0) 46%,
    rgba(66,133,244,0) 62%,rgba(52,168,83,.5) 80%,rgba(66,133,244,.85));
  animation:tmr-spin 10s linear infinite;
  opacity:0;transform:translateY(22px) scale(.975);
  transition:opacity .7s var(--ease-out),transform .7s var(--ease-out)}
@property --tmr-a{syntax:"<angle>";initial-value:0deg;inherits:false}
@keyframes tmr-spin{to{--tmr-a:360deg}}
.tmr.is-in{opacity:1;transform:none}
.tmr__inner{position:relative;overflow:hidden;border-radius:24.5px;padding:30px 28px 24px;
  text-align:center;background:radial-gradient(130% 140% at 50% -35%,rgba(66,133,244,.10),transparent 60%),
    linear-gradient(180deg,rgba(255,255,255,.6),transparent 40%),#fff;
  box-shadow:0 1px 2px rgba(8,11,18,.05),0 30px 70px -34px rgba(8,11,18,.35)}
html[data-theme="dark"] .tmr__inner{background:
    radial-gradient(130% 140% at 50% -35%,rgba(66,133,244,.18),transparent 60%),
    linear-gradient(180deg,rgba(255,255,255,.04),transparent 40%),#141821;
  box-shadow:0 1px 2px rgba(0,0,0,.4),0 30px 70px -34px rgba(0,0,0,.8)}
.tmr__aura{position:absolute;top:-30%;left:50%;width:78%;height:150%;transform:translateX(-50%);
  background:radial-gradient(closest-side,rgba(242,166,0,.14),transparent 72%);opacity:0;
  transition:opacity .8s ease;pointer-events:none}
.tmr.is-lit .tmr__aura{opacity:1}
.tmr__inner::after{content:"";position:absolute;inset:-40% -120%;pointer-events:none;
  background:linear-gradient(102deg,transparent 44%,rgba(66,133,244,.07) 50%,transparent 56%);
  transform:translateX(-40%);animation:tmr-sheen 8s cubic-bezier(.5,0,.5,1) infinite}
@keyframes tmr-sheen{0%,64%{transform:translateX(-40%)}94%,100%{transform:translateX(40%)}}
.tmr__spark{position:absolute;width:3px;height:3px;border-radius:50%;background:var(--saffron);
  opacity:0;pointer-events:none;animation:tmr-float var(--dur,9s) ease-in-out infinite;
  animation-delay:var(--delay,0s)}
@keyframes tmr-float{0%,100%{opacity:0;transform:translateY(0) scale(.6)}20%{opacity:.5}
  50%{opacity:.85;transform:translateY(-44px) scale(1)}80%{opacity:.35}}
.tmr__eyebrow{position:relative;display:inline-flex;align-items:center;gap:8px;font-size:10.5px;
  font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:var(--blue);
  margin-bottom:12px;font-family:'Inter',sans-serif}
html[data-theme="dark"] .tmr__eyebrow{color:var(--blue-l)}
.tmr__pulse{width:6px;height:6px;border-radius:50%;background:var(--blue);
  animation:tmr-pulse 2.4s ease-out infinite}
@keyframes tmr-pulse{0%{box-shadow:0 0 0 0 rgba(66,133,244,.55)}70%,100%{box-shadow:0 0 0 10px transparent}}
.tmr__title{position:relative;margin:0;font-size:22px;font-weight:800;letter-spacing:-.022em;
  font-family:'Plus Jakarta Sans',sans-serif;color:var(--ink)}
.tmr__sub{position:relative;margin:7px 0 0;font-size:13px;color:var(--muted)}
.tmr__stars{position:relative;display:flex;justify-content:center;gap:8px;margin:18px 0 6px}
.tmr__star{position:relative;width:54px;height:54px;padding:0;border:0;background:none;cursor:pointer;
  color:rgba(91,100,116,.32);transition:transform .3s var(--spring),color .25s ease;
  -webkit-tap-highlight-color:transparent}
html[data-theme="dark"] .tmr__star{color:rgba(163,172,190,.3)}
.tmr.is-in:not(.is-ready) .tmr__star{animation:tmr-star-in .6s var(--spring) both;
  animation-delay:calc(var(--i,0) * 80ms + 140ms)}
@keyframes tmr-star-in{0%{opacity:0;transform:translateY(12px) scale(.75)}
  60%{opacity:1;transform:translateY(-4px) scale(1.12)}100%{opacity:1;transform:none}}
.tmr__star svg{width:100%;height:100%;display:block;overflow:visible}
.tmr__star path{fill:currentColor;transition:fill .25s ease,filter .3s ease}
.tmr__star:hover,.tmr__star:focus-visible{transform:translateY(-7px) scale(1.2);
  color:var(--yellow);outline:none}
.tmr__star:focus-visible{border-radius:12px;box-shadow:0 0 0 2px var(--blue)}
.tmr__stars[data-hover="1"] .tmr__star:nth-child(-n+1),
.tmr__stars[data-hover="2"] .tmr__star:nth-child(-n+2),
.tmr__stars[data-hover="3"] .tmr__star:nth-child(-n+3),
.tmr__stars[data-hover="4"] .tmr__star:nth-child(-n+4),
.tmr__stars[data-hover="5"] .tmr__star:nth-child(-n+5){color:var(--yellow)}
.tmr__stars[data-hover] .tmr__star path{filter:drop-shadow(0 0 10px rgba(242,166,0,.45))}
.tmr__star.is-lit{color:var(--yellow)}
.tmr__star.is-lit path{filter:drop-shadow(0 0 12px rgba(242,166,0,.5))}
.tmr__star.is-sweep{animation:tmr-sweep .5s var(--spring) both;animation-delay:var(--sd,0ms)}
@keyframes tmr-sweep{0%{transform:scale(.82) translateY(4px)}
  55%{transform:scale(1.22) translateY(-3px)}100%{transform:none}}
.tmr__star.is-pop{animation:tmr-pop .62s var(--spring)}
@keyframes tmr-pop{0%{transform:none}32%{transform:scale(1.5) rotate(-10deg)}
  62%{transform:scale(.92) rotate(4deg)}100%{transform:none}}
.tmr__preview{color:var(--yellow);font-weight:650}
.tmr__meta{position:relative;min-height:26px;margin-top:12px;font-size:12.5px;color:var(--muted);
  display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap}
.tmr__avg{font-weight:750;font-variant-numeric:tabular-nums;color:var(--ink)}
.tmr__count{opacity:.85}
.tmr__dot{opacity:.4}
.tmr__thanks{display:inline-flex;align-items:center;gap:8px;font-weight:650;color:#B07A00;
  animation:tmr-thanks .55s var(--ease-out) both}
html[data-theme="dark"] .tmr__thanks{color:var(--yellow-l)}
@keyframes tmr-thanks{from{opacity:0;transform:translateY(8px) scale(.9)}to{opacity:1;transform:none}}
.tmr__check{display:inline-flex;width:18px;height:18px;border-radius:50%;align-items:center;
  justify-content:center;background:linear-gradient(160deg,var(--yellow),#E39A00);color:#1A1200;
  font-size:11px;font-weight:900;box-shadow:0 0 14px rgba(242,166,0,.45);
  animation:tmr-check .6s var(--spring) both}
@keyframes tmr-check{0%{transform:scale(0) rotate(-40deg)}70%{transform:scale(1.25) rotate(6deg)}
  100%{transform:none}}
.tmr__meter{position:relative;margin-top:16px;height:5px;border-radius:999px;background:var(--soft);
  overflow:hidden}
.tmr__meterFill{position:relative;height:100%;width:0;border-radius:999px;
  background:linear-gradient(90deg,var(--blue),var(--saffron));
  transition:width 1.1s var(--ease-out)}
.tmr__meterFill::after{content:"";position:absolute;inset:0;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.55),transparent);
  transform:translateX(-100%);animation:tmr-meter 2.6s ease-in-out infinite}
@keyframes tmr-meter{0%{transform:translateX(-100%)}60%,100%{transform:translateX(220%)}}
.tmr__note{position:relative;margin:12px 0 0;font-size:11px;line-height:1.5;color:var(--muted-2)}
.tmr__bit{position:absolute;top:44%;left:50%;width:8px;height:8px;pointer-events:none;
  animation:tmr-bit var(--t,1.1s) cubic-bezier(.2,.6,.4,1) forwards}
@keyframes tmr-bit{0%{opacity:1;transform:translate(-50%,-50%) scale(.3) rotate(0deg)}
  100%{opacity:0;transform:translate(calc(-50% + var(--dx)),calc(-50% + var(--dy))) scale(1) rotate(var(--rot))}}
@media (max-width:560px){
  .tmr{border-radius:22px;margin:20px auto}
  .tmr__inner{padding:24px 16px 20px;border-radius:20.5px}
  .tmr__star{width:46px;height:46px}
  .tmr__stars{gap:5px}
  .tmr__title{font-size:19px}
}
@media (prefers-reduced-motion:reduce){
  .tmr,.tmr__star,.tmr__meterFill,.tmr__thanks,.tmr__check,.tmr__inner::after,
  .tmr__meterFill::after,.tmr__spark{animation:none!important;transition:none!important}
  .tmr{opacity:1;transform:none;background:var(--line)}
  .tmr__spark{display:none}
}
"""
