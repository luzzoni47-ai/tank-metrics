#!/usr/bin/env python3
"""Append one validated story to tools/news.json.

Why this exists: `tools/news.json` is 91 KB and the daily news runbook told the
agent to read it "for the exact field list" and then hand-edit it. Reading it
plus writing the story was most of the run's 30-minute budget, and the run kept
being killed before it reached the deploy step. The field list is fixed, so the
agent now supplies a small JSON file with the new story only, and this appends
it in the right shape and refuses anything that breaks a rule.

The story JSON the author writes:

    {
      "slug": "rupee-falls-to-95-22-what-it-costs-importers-exporters",
      "title": "Rupee Falls to 95.22: What It Costs Importers",
      "dek": "150-158 characters ...",
      "category": "Small Business",
      "date": "2026-10-26",
      "date_display": "October 26, 2026",
      "source_name": "The Hindu",
      "source_url": "https://...",
      "cta": {"text": "...", "href": "/landed-cost-calculator",
              "label": "Open the Landed Cost Calculator"},
      "related": [{"slug": "markup-vs-margin-explained",
                   "title": "Markup vs Margin Explained"}],
      "body_en": ["<p>...</p>", "<h2>...</h2>", "..."],
      "body_hinglish": ["<p>...</p>", "<h2>...</h2>", "..."]
    }

    python3 tools/new_news_story.py --story /tmp/story.json

Then run `python3 tools/gen_news.py` and the pipeline.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEWS = ROOT / "tools" / "news.json"

FIELD_ORDER = [
    "slug", "title", "dek", "category", "date", "date_display",
    "source_name", "source_url", "cta", "related", "body_en", "body_hinglish",
]
TITLE_MAX = 60
DEK_MIN, DEK_MAX = 150, 158
MIN_WORDS = 400
DEVANAGARI = re.compile(r"[\u0900-\u097F]")
HEADING = re.compile(r"<h[23]\b", re.I)
SLUG_OK = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _headings(paras: list[str]) -> int:
    return sum(len(HEADING.findall(p)) for p in paras)


def _words(paras: list[str]) -> int:
    return len(re.sub(r"<[^>]+>", " ", " ".join(paras)).split())


def validate(story: dict, existing_slugs: set[str]) -> list[str]:
    problems: list[str] = []
    missing = [f for f in FIELD_ORDER if f not in story]
    if missing:
        return [f"missing field(s): {', '.join(missing)}"]

    slug = story["slug"]
    if not SLUG_OK.match(slug):
        problems.append(f"slug must be lowercase words joined by dashes: {slug!r}")
    if slug in existing_slugs:
        problems.append(f"slug already exists in news.json: {slug}")

    title = story["title"]
    if len(title) > TITLE_MAX:
        problems.append(f"title is {len(title)} chars, max {TITLE_MAX} (the page adds ' | Tank Metrics')")

    dek = story["dek"]
    if not (DEK_MIN <= len(dek) <= DEK_MAX):
        problems.append(f"dek is {len(dek)} chars, need {DEK_MIN}-{DEK_MAX}")

    try:
        datetime.date.fromisoformat(story["date"])
    except (ValueError, TypeError):
        problems.append(f"date must be ISO YYYY-MM-DD: {story['date']!r}")

    if not str(story["source_url"]).startswith("http"):
        problems.append("source_url must be a real http(s) URL")

    cta = story["cta"]
    if not isinstance(cta, dict) or not {"text", "href", "label"} <= set(cta):
        problems.append("cta must have text, href and label")
    elif not str(cta["href"]).startswith("/"):
        problems.append(f"cta.href must be a site path: {cta['href']!r}")

    for key in ("body_en", "body_hinglish"):
        body = story[key]
        if not isinstance(body, list) or not body:
            problems.append(f"{key} must be a non-empty list of HTML paragraphs")

    en, hi = story["body_en"], story["body_hinglish"]
    if isinstance(en, list) and isinstance(hi, list):
        if _headings(en) != _headings(hi):
            problems.append(
                f"heading counts differ: body_en has {_headings(en)}, "
                f"body_hinglish has {_headings(hi)}"
            )
        words = _words(en)
        if words < MIN_WORDS:
            problems.append(f"body_en is {words} words, expected {MIN_WORDS}+")
        if DEVANAGARI.search(" ".join(hi)):
            problems.append("body_hinglish contains Devanagari - it must be roman script")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--story", required=True, help="JSON file holding the one new story")
    ap.add_argument("--allow-duplicate", action="store_true",
                    help="replace an existing story with the same slug")
    a = ap.parse_args()

    story = json.loads(Path(a.story).read_text(encoding="utf-8"))
    if not isinstance(story, dict):
        print("error: the story file must hold a single JSON object", file=sys.stderr)
        return 1

    raw = NEWS.read_text(encoding="utf-8")
    doc = json.loads(raw)
    items = doc["items"]
    existing = {it["slug"] for it in items}

    problems = validate(story, set() if a.allow_duplicate else existing)
    if problems:
        for p in problems:
            print(f"error: {p}", file=sys.stderr)
        return 1

    ordered = {k: story[k] for k in FIELD_ORDER}
    items[:] = [it for it in items if it["slug"] != story["slug"]]
    items.insert(0, ordered)

    NEWS.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"added story: {story['slug']} ({len(items)} items, newest first)")
    print("next: python3 tools/gen_news.py && bash tools/publish_news.sh <slug>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
