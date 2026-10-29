# Tank Metrics — daily keyword-page runbook

You publish FIVE new keyword-targeted calculator pages on tankmetrics.in, one
batch per day, until the 30-page plan in `tools/keyword_pages.json` is done.
Day 1 (keywords 1-5) shipped on 2026-10-29. This run does the next unfinished
day. Do not touch `tools/news.json` or the existing guides.

## Time budget
Killed at 30 minutes. Work briskly. If you are short on time, commit and push
what you have rather than leaving it uncommitted.

## Read first
1. `AGENTS.md` — build rules and gotchas.
2. `tools/keyword_pages.json` — the plan (`days`) and the pages already written.
3. `tools/gen_keyword_pages.py` — the renderer; do not change its shape.

## The one thing to understand first

These pages must NOT be thin. `tools/content_uniqueness.py` shows 81 of 101
calculator pages are near-duplicates, and that is the reason only a handful are
indexed in Google. A new page earns its place only if the copy is specific to
its own keyword. If a paragraph would read fine on a sibling page, rewrite it.

Every page must satisfy, in order:

- `<title>` <= 65 chars, meta description 50-165 chars (the generator asserts this).
- English article of ~700 words: hook, What is [keyword], Formula, a worked
  example with a TABLE, How to use (3 steps), Why India is different (US vs
  India), Common mistakes.
- A Hinglish twin with the SAME headings (romanised, ZERO Devanagari).
- A working calculator: real `inputs` and a `compute` function that uses the
  shared helpers `val`, `inr`, `pct`, `num` (see calcs.json "helpers").
- ₹ Lakhs and ₹ Crores only. Never a `$`, never "million" in the copy.
- A Shark Tank India example where the keyword allows it.
- 3 FAQs, and the CTA text exactly:
  "Calculate your [keyword] now on TankMetrics.in - 100% free, made for Indian
  founders in ₹ Lakhs & Crores."

## Task, in order

1. Pick the day. In `tools/keyword_pages.json`, take the first entry in `days`
   whose `nums` are not all present in `pages[].num`. Append one page object per
   number to `pages`, matching the existing entries' keys exactly.

2. Verify the related links resolve. Every `related` URL must exist in
   `tools/url-map.json` or be `/`. Check before writing:

   ```
   python3 - <<'PY'
   import json
   m = json.load(open('tools/url-map.json'))
   d = json.load(open('tools/keyword_pages.json'))
   for pg in d['pages']:
       for u, n in pg['related']:
           if u != '/' and u not in m:
               print('BAD', pg['num'], u)
   PY
   ```

3. Generate and rebuild:

   ```
   python3 tools/gen_keyword_pages.py
   python3 tools/rebuild.sh
   ```

   `rebuild.sh` already runs `gen_keyword_pages.py` FIRST (so the PWA block and
   the "Run the numbers" section survive) and runs `add_blog_schema.py`. Do not
   reorder it. Do not run `npm install` or `next build`.

4. Run the tests. All must pass:

   ```
   python3 tools/test_sitemap.py
   python3 tools/test_interlinks.py
   python3 tools/test_blog.py
   python3 tools/seo_monitor.py --local      # must be 0 problems
   ```

5. Commit and push with `GITHUB_PERSONAL_ACCESS_TOKEN` (plain `GITHUB_TOKEN` is
   read-only and returns 403). If the push is rejected, `git pull --rebase
   origin main` first, rebuild, then push again.

6. Deploy and announce. Pass every new clean path so IndexNow hears about it:

   ```
   tools/deploy.sh -m "Day N keyword batch" \
     /keyword-<slug-1> /keyword-<slug-2> /keyword-<slug-3> /keyword-<slug-4> /keyword-<slug-5>
   ```

   The deploy script points the domain at the new build and submits the paths
   to IndexNow after the site is live. It needs `VERCEL_TOKEN`.

7. Verify live: each `https://tankmetrics.in/keyword-<slug>` returns 200, carries
   FAQPage + WebApplication + Article + BreadcrumbList JSON-LD, one `<h1>`, and
   `data-lang="hinglish"`. Then `python3 tools/seo_monitor.py https://tankmetrics.in`
   must report 0 problems across the whole live site.

## Guardrails
- Never invent keyword data or a Shark Tank figure. If unsure of a deal's
  numbers, use a generic worked example instead of a wrong real one.
- Never use `$` or "million". ₹ Lakhs and ₹ Crores only.
- Do not change the Day-1 pages or the existing guides.
- Never commit `.vercel/`, `node_modules/`, `tools/__pycache__/`, or a token.
- If a required secret is missing, stop and report it instead of guessing.

## Report
One short summary: the day and keywords shipped, the new URLs, the tests that
ran and their result, the deployment URL, and anything needing a human decision.
