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
# the banner show the same squircle. Values are fractions of a 42px box.
OUTER_R = 13      # .pwa-mark border-radius
INNER_INSET = 5   # .pwa-mark::after inset
INNER_R = 9       # .pwa-mark::after border-radius

# No outer margin: the tile fills the whole viewBox, exactly like the PNG. An
# inset here would make the tab icon smaller than the raster icons, and the
# raster ones are what the home screen and Google use.
SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <defs><clipPath id="tm"><rect width="64" height="64" rx="20"/></clipPath></defs>
  <g clip-path="url(#tm)">
    <path d="M32 0h32v32H32Z" fill="#4285F4"/>
    <path d="M64 32v32H32V32Z" fill="#EA4335"/>
    <path d="M32 64H0V32h32Z" fill="#F2A600"/>
    <path d="M0 32V0h32v32Z" fill="#34A853"/>
  </g>
  <rect x="7.6" y="7.6" width="48.8" height="48.8" rx="13.7" fill="#ffffff"/>
  <g fill="none" stroke="{ink}" stroke-width="3.2" stroke-linecap="round">
    <path d="M24 24h16"/>
    <path d="M24 30h16"/>
    <path d="M28 24v13a7.5 7.5 0 0 0 15 0"/>
  </g>
</svg>
""".format(ink=INK)


def mark_png(size: int = FAVICON_PX) -> Image.Image:
    """Rasterise the brand mark as a rounded square.

    The tab/app icon used to be a circle while the install banner drew a
    squircle, so the two never matched. Sir asked for the app icon to look like
    the banner mark, so this draws the same four-colour squircle with a white
    inset and the rupee glyph.
    """
    s = size * 4
    half = s // 2
    quad = Image.new("RGBA", (s, s), (255, 255, 255, 0))
    d = ImageDraw.Draw(quad)
    # Four SQUARES, not pieslices. The first version of this used pieslice, which
    # draws a disc, so clipping it to a rounded square still left a circle - the
    # mask only ever removed pixels the disc had already made transparent. The
    # banner is a conic-gradient, so its quadrants reach the corners; these must
    # too, or the icon cannot become a squircle.
    for (x0, y0, x1, y1), colour in zip(
        ((half, 0, s, half), (half, half, s, s),
         (0, half, half, s), (0, 0, half, half)),
        RING,
    ):
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=colour)

    # Clip the quadrants to a rounded square, which is what makes it a squircle.
    img = Image.new("RGBA", (s, s), (255, 255, 255, 0))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, s - 1, s - 1], radius=int(s * OUTER_R / 42), fill=255)
    img.paste(quad, (0, 0), mask)

    d = ImageDraw.Draw(img)
    inset = s * INNER_INSET / 42
    d.rounded_rectangle(
        [inset, inset, s - 1 - inset, s - 1 - inset],
        radius=int(s * INNER_R / 42), fill="#ffffff")
    try:
        f = ImageFont.truetype(FONT_BOLD, int(s * 0.38))
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
    # mark gets sliced. The tile behind the mark is WHITE - Sir asked for it:
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
