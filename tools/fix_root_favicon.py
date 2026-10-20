#!/usr/bin/env python3
"""Regenerate the root-level icons with the Tank Metrics brand mark.

Requests to /favicon.ico or /favicon.png must not fall back to the old v0 logo.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SITE = Path("/workspace/project/public/site")
PUB = Path("/workspace/project/public")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

mark = Image.new("RGBA", (256, 256), (255, 255, 255, 0))
d = ImageDraw.Draw(mark)
d.rounded_rectangle([0, 0, 255, 255], radius=56, fill="#ffffff")
box = [7, 7, 248, 248]
d.pieslice(box, 270, 360, fill="#4285F4")
d.pieslice(box, 0, 90, fill="#EA4335")
d.pieslice(box, 90, 180, fill="#34A853")
d.pieslice(box, 180, 270, fill="#F2A600")
try:
    f = ImageFont.truetype(FONT, 128)
    d.text((128, 128), "\u20b9", font=f, fill="#142434", anchor="mm")
except Exception:
    pass

mark.save(PUB / "favicon.png")
mark.save(SITE / "favicon.png")
mark.save(PUB / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
mark.save(SITE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
print("regenerated root + site favicon.ico / .png")
