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
