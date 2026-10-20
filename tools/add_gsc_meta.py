#!/usr/bin/env python3
"""Add the Google Search Console verification meta tag to every page.

The domain is already verified via a DNS TXT record; this meta tag adds a
second, redundant signal so a URL-prefix property can also be verified.
The tag lives in <head> and is invisible to visitors.
"""
from pathlib import Path

SITE = Path("/workspace/project/public/site")
TOKEN = "CyIhu9CYYQapfzYJOeSLTP_XY_HWq0McbmY4uX342o4"
META = f'<meta name="google-site-verification" content="{TOKEN}">'

changed = 0
for f in sorted(SITE.glob("*.html")):
    t = f.read_text(encoding="utf-8")
    if "google-site-verification" in t:
        print(f"  already present: {f.name}")
        continue
    if "<meta charset" in t:
        i = t.index("<meta charset")
        j = t.index(">", i) + 1
        t = t[:j] + META + t[j:]
    elif "<head>" in t:
        t = t.replace("<head>", "<head>" + META, 1)
    else:
        print(f"  SKIP (no head): {f.name}")
        continue
    f.write_text(t, encoding="utf-8")
    changed += 1

print(f"\nverification tag added to {changed} files")
