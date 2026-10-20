#!/usr/bin/env python3
"""Generate every Tank Metrics favicon from one brand-mark definition.

The header mark is a four-colour ring with a white centre. Reuse that shape so
browser tabs match the site, and write .svg, .png and .ico for the site and the
project root.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SITE = Path("/workspace/project/public/site")
PUB = Path("/workspace/project/public")
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

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


def mark_png(size: int = 256) -> Image.Image:
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


def main() -> None:
    (SITE / "favicon.svg").write_text(SVG, encoding="utf-8")
    (PUB / "favicon.svg").write_text(SVG, encoding="utf-8")
    for icon in (mark_png(256),):
        for d in (SITE, PUB):
            icon.save(d / "favicon.png")
            icon.save(d / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print("wrote favicon.svg/.png/.ico to public/ and public/site/")


if __name__ == "__main__":
    main()
