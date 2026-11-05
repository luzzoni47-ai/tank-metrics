# Tank Metrics — daily internal-links + CTR run

This run owns the **on-page linking and click-through** work that the publishing
runs (`daily guide`, `daily news`) leave behind. It does NOT write a blog post
and does NOT add a news story — `daily guide` and `daily news` already publish
one of each every day. Writing a third post here is exactly what made the old
`daily blog + SEO` run time out at 30 minutes. Do not do it.

## Why this run exists

Content is published daily, but a new page only earns impressions if it is
reachable from indexed pages and if its title matches what people search. Two
real, measured jobs:

1. **Internal links** - a page with no inbound link from an indexed page is
   "URL unknown to Google". Every new guide and news story needs 2-3 inbound
   links, and old pages need their links kept alive.
2. **CTR** - a page ranking on position 1-10 with zero clicks has a title that
   does not match the query. `tools/gsc.py pages` surfaces these; the fix is the
   `seo_title` field in `tools/calcs.json` (titles <= 60 chars, descriptions
   <= 155).

## Time budget
The run is killed at 30 minutes. Steps 1-2 are the value; do them first.

## Read first
1. `AGENTS.md` — build rules and gotchas.
2. Nothing else. Do not read the blog posts or `tools/news.json`.

## Task, in order

### 1. Find the pages that need links and clicks

```
python3 tools/gsc.py pages 28        # per-page clicks/imp/CTR/position
python3 tools/gsc_triage.py          # which pages are not-seen / discovered
```

- **not-seen / discovered** pages: they need inbound internal links.
- **position <= 10 with 0 clicks and >= 10 impressions**: title/description fix.

### 2. Wire internal links for the newest pages

The two newest published pages (a guide and a news story from today's runs) must
each be linked from at least two already-indexed pages. Use the existing
machinery — do not hand-edit HTML:

```
python3 tools/wire_blog_tools.py
python3 tools/wire_crawl_graph.py
python3 tools/test_interlinks.py     # must pass: no dead internal links
```

`wire_blog_tools.py` has a title-keyword matcher that guesses the calculators a
post is about, and the guess is often wrong — "Import Duty" once matched **Stamp
Duty** and **Average Order Value**. If the newest post is not already mapped,
add an explicit entry at the top of its mapping dict: `"blog-<slug>": ["<calc-slug>"]`.

### 3. Fix the worst CTR titles

From `gsc.py pages`, take the pages at position <= 10 with the most impressions
and 0 clicks. Then read the exact queries that page ranks for:

```
python3 tools/gsc.py page-queries <path> 28
```

For each page, set/repair its title so it uses the words of the query it ranks
for. Titles <= 60 chars including " | Tank Metrics", descriptions <= 155. Do at
most 3 per run; do not retitle a page sitting at position > 30 (that is a
ranking gap, retitling does nothing).

There are two title sources, and the biggest opportunities are usually the
second:

- **calculator pages** — the `seo_title` field in `tools/calcs.json`
  (`gen_tool_pages.py`'s `title_for()` already prefers it). Calc **ids are not
  slugs** — look the id up in `tools/calcs.json`.
- **keyword-targeted pages** — the `title` field in `tools/keyword_pages.json`,
  rendered by `gen_keyword_pages.py`. Keep the page's `h1` in step with the new
  title, then update the matching card's `<h2>`/`<p>` in `public/site/blog.html`
  so the listing does not advertise the old wording.

### 4. Watch for anyone writing about the brand

```
python3 tools/brand_monitor.py
```

Sir's standing ask: if anyone writes "Tank Metrics" or "tankmetrics" anywhere, he
wants to see it. This scans Hacker News, Bing, Google News and DuckDuckGo - all
free, none needing a login - and writes `tools/reports/brand-latest.md`. Read the
report before reporting it: the classifier splits hits into **about us**,
**others linking to us**, and **namesakes** (tankmetrics.com, BattleMetrics and a
fuel-logging Chrome extension are NOT us). Never tell Sir a namesake is a mention.
If only namesakes were found, say plainly that nobody wrote about the brand.

### 5. Rebuild, test, publish

```
python3 tools/gen_tool_pages.py
python3 tools/lastmod_stamp.py       # MUST follow wire_crawl_graph: it writes 1970-01-01 placeholders
python3 tools/test_interlinks.py
python3 tools/test_dedup.py
tools/deploy.sh -m "Daily links + CTR run <date>: <n> pages linked, <n> titles fixed"
```

`wire_crawl_graph.py` (step 2) rewrites the whole sitemap with a `1970-01-01`
placeholder lastmod, and `lastmod_stamp.py` is the only thing that turns those
into honest dates. Skip it and every URL ships dated 1970, which makes Google
discount the entire sitemap — the one indexing lever this repo owns. It is a
no-op when nothing changed, so always run it.

Run the full offline suite (`python3 tools/test_*.py`) before deploying; it
takes ~10 seconds. `test_clean_urls.py` needs a running server — skip it.

### 6. Report

```
Links + CTR run <date>
  newest pages linked: <guide-slug>, <news-slug> (from N indexed pages)
  CTR titles fixed: <calc ids>
  brand mentions: N about us, M citing us, K namesakes (tools/reports/brand-latest.md)
  dead internal links: 0 (test_interlinks passed)
```

## Guardrails
- Never write a blog post or a news story here — other runs own those.
- Never post anywhere, never send an email, never submit a listing.
- Never invent keyword data. Use `gsc.py` / `keyword_radar.py` output.
- Never commit `.vercel/`, `node_modules/`, `tools/__pycache__/`, or any token.
- If a required secret is missing, stop and report it instead of guessing.
