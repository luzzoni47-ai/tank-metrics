# Tank Metrics — tankmetrics.in

Free business and money calculators for India. 101 calculators and 123 pages,
served as static HTML from `public/site/` through a thin Next.js shell that owns
the routing, the security headers and the 404 page.

## Layout

- `public/site/*.html` — the site of record: home, guides, blog, legal, tools.
- `public/site/tools/*.html` — one page per calculator.
- `app/` — Next.js App Router. It serves no content of its own; the rewrites in
  `next.config.mjs` send every real path to a static file. It exists for the
  routing table, the security headers and `app/not-found.tsx`.
- `tools/` — every generator and test. These own the HTML; do not hand-edit
  generated pages.

## Build and deploy

```bash
corepack pnpm build      # writes .next/ from app/ + public/
npx vercel --prod        # deploy (VERCEL_TOKEN)
```

`next start` snapshots `public/` at boot, so after regenerating HTML you must
rebuild `.next/` before the change is visible locally.

## Regenerate

```bash
python3 tools/gen_tool_pages.py    # tool pages from tools/calcs.json
python3 tools/gen_news.py          # /blog and /news listings
python3 tools/clean_urls.py        # the clean-URL table + sitemap
python3 tools/make_favicon.py      # favicon.svg/.png/.ico, PWA icons, manifest
python3 tools/fix_blog_meta.py     # Article/BreadcrumbList + og: tags
python3 tools/fix_static_seo.py    # breadcrumbs + og: tags on static pages
python3 tools/wire_crawl_graph.py  # internal links between related pages
```

`tools/url-map.json` is the single source of truth for the public URL shape.
`next.config.mjs` reads it for rewrites, `tools/clean_urls.py` writes it, and
the sitemap is derived from it, so the three can never drift.

## Tests

Standalone scripts, no pytest. Each exits non-zero and prints the failures.

```bash
for t in tools/test_*.py; do python3 "$t"; done
python3 tools/seo_monitor.py --local   # built files: titles, descriptions, schema
```

`tools/test_layout.py` starts its own `http.server` and chromium, so it needs no
running server. It guards the header stripe, image hosts, the mobile close
button, the favicon size (Google needs a side that is a multiple of 48px) and
the web app manifest.

## Daily automations (Asia/Kolkata)

Two OpenHands cron jobs write and deploy a news post and a guide each day. Their
prompts live in `tools/automation/` and state the length limits, the schema step
and the checks they must run.
