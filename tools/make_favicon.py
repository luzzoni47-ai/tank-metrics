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

# Quadrant order is the conic-gradient order used by .brand-mark and .pwa-mark
# in style.css: start at 12 o'clock and go clockwise.
RING = ["#4285F4", "#EA4335", "#F2A600", "#34A853"]  # TR, BR, BL, TL
INK = "#06038D"

# Geometry copied from the install banner's mark (.pwa-mark) so the app icon and
# the banner show the same mark. Values are fractions of a 42px box.
INNER_INSET = 5   # .pwa-mark::after inset
INNER_R = 9       # .pwa-mark::after border-radius

# The colour runs to every edge and corner - no outer rounding, so no transparent
# corner for a white launcher background to show through. Only the white panel is
# rounded. An inset or an rx here would put a pale border around the logo, which
# is exactly what Sir asked to remove.
SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <path d="M32 0h32v32H32Z" fill="#4285F4"/>
  <path d="M64 32v32H32V32Z" fill="#EA4335"/>
  <path d="M32 64H0V32h32Z" fill="#F2A600"/>
  <path d="M0 32V0h32v32Z" fill="#34A853"/>
  <rect x="7.6" y="7.6" width="48.8" height="48.8" rx="13.7" fill="#ffffff"/>
  <g fill="none" stroke="{ink}" stroke-width="3.2" stroke-linecap="round">
    <path d="M24 24h16"/>
    <path d="M24 30h16"/>
    <path d="M28 24v13a7.5 7.5 0 0 0 15 0"/>
  </g>
</svg>
""".format(ink=INK)


def mark_png(
    size: int = FAVICON_PX,
    panel_inset: float = INNER_INSET / 42,
    glyph_frac: float = 0.56,
) -> Image.Image:
    """Rasterise the brand mark: colour edge-to-edge, white panel, rupee.

    Sir's brief: the colour must reach every edge and corner - no white and no
    transparent band on the OUTSIDE. Where a corner is green, the corner is
    green; the same for red, yellow and blue. An earlier version rounded the
    outer corners, so those pixels were transparent, and the launcher's own
    background (usually white) showed through as a pale border. Another version
    drew the maskable as a white tile with the art centred, which put a solid
    white frame around the logo. Both are gone: the quadrants now fill the whole
    square, corner to corner.

    `panel_inset` is the white panel's margin as a fraction of the side. The
    maskable icon passes a larger value so the panel survives Android's crop
    (see `maskable_png`).
    """
    s = size * 4
    half = s // 2
    # Opaque from the first pixel: nothing outside the colour can show through.
    img = Image.new("RGBA", (s, s), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)
    # Four SQUARES, not pieslices. pieslice draws a disc, so its quadrants never
    # reach the corners and the icon could not be edge-to-edge colour.
    for (x0, y0, x1, y1), colour in zip(
        ((half, 0, s, half), (half, half, s, s),
         (0, half, half, s), (0, 0, half, half)),
        RING,
    ):
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=colour)

    inset = s * panel_inset
    d.rounded_rectangle(
        [inset, inset, s - 1 - inset, s - 1 - inset],
        radius=int(s * INNER_R / 42), fill="#ffffff")
    try:
        # 0.56 puts the rupee's ink at ~54% of the white panel. At the old 0.38
        # it was ~36%, which read as a speck in the middle of the tile.
        f = ImageFont.truetype(FONT_BOLD, int(s * glyph_frac))
        d.text((s / 2, s / 2), "\u20b9", font=f, fill=INK, anchor="mm")
    except Exception:
        pass
    return img.resize((size, size), Image.LANCZOS)


def maskable_png(size: int = 512) -> Image.Image:
    """A maskable icon: full-bleed colour, with the panel inside the safe zone.

    Android crops a maskable icon to whatever shape the launcher wants (a circle
    on most phones), keeping only the centre 80% circle. The white panel is a
    rounded square, so its CORNERS are the first thing a circular crop bites.
    Its half-diagonal is (0.5 - inset) x sqrt(2), and that must stay under the
    0.40 safe radius, so the inset cannot be below 0.217. 0.22 is the largest
    panel that still survives a circular crop, and the glyph is sized to fill
    ~55% of that panel so the rupee reads clearly at home-screen size. The
    colour still bleeds to every edge, so no white frame can appear.
    """
    return mark_png(size, panel_inset=0.22, glyph_frac=0.42)


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
    # circle on most Androids), so the art must fit the safe zone or the mark
    # gets sliced. The COLOUR still bleeds to every edge - only the white panel
    # is inset - so no white frame can show around the logo. An earlier version
    # put the art on a white 512 tile, which produced exactly the pale border
    # Sir asked to remove.
    maskable_png(512).save(SITE / "icon-maskable-512.png")
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
