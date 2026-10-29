#!/usr/bin/env python3
"""Write public/llms.txt - the file AI answer engines read.

llms.txt tells an AI crawler (ChatGPT, Gemini, Perplexity, Claude) what the site
is and which URLs matter, in plain markdown. It matters because those engines
increasingly answer "what is a good EMI calculator" directly, and a site they
cannot parse cleanly does not get cited.

The old file had two faults:

  1. its links pointed at the raw `/site/*.html` paths, which now 308-redirect to
     the clean URLs, so every link was a redirect;
  2. it listed guides and news but none of the 101 calculators - the one thing
     the site is actually for.

This generator fixes both by deriving the file from `tools/url-map.json`, the
single source of truth for the clean URL of every page, and reading each page's
real <title>. Nothing is hand-typed, so the file cannot drift from the site.

Run it after `wire_crawl_graph.py` (which finalises url-map) and after
`gen_news.py`. `rebuild.sh` does.

    python3 tools/gen_llms.py
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
URL_MAP = ROOT / "tools" / "url-map.json"
OUT = PUBLIC / "llms.txt"
BASE = "https://tankmetrics.in"

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")

# The pages that are not calculators, guides or news, with their section order.
MAIN = [
    ("/", "Home - all 101 calculators"),
    ("/blog", "Blog - plain-English money guides"),
    ("/news", "News desk - funding, Shark Tank and tax rules"),
    ("/about", "About"),
    ("/contact", "Contact"),
]


def clean(text: str) -> str:
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def title_of(path: Path, fallback: str) -> str:
    """The page's own title, trimmed to the part before the site suffix."""
    if not path.exists():
        return fallback
    raw = path.read_text(encoding="utf-8", errors="replace")
    m = TITLE_RE.search(raw) or H1_RE.search(raw)
    if not m:
        return fallback
    t = clean(m.group(1))
    for sep in (" | Tank Metrics", " - Tank Metrics", " — Tank Metrics"):
        if sep in t:
            t = t.split(sep)[0]
    return t or fallback


def build() -> str:
    m = json.loads(URL_MAP.read_text(encoding="utf-8"))
    calcs = json.loads((ROOT / "tools" / "calcs.json").read_text(encoding="utf-8"))

    # Every calculator clean URL, titled from its own page.
    calc_urls = {cp: built for cp, built in m.items() if built.startswith("/site/tools/")}
    calculators = sorted(
        (cp, title_of(PUBLIC / built.lstrip("/"), cp)) for cp, built in calc_urls.items()
    )

    lines = [
        "# Tank Metrics",
        "",
        "> 101 free, instant business and money calculators for entrepreneurs, "
        "students and small business owners in India. Every tool runs in the "
        "browser, in rupees and crores, with no sign-up. The site also publishes "
        "plain-English guides and a news desk on Indian funding, Shark Tank deals "
        "and money rules.",
        "",
        "## Main pages",
    ]
    for path, label in MAIN:
        lines.append(f"- [{label}]({BASE}{path})")

    lines += ["", "## Calculators (all free, all in \u20b9)",
              "Every page below is a working calculator with a worked example, "
              "a formula and the common mistakes for that specific number."]
    for clean_path, title in calculators:
        lines.append(f"- [{title}]({BASE}{clean_path})")

    # Guides: blog-*.html pages that are not calculators and not news.
    guides = []
    news = []
    for clean_path, built in sorted(m.items()):
        if built.startswith("/site/tools/"):
            continue
        if any(clean_path == p for p, _ in MAIN):
            continue
        title = title_of(PUBLIC / built.lstrip("/"), clean_path)
        if built.startswith("/site/news-"):
            news.append((clean_path, title))
        elif built.startswith("/site/blog-"):
            guides.append((clean_path, title))

    if guides:
        lines += ["", "## Guides"]
        for clean_path, title in guides:
            lines.append(f"- [{title}]({BASE}{clean_path})")
    if news:
        lines += ["", "## News"]
        for clean_path, title in news:
            lines.append(f"- [{title}]({BASE}{clean_path})")

    lines += [
        "",
        "## About this file",
        "Generated from tools/url-map.json, the source of truth for every clean "
        "URL, so no link here is a redirect. Regenerate with tools/gen_llms.py.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    text = build()
    OUT.write_text(text, encoding="utf-8")
    n_links = text.count("\n- [")
    print(f"wrote {OUT.relative_to(ROOT)} ({n_links} links)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
