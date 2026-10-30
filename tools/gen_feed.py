#!/usr/bin/env python3
"""Build /feed.xml — an RSS 2.0 feed of the news and blog posts.

Why the site needs one: Bing and the other IndexNow engines accept a *feed* as
a standing instruction to re-crawl, and `SubmitFeed` costs no submission quota
(unlike `SubmitUrl`, which is capped at 100 URLs a day). Without a feed, every
new article has to be pushed by hand or waited on.

The feed is assembled from the sources the site already has - `tools/news.json`
for the stories and the `datePublished` in each `blog-*.html`'s JSON-LD for the
guides - so there is no second copy of the content to keep in sync.

    python3 tools/gen_feed.py

Writes `public/feed.xml` and `public/site/feed.xml` (the clean path serves the
site copy). Run from rebuild.sh after gen_news.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
NEWS = json.loads((Path(__file__).resolve().parent / "news.json").read_text(encoding="utf-8"))
BASE = "https://tankmetrics.in"
TITLE = "Tank Metrics — Startups, Shark Tank and Money in Rupees"
DESC = ("Shark Tank India deals, startup valuation and the money maths behind Indian "
        "businesses, explained in plain English and Hinglish.")
LIMIT = 30


def news_items() -> list[dict]:
    out = []
    for it in NEWS["items"]:
        out.append({
            "title": it["title"],
            "link": f"{BASE}/news/{it['slug']}",
            "desc": it.get("dek", ""),
            "date": it.get("date", ""),
            "cat": it.get("category", "News"),
        })
    return out


def blog_items() -> list[dict]:
    """Read the date and description straight out of each built post.

    The blog has no JSON source - `new_blog_post.py` writes the page - so the
    published page is the source of truth, which also means the feed can never
    disagree with what a reader sees.
    """
    out = []
    for p in sorted(SITE.glob("blog-*.html")):
        t = p.read_text(encoding="utf-8")
        m = re.search(r'"datePublished"\s*:\s*"([\d-]+)"', t)
        if not m:
            continue
        d = re.search(r'<meta name="description" content="([^"]*)"', t)
        h = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S)
        title = re.sub(r"<[^>]+>", "", h.group(1)).strip() if h else p.stem
        out.append({
            "title": title,
            "link": f"{BASE}/{p.stem[len('blog-'):]}",
            "desc": d.group(1) if d else "",
            "date": m.group(1),
            "cat": "Guide",
        })
    return out


def rfc822(d: str) -> str:
    try:
        dt = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        dt = datetime.now(timezone.utc)
    return format_datetime(dt)


def build() -> str:
    items = news_items() + blog_items()
    items = [i for i in items if i["date"]]
    items.sort(key=lambda i: i["date"], reverse=True)
    items = items[:LIMIT]

    now = format_datetime(datetime.now(timezone.utc))
    body = []
    for i in items:
        link = i["link"]
        body.append(f"""  <item>
    <title>{escape(i['title'])}</title>
    <link>{escape(link)}</link>
    <guid isPermaLink="true">{escape(link)}</guid>
    <pubDate>{rfc822(i['date'])}</pubDate>
    <category>{escape(i['cat'])}</category>
    <description>{escape(i['desc'])}</description>
  </item>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{escape(TITLE)}</title>
  <link>{BASE}/</link>
  <description>{escape(DESC)}</description>
  <language>en-in</language>
  <lastBuildDate>{now}</lastBuildDate>
  <atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(body)}
</channel>
</rss>
"""


def main() -> None:
    xml = build()
    (ROOT / "public" / "feed.xml").write_text(xml, encoding="utf-8")
    (SITE / "feed.xml").write_text(xml, encoding="utf-8")
    n = xml.count("<item>")
    print(f"wrote feed.xml with {n} items")


if __name__ == "__main__":
    main()
