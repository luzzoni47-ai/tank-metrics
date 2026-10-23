#!/usr/bin/env python3
"""Make the site installable, and make the calculators work offline.

Each page gets two things, and running this twice changes nothing:

1. The manifest link is replaced by a small block: the manifest plus the
   `apple-mobile-web-app-*` meta tags, so iOS and Android both offer "Add to
   Home screen" and the installed app opens without browser chrome.
2. A three-line service-worker registration. The worker
   (`public/site/sw.js`) caches the shell on install and answers a page view
   from cache when the network is gone, so a calculator opened once keeps
   working with the phone offline.

Idempotency is by exact string match, not a regex over the head: a greedy
pattern here once swallowed the neighbouring `google-site-verification` tag
and broke Search Console verification on all 123 pages. Keep it literal.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "public" / "site"

MANIFEST_LINK = '<link rel="manifest" href="/site/manifest.webmanifest">'
MARKER = "<!-- pwa -->"

BLOCK = MARKER + (
    '<link rel="manifest" href="/site/manifest.webmanifest">'
    '<meta name="theme-color" content="#FF9933">'
    '<meta name="mobile-web-app-capable" content="yes">'
    '<meta name="apple-mobile-web-app-capable" content="yes">'
    '<meta name="apple-mobile-web-app-status-bar-style" content="default">'
    '<meta name="apple-mobile-web-app-title" content="Tank Metrics">'
    '<link rel="apple-touch-icon" href="/site/icon-192.png">'
    '<script defer src="/site/pwa.js"></script>'
    '<script defer src="/site/nav.js"></script>'
)

# The menu button was hidden on every page except the home page, and the home
# page's own sidebar is the only thing it ever opened. Show it everywhere and
# label it with three dots, so the drawer in nav.js is reachable.
OLD_MENU = ('<button class="menu-btn" id="menuBtn" aria-label="Menu" '
            'style="visibility:hidden">\u2630</button>')
NEW_MENU = ('<button class="menu-btn" id="menuBtn" type="button" '
            'aria-label="Open menu" aria-expanded="false">\u2022\u2022\u2022</button>')
NAV_SCRIPT = '<script defer src="/site/nav.js"></script>'


def patch_nav(text: str) -> str:
    """Add the drawer script and un-hide the menu button. Idempotent."""
    if NAV_SCRIPT not in text:
        if "</body>" in text:
            text = text.replace("</body>", NAV_SCRIPT + "</body>", 1)
        else:
            text = text + NAV_SCRIPT
    text = text.replace(OLD_MENU, NEW_MENU)
    return text


def pages() -> list:
    found = [SITE / "index.html"]
    found += sorted(SITE.glob("*.html"))
    found += sorted((SITE / "tools").glob("*.html"))
    return sorted(set(found))


# The first version inlined the registration. Swap it for the shared file so
# the install/update notices live in one place.
OLD_INLINE = (
    "<script>if('serviceWorker' in navigator){window.addEventListener('load',"
    "function(){navigator.serviceWorker.register('/site/sw.js')"
    ".catch(function(){});});}</script>"
)


def patch(text: str) -> str:
    if OLD_INLINE in text:
        text = text.replace(OLD_INLINE, '<script defer src="/site/pwa.js"></script>', 1)
    if MARKER in text:
        return text
    if MANIFEST_LINK in text:
        return text.replace(MANIFEST_LINK, BLOCK, 1)
    return text.replace("</head>", BLOCK + "</head>", 1)


def main() -> None:
    changed = 0
    for page in pages():
        text = page.read_text(encoding="utf-8")
        new = patch_nav(patch(text))
        if new != text:
            page.write_text(new, encoding="utf-8")
            changed += 1
    print(f"pwa block + nav drawer added to {changed} page(s)")


if __name__ == "__main__":
    main()
