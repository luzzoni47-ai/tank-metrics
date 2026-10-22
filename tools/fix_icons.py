#!/usr/bin/env python3
"""Replace the inherited v0 icons with the Tank Metrics brand mark.

The static pages pointed every icon slot at icon.svg, which held the v0 logo,
so browser tabs showed a black "V0" square. favicon.svg was also broken (a
saved 404 HTML page). Write a real bank-mark SVG and point every page at the
.ico/.png/.svg set explicitly.
"""
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "public" / "site"

# --- brand mark: four Google-coloured quadrants + rupee sign -----------------
svg = """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#ffffff"/>
  <path d="M32 2A30 30 0 0 1 62 32H32Z" fill="#4285F4"/>
  <path d="M62 32A30 30 0 0 1 32 62V32Z" fill="#EA4335"/>
  <path d="M32 62A30 30 0 0 1 2 32h30Z" fill="#34A853"/>
  <path d="M2 32A30 30 0 0 1 32 2v30Z" fill="#F2A600"/>
  <g stroke="#F2A600" stroke-width="3">
    <line x1="22" y1="21" x2="42" y2="21"/>
    <line x1="22" y1="28" x2="42" y2="28"/>
  </g>
  <path d="M26 21v14a7 7 0 0 0 14 0" fill="none" stroke="#142434" stroke-width="4" stroke-linecap="round"/>
</svg>
"""
(SITE / "favicon.svg").write_text(svg, encoding="utf-8")

ICON_LINKS = (
    '<link rel="icon" href="/site/favicon.ico" sizes="any">'
    '<link rel="icon" href="/site/favicon.svg" type="image/svg+xml">'
    '<link rel="icon" href="/site/favicon.png" type="image/png" sizes="192x192">'
    '<link rel="apple-touch-icon" href="/site/favicon.png" sizes="192x192"><link rel="manifest" href="/site/manifest.webmanifest">'
)

# match every icon-ish link tag so no old reference survives
ICON_RE = re.compile(
    r'<link[^>]+rel="(?:icon|shortcut icon|apple-touch-icon|mask-icon)"[^>]*>', re.I)

changed = 0
for f in sorted(SITE.glob("*.html")):
    t = f.read_text(encoding="utf-8")
    if 'rel="icon"' not in t and "icon.svg" not in t:
        print(f"  no icon links: {f.name}")
        continue
    new, n = ICON_RE.subn("", t)
    # re-insert the fresh set right after the charset meta
    i = new.index("<meta charset")
    j = new.index(">", i) + 1
    new = new[:j] + ICON_LINKS + new[j:]
    if new != t:
        f.write_text(new, encoding="utf-8")
        changed += 1
        print(f"  {f.name}: replaced {n} link(s)")

print(f"\nupdated {changed} files")
