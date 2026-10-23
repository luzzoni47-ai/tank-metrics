#!/usr/bin/env python3
"""Generate every Tank Metrics favicon from one brand-mark definition.

The header mark is a four-colour ring with a white centre. Reuse that shape so
browser tabs match the site, and write .svg, .png and .ico for the site and the
project root.

Sizes matter for Google: its favicon crawler only accepts a square icon whose
side is a multiple of 48px (48, 96, 144, 192, ...). The PNG was 256x256, which
is NOT a multiple of 48, so Google ignored it and kept showing the old cached
v0 icon in search results. It is 192x192 now. If you ever change the size,
change FAVICON_PX and the `sizes=` in the <link> tags together - a declaration
that disagrees with the file makes Google distrust the whole icon.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "public" / "site"
PUB = ROOT / "public"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Must be a multiple of 48 for Google to accept it in search results.
FAVICON_PX = 192

QUADRANTS = ["#4285F4", "#EA4335", "#34A853", "#F2A600"]  # TL, TR, BR, BL
INK = "#06038D"

SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <path d="M32 2A30 30 0 0 1 62 32H32Z" fill="#4285F4"/>
  <path d="M62 32A30 30 0 0 1 32 62V32Z" fill="#EA4335"/>
  <path d="M32 62A30 30 0 0 1 2 32h30Z" fill="#34A853"/>
  <path d="M2 32A30 30 0 0 1 32 2v30Z" fill="#F2A600"/>
  <circle cx="32" cy="32" r="21" fill="#ffffff"/>
  <g fill="none" stroke="{ink}" stroke-width="3.2" stroke-linecap="round">
    <path d="M24 24h16"/>
    <path d="M24 30h16"/>
    <path d="M28 24v13a7.5 7.5 0 0 0 15 0"/>
  </g>
</svg>
""".format(ink=INK)


def mark_png(size: int = FAVICON_PX) -> Image.Image:
    """Rasterise the same mark: coloured ring, white centre, rupee glyph."""
    s = size * 4
    img = Image.new("RGBA", (s, s), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    box = [0, 0, s - 1, s - 1]
    # quadrants start at 12 o'clock, clockwise
    d.pieslice(box, 270, 360, fill=QUADRANTS[0])
    d.pieslice(box, 0, 90, fill=QUADRANTS[1])
    d.pieslice(box, 90, 180, fill=QUADRANTS[2])
    d.pieslice(box, 180, 270, fill=QUADRANTS[3])
    inner = s * 21 / 64  # the SVG's white circle is r=21 in a 64 viewBox
    d.ellipse([s / 2 - inner, s / 2 - inner, s / 2 + inner, s / 2 + inner], fill="#ffffff")
    try:
        f = ImageFont.truetype(FONT_BOLD, int(s * 0.42))
        d.text((s / 2, s / 2), "\u20b9", font=f, fill=INK, anchor="mm")
    except Exception:
        pass
    return img.resize((size, size), Image.LANCZOS)


# PWA / home-screen icons. These are NOT bound by Google's multiple-of-48
# rule (that one applies to the search-result favicon); 192 and 512 are the
# sizes Android and Chrome expect in a manifest.
PWA_SIZES = [192, 512]

MANIFEST = """{{
  "name": "Tank Metrics",
  "short_name": "Tank Metrics",
  "description": "Free business and money calculators for India.",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#FF9933",
  "icons": [
{icons}
  ]
}}
"""


def main() -> None:
    (SITE / "favicon.svg").write_text(SVG, encoding="utf-8")
    (PUB / "favicon.svg").write_text(SVG, encoding="utf-8")
    icon = mark_png(FAVICON_PX)
    for d in (SITE, PUB):
        icon.save(d / "favicon.png")
        icon.save(d / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

    # Every icon slot the browser or the OS can ask for, so the brand mark
    # shows up in the tab, in search, and on the home screen alike.
    entries = []
    for size in PWA_SIZES:
        mark_png(size).save(SITE / f"icon-{size}.png")
        entries.append(
            '    {{ "src": "/site/icon-{0}.png", "sizes": "{0}x{0}", '
            '"type": "image/png", "purpose": "any" }},'.format(size)
        )
    # A maskable icon is cropped to whatever shape the launcher likes (a
    # circle on most Androids), so the art must fit an 80% safe zone or the
    # ring gets sliced. The tile behind the mark is WHITE - Sir asked for it:
    # a coloured tile made the home-screen icon look like a blob next to every
    # other white-backed app icon.
    maskable = Image.new("RGBA", (512, 512), "#FFFFFF")
    art = mark_png(410)
    maskable.paste(art, ((512 - 410) // 2, (512 - 410) // 2), art)
    maskable.save(SITE / "icon-maskable-512.png")
    entries.append(
        '    { "src": "/site/icon-maskable-512.png", "sizes": "512x512", '
        '"type": "image/png", "purpose": "maskable" }'
    )
    (SITE / "manifest.webmanifest").write_text(
        MANIFEST.format(icons="\n".join(entries)), encoding="utf-8"
    )
    print(
        f"wrote favicon.svg/.png({FAVICON_PX}x{FAVICON_PX})/.ico, "
        f"icon-{{192,512}}.png and manifest.webmanifest to public/site/"
    )


if __name__ == "__main__":
    main()
