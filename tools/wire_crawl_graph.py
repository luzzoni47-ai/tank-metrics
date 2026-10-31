#!/usr/bin/env python3
"""Wire the new tool pages into the site's crawl graph.

Two jobs:
1. Turn each entry in the home page's hidden SEO catalogue into a real link to
   its tool page, so crawlers can walk from the home page to all 100 tools.
   The catalogue is replaced by renderAll() for JS clients, so visitors see
   nothing new.
2. Rebuild public/sitemap.xml so every tool page is listed.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "public" / "site"
DATA = json.loads((Path(__file__).parent / "calcs.json").read_text(encoding="utf-8"))
BASE = "https://tankmetrics.in"


def slugify(name: str) -> str:
    s = name.lower().replace("&", " and ").replace("%", " percent ")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return re.sub(r"-{2,}", "-", s)


def build_slugs() -> dict[str, str]:
    seen: dict[str, int] = {}
    out: dict[str, str] = {}
    catnames = {x["id"]: x["name"] for x in DATA["cats"]}
    for c in DATA["calcs"]:
        slug = slugify(c["name"])
        if slug in seen:
            slug = f"{slug}-{slugify(catnames.get(c['cat'], c['cat']))}"
        else:
            seen[slug] = 1
        out[c["id"]] = slug
    return out


SLUGS = build_slugs()


def link_catalogue() -> int:
    p = SITE / "index.html"
    t = p.read_text(encoding="utf-8")
    count = 0
    # Two tools can share a name, so replace the Nth occurrence of a heading
    # with the Nth calculator's own page rather than reusing the first match.
    per_name: dict[str, int] = {}
    for c in DATA["calcs"]:
        href = f"/site/tools/{SLUGS[c['id']]}.html"
        esc = html.escape(c["name"], quote=False)
        for name in (esc, c["name"]):
            needle = f"<h3>{name}</h3>"
            n = per_name.get(name, 0)
            if n >= t.count(needle):
                continue
            pos = -1
            for _ in range(n + 1):
                pos = t.index(needle, pos + 1)
            t = t[:pos] + f'<h3><a href="{href}">{name}</a></h3>' + t[pos + len(needle):]
            per_name[name] = n + 1
            count += 1
            break
    p.write_text(t, encoding="utf-8")
    return count


def link_cards() -> bool:
    """Wrap each JS-rendered card title in a link to its own page.

    The anchor is styled to inherit the heading colour and drop its underline,
    so the card looks exactly as before. Idempotent.
    """
    p = SITE / "index.html"
    t = p.read_text(encoding="utf-8")
    slugs_js = "var SLUGS=" + json.dumps(
        {c["id"]: SLUGS[c["id"]] for c in DATA["calcs"]}, separators=(",", ":")) \
        + ";function CARD_SLUG(e){return SLUGS[e.id]||''}"
    if "var SLUGS={" not in t:
        marker = "function cardHTML("
        if marker not in t:
            return False
        t = t.replace(marker, slugs_js + marker, 1)
    old = "<h3>'+e.name+'</h3>"
    new = ("<h3><a class=\"tool-link\" href=\"/'"
           "+CARD_SLUG(e)+'\">'+e.name+'</a></h3>")
    if old in t:
        t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    return new in t


def write_sitemap() -> int:
    pages = [
        (f"{BASE}/", "daily", "1.0"),
        (f"{BASE}/site/blog.html", "weekly", "0.8"),
        (f"{BASE}/site/news.html", "daily", "0.8"),
        (f"{BASE}/site/about.html", "monthly", "0.6"),
        (f"{BASE}/site/contact.html", "monthly", "0.6"),
        # The product landing page. It lives in its own directory, so the
        # blog-/news- globs below cannot find it; without this line it would be
        # served but never crawled, which is the same defect the news pages had.
        (f"{BASE}/site/digital-products/indian-business-financial-model.html",
         "monthly", "0.8"),
        (f"{BASE}/site/refund-policy.html", "yearly", "0.3"),
    ]
    for c in DATA["calcs"]:
        pages.append((f"{BASE}/site/tools/{SLUGS[c['id']]}.html", "monthly", "0.7"))
    for b in sorted(SITE.glob("blog-*.html")):
        pages.append((f"{BASE}/site/{b.name}", "monthly", "0.7"))
    # News pages belong in the sitemap too. They were missing until 2026-10-23,
    # so Google had no crawl path to them at all - nine URLs, including the
    # /news index, simply did not exist as far as the sitemap was concerned.
    for n in sorted(SITE.glob("news-*.html")):
        pages.append((f"{BASE}/site/{n.name}", "weekly", "0.6"))
    for extra in ("privacy-policy", "terms-and-conditions", "disclaimer"):
        pages.append((f"{BASE}/site/{extra}.html", "yearly", "0.3"))

    # This step runs near the top of rebuild.sh, but add_pwa, add_pagination,
    # fix_static_seo and add_site_verification all rewrite the pages afterwards.
    # A hash taken here is therefore a hash of a half-finished page, and it
    # never matches the file that actually ships - so stamping lastmod from it
    # re-dated all 178 URLs "today" on every run, which is the signal Google
    # discounts. Write a fixed placeholder instead; lastmod_stamp.py runs last
    # and replaces it with the real per-page date.
    stamp = "1970-01-01"
    seen, urls = set(), []
    for loc, cf, pr in pages:
        if loc in seen:
            continue
        seen.add(loc)
        urls.append(
            f"  <url><loc>{loc}</loc><lastmod>{stamp}</lastmod>"
            f"<changefreq>{cf}</changefreq><priority>{pr}</priority></url>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n</urlset>\n"
    )
    (ROOT / "public" / "sitemap.xml").write_text(xml, encoding="utf-8")
    return len(urls)


if __name__ == "__main__":
    linked = link_catalogue()
    cards = link_cards()
    n = write_sitemap()
    print(f"catalogue entries linked: {linked}/100")
    print(f"JS card links wired: {cards}")
    print(f"sitemap urls written: {n}")
