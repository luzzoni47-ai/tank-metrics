#!/usr/bin/env bash
# Regenerate every derived page in the one order that works.
#
# The order matters and getting it wrong is silent. `gen_tool_pages.py` and
# `wire_crawl_graph.py` both emit raw /site/*.html links on purpose, and
# `clean_urls.py` is the single place that turns those into clean public URLs.
# Run clean_urls before the two of them and it rewrites nothing: the canonicals
# stay /site/tools/x.html, the sitemap lists 116 URLs instead of 125, and the
# news pages drop out entirely. That happened on 2026-10-23. One script with
# the order baked in is the fix.
#
# `add_pwa.py` is last because it must see the final files - the PWA shell and
# the nav drawer go into the pages that clean_urls has already rewritten.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Drop stale bytecode first. Python decides a .pyc is current by comparing the
# source's mtime and size, and an edit that keeps the same length within the
# same second defeats both. On 2026-10-24 a landing_style.py edit changed
# `padding:52px` to `padding:96px` - same length, same second - so Python kept
# serving the old rule from __pycache__ and the mobile hero stayed clipped while
# the source looked correct. Cheap to clear, and it removes the whole class of
# "the fix is in the file but not in the page".
find tools -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true

# The keyword pages are written FIRST. gen_tool_pages.py re-applies the PWA
# block and wire_blog_tools.py adds the "Run the numbers" section to every
# blog-*.html; running the keyword generator after them would overwrite those
# sections on the keyword pages, because it rewrites the whole file.
echo "==> gen_keyword_pages (keyword-targeted calculator pages)"
python3 tools/gen_keyword_pages.py
echo "==> gen_tool_pages"
python3 tools/gen_tool_pages.py
echo "==> validate_guides (reject weak per-calculator copy before it ships)"
python3 tools/validate_guides.py
echo "==> dedup_worklist (which calculators still share the category template)"
python3 tools/dedup_worklist.py --quiet
echo "==> gen_news"
python3 tools/gen_news.py
echo "==> gen_products_page (after gen_news, so news footers get the link)"
python3 tools/gen_products_page.py
echo "==> gen_landing_page (the product landing page)"
python3 tools/gen_landing_page.py
echo "==> wire_crawl_graph (writes the sitemap, incl. news)"
python3 tools/wire_crawl_graph.py
echo "==> clean_urls (the only place that decides the public URL shape)"
python3 tools/clean_urls.py
echo "==> gen_llms (the AI-answer file, from url-map)"
python3 tools/gen_llms.py
echo "==> make_favicon"
python3 tools/make_favicon.py
echo "==> fix_blog_meta"
python3 tools/fix_blog_meta.py
echo "==> add_blog_schema (Article + BreadcrumbList on guides, incl. keyword pages)"
python3 tools/add_blog_schema.py
echo "==> fix_static_seo"
python3 tools/fix_static_seo.py
echo "==> add_pwa"
python3 tools/add_pwa.py
echo "==> gen_updates"
python3 tools/gen_updates.py

echo "==> seo_monitor --local"
python3 tools/seo_monitor.py --local
