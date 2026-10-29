#!/usr/bin/env python3
"""Stamp out a new blog post from the site's own shell.

Why this exists: the daily guide run was hand-writing ~15 KB of boilerplate
(doctype, head, trivially repeated footer and the language toggle script) and
re-reading all nine existing posts to copy their structure. That is most of the
LLM budget the runbook has, and the run kept dying at the 30-minute cap before
it reached the deploy step. The shell is identical on every post, so it belongs
in code, not in the model's output.

The author supplies only the two things that are actually new — the English
article body and the Hindi source — and this assembles the page, the blog card
and the Hinglish source registration around them.

    python3 tools/new_blog_post.py \
        --slug import-duty-explained \
        --title "What Import Duty Really Adds to Your Order" \
        --desc "Import duty and IGST explained ..." \
        --cat "Pricing & Costs" --accent "#4285f4" \
        --hero "Duty and IGST, in the order they are charged." \
        --en /tmp/en.html --hi /tmp/hi.html

Then run the normal pipeline (rebuild.sh or the guide runbook's step 5 onward).
`add_blog_schema.py`, `add_pwa.py` and `fix_blog_meta.py` all run later and fill
in the schema, the PWA block and the og: tags, so this only has to produce a
page the rest of the pipeline recognises.
"""
from __future__ import annotations

import argparse
import datetime
import html as html_mod
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
HINDI = ROOT / "tools" / "hindi"
BASE = "https://tankmetrics.in"
BRAND = "Tank Metrics"
TITLE_MAX = 60
DESC_MIN, DESC_MAX = 150, 158

TITLE_TAG = re.compile(r"<title>.*?</title>", re.S)
DESC_TAG = re.compile(r'<meta name="description" content="[^"]*">')
CANON = re.compile(r'<link rel="canonical" href="[^"]*"')
OG_TITLE = re.compile(r'<meta property="og:title" content="[^"]*">')
OG_DESC = re.compile(r'<meta property="og:description" content="[^"]*">')
OG_URL = re.compile(r'<meta property="og:url" content="[^"]*">')
TW_TITLE = re.compile(r'<meta name="twitter:title" content="[^"]*">')
TW_DESC = re.compile(r'<meta name="twitter:description" content="[^"]*">')


def _reference_post() -> str:
    """Any existing post, used as the shell template."""
    for p in sorted(SITE.glob("blog-*.html")):
        body = p.read_text(encoding="utf-8")
        if 'class="post-lang" data-lang="en"' in body and 'class="lang-toggle"' in body:
            return body
    raise SystemExit("no existing blog post to copy the shell from")


def _head(reference: str, full_title: str, desc: str, canonical: str) -> str:
    head = reference[: reference.index("</head>") + len("</head>")]
    head = TITLE_TAG.sub(f"<title>{full_title}</title>", head, count=1)
    head = DESC_TAG.sub(f'<meta name="description" content="{desc}">', head, count=1)
    head = CANON.sub(f'<link rel="canonical" href="{canonical}"', head, count=1)
    head = OG_TITLE.sub(f'<meta property="og:title" content="{full_title}">', head, count=1)
    head = OG_DESC.sub(f'<meta property="og:description" content="{desc}">', head, count=1)
    head = OG_URL.sub(f'<meta property="og:url" content="{canonical}">', head, count=1)
    head = TW_TITLE.sub(f'<meta name="twitter:title" content="{full_title}">', head, count=1)
    head = TW_DESC.sub(f'<meta name="twitter:description" content="{desc}">', head, count=1)
    return head


def _shell_top(reference: str) -> str:
    """From <body> through the post-meta row, before the English block."""
    start = reference.index("<body>")
    stop = reference.index('<div class="post-lang" data-lang="en"')
    return reference[start:stop]


def _shell_bottom(reference: str) -> str:
    """From after the Hinglish block to </html> — footer and the toggle script."""
    marker = '<div class="post-lang" data-lang="hinglish"'
    start = reference.index(marker)
    end = reference.index("</div>", reference.index("</div>", start) + len("</div>"))
    return reference[end + len("</div>") :]


def _hero(top: str, hero: str) -> str:
    return re.sub(r"<p>.*?</p>", f"<p>{html_mod.escape(hero)}</p>", top, count=1, flags=re.S)


def _meta(top: str, cat: str, date: str) -> str:
    top = re.sub(
        r'<span class="tag2">.*?</span>',
        f'<span class="tag2">{html_mod.escape(cat)}</span>',
        top,
        count=1,
        flags=re.S,
    )
    return re.sub(r"<span>[^<]*</span>", f"<span>{date}</span>", top, count=1)


def _h1(top: str, title: str) -> str:
    return re.sub(r"<h1>.*?</h1>", f"<h1>{html_mod.escape(title)}</h1>", top, count=1, flags=re.S)


def _cta(card: str, en_text: str, hi_text: str) -> tuple[str, str]:
    """The call to action each language block must end with.

    `test_blog.check_post_structure()` fails a post whose language block has no
    `cta-inline`, and the CTA is the only link that turns a reader into a
    calculator user — so it is generated here rather than left to be remembered.
    """
    en = (
        f'<div class="cta-inline"><p>{html_mod.escape(en_text)}</p>'
        f'<a class="btn-primary" href="/#card_{card}">Open the calculator →</a></div>'
    )
    hi = (
        f'<div class="cta-inline"><p>{html_mod.escape(hi_text)}</p>'
        f'<a class="btn-primary" href="/#card_{card}">Calculator kholen →</a></div>'
    )
    return en, hi


def _card(slug: str, cat: str, title: str, desc: str, accent: str) -> str:
    return (
        f'<a class="blog-card" href="/{slug}" style="border-top-color:{accent}">'
        f'<span class="cat">{html_mod.escape(cat)}</span>'
        f"<h2>{html_mod.escape(title)}</h2>"
        f"<p>{html_mod.escape(desc)}</p>"
        f'<span class="readmore">Read the guide →</span> </a>'
    )


def add_card(slug: str, card: str) -> bool:
    """Insert the card at the end of the Guides grid. Idempotent."""
    page = SITE / "blog.html"
    body = page.read_text(encoding="utf-8")
    if f'href="/{slug}"' in body:
        return False
    start = body.index('id="paneGuides"')
    end = body.index("</div></div>", start)
    body = body[:end] + card + body[end:]
    page.write_text(body, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True, help="headline without the brand suffix")
    ap.add_argument("--desc", required=True)
    ap.add_argument("--cat", required=True)
    ap.add_argument("--accent", default="#4285f4")
    ap.add_argument("--hero", default="")
    ap.add_argument("--date", default="")
    ap.add_argument("--en", required=True, help="file holding the English article body")
    ap.add_argument("--hi", required=True, help="file holding the Hindi source body")
    ap.add_argument("--cta-card", required=True,
                    help="calculator card id the CTA points at, e.g. importduty")
    ap.add_argument("--cta-en", default="Run your own numbers in seconds — free, in your browser, nothing saved.")
    ap.add_argument("--cta-hi", default="Apne aankde secondon mein nikalein — muft, aapke browser mein, kuch bhi save nahi hota.")
    a = ap.parse_args()

    slug = a.slug.strip().lstrip("/")
    full_title = f"{a.title.strip()} | {BRAND}"
    canonical = f"{BASE}/{slug}"

    problems = []
    if len(full_title) > TITLE_MAX:
        problems.append(f"title is {len(full_title)} chars, max {TITLE_MAX}: {full_title!r}")
    if not (DESC_MIN <= len(a.desc) <= DESC_MAX):
        problems.append(f"description is {len(a.desc)} chars, need {DESC_MIN}-{DESC_MAX}")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", a.accent):
        problems.append(f"accent {a.accent!r} is not a #RRGGBB colour")
    if problems:
        for p in problems:
            print(f"error: {p}", file=sys.stderr)
        return 1

    en_body = Path(a.en).read_text(encoding="utf-8").strip()
    hi_body = Path(a.hi).read_text(encoding="utf-8").strip()
    if not en_body.startswith("<"):
        print("error: --en must be an HTML fragment (start with <p>)", file=sys.stderr)
        return 1
    if not hi_body.startswith("<"):
        print("error: --hi must be an HTML fragment (start with <p>)", file=sys.stderr)
        return 1

    date = a.date.strip() or datetime.date.today().strftime("%B %-d, %Y")

    ref = _reference_post()
    top = _shell_top(ref)
    top = _hero(top, a.hero or a.desc)
    top = _h1(top, a.title.strip())
    top = _meta(top, a.cat, date)

    en_cta, hi_cta = _cta(a.cta_card, a.cta_en, a.cta_hi)
    hi_body = hi_body + "\n" + hi_cta

    page = (
        _head(ref, full_title, a.desc, canonical)
        + top
        + '<div class="post-lang" data-lang="en">\n'
        + en_body
        + "\n"
        + en_cta
        + "\n</div>"
        + _shell_bottom(ref)
    )

    out = SITE / f"blog-{slug}.html"
    if out.exists():
        print(f"error: {out} already exists", file=sys.stderr)
        return 1
    out.write_text(page, encoding="utf-8")
    (HINDI / f"blog-{slug}.hi.html").write_text(hi_body + "\n", encoding="utf-8")

    card = _card(slug, a.cat, a.title.strip(), a.desc, a.accent)
    added = add_card(slug, card)

    print(f"created {out.relative_to(ROOT)}")
    print(f"created {(HINDI / f'blog-{slug}.hi.html').relative_to(ROOT)}")
    print(f"blog card {'added' if added else 'already present'}")
    print("next: python3 tools/hinglish.py --rebuild && bash tools/rebuild.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
