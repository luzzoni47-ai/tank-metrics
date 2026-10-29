# Tank Metrics — daily news runbook

You publish ONE news story on the Tank Metrics website (tankmetrics.in): free
Indian business calculators plus a small blog and a news desk. This run writes a
news story only. A separate run handles the guide (the evergreen blog post) — do
not touch `public/site/blog-*.html` or `tools/hindi/` here.

## Time budget
The run is killed at 30 minutes. Work briskly. The web research in step 1 is the
part that eats the clock, so do it first and keep it to a handful of searches.

## Read first
1. `AGENTS.md` — build rules and gotchas. (`.openhands/` is gitignored, so no
   memory file ships in this clone.)
2. Nothing else. Do NOT read `tools/news.json` (91 KB) or `tools/gen_news.py`
   (18 KB): the story shape is enforced by the adder you are about to run, and
   reading them was most of what pushed this run past its 30-minute budget.

## Task, in order
1. Research ONE current story with web search. The desk exists to pull in
   traffic from whatever is being talked about today, so the topic must be
   current, not evergreen. If you are unsure which angle to take, this shows
   what the audience is typing into Google right now:

   ```
   python3 tools/keyword_radar.py --top 30
   ```

   Use it only to pick the angle, not the facts — the story itself must still
   come from today's sources. Look at:
   - Indian startup funding rounds from the last few days
   - Shark Tank India and Shark Tank USA episodes
   - GST and tax rule changes
   - anything a small-business owner would search for this week
   US funding news counts too when it says something about India.
   Do not repeat a story already in `tools/news.json`.

2. Write the story as a small JSON file, e.g. `/tmp/story.json`, and let the
   adder place it. Do NOT edit `tools/news.json` by hand — it is 91 KB and easy
   to corrupt. The file is one object with exactly these fields:

   ```
   {"slug": "<lowercase-words-joined-by-dashes>",
    "title": "<60 chars or fewer on its own>",
    "dek": "<150-158 characters>",
    "category": "<e.g. Small Business>",
    "date": "<ISO, e.g. 2026-10-26>",
    "date_display": "<e.g. October 26, 2026>",
    "source_name": "<publication>",
    "source_url": "<the real article URL>",
    "cta": {"text": "...", "href": "/<calculator-slug>", "label": "Open the ... Calculator"},
    "related": [{"slug": "<guide-slug>", "title": "<guide title>"}],
    "body_en": ["<p>...</p>", "<h2>...</h2>", "..."],
    "body_hinglish": ["<p>...</p>", "<h2>...</h2>", "..."]}
   ```

   Then run:

   ```
   python3 tools/new_news_story.py --story /tmp/story.json
   ```

   It validates and refuses to add a bad story, so fix what it complains about:
   - `title` must be **60 characters or fewer on its own** (the page renders it
     as "<title> | Tank Metrics", and anything past 60 is truncated in search).
   - `dek` must be **150-158 characters**.
   - `body_en` and `body_hinglish` must have the same number of `<h2>`/`<h3>`
     headings, `body_en` must be at least 400 words, and `body_hinglish` must be
     roman script with zero Devanagari.
   - `source_url` must be the real article URL, and `cta.href` a site path.
   - Write for a reader who runs a shop or is building a startup. Explain the
     numbers with arithmetic and end with what it means for them. Use ROUND
     numbers in every example (10,000 / 6,000 / 60%), never odd figures like 580
     or 7,180. Never invent a fact, figure or quote.
   It keeps the newest story first automatically.

3. Run `python3 tools/gen_news.py`. It refreshes the news pages, the /news
   index, the `id="newsGrid"` pane on `/blog`, the sitemap, `llms.txt` and
   `tools/url-map.json`, and validates the story as it goes. Do not edit those
   by hand. If it reports a legacy `<section class="news-strip">` it will
   migrate it — that is expected.

4. Publish it: `tools/publish_news.sh <slug>`. That one command runs the rest of
   this runbook for you — the pipeline, the tests, the commit and push, the
   deploy, and the IndexNow announce. Do NOT run the pipeline commands, the
   tests, `deploy.sh` or `indexnow_submit.py` one by one; the script does all of
   them and stops before deploying if any test fails or the story is missing
   from the sitemap. If it reports a failure, fix it and run it again.

5. Verify what shipped: `https://tankmetrics.in/<slug>` returns 200 and contains
   `data-lang="en"` and `data-lang="hinglish"`, and `https://tankmetrics.in/news`
   lists the new story first. Then run
   `python3 tools/seo_monitor.py https://tankmetrics.in` - it must report 0
   problems across the whole live site.

## Guardrails
- Never commit `.vercel/`, `node_modules/`, `tools/__pycache__/`, or any token.
- Never add `vercel` to `package.json` — Vercel installs with
  `pnpm install --frozen-lockfile` and the build aborts.
- Do not edit the guide posts, `tools/hindi/` or the `id="paneGuides"` pane.
- Never invent a source. If you cannot find a real story with a real URL, stop
  and report it instead of publishing.
- If a required secret is missing, stop and report it instead of guessing.

## Report
One short summary: the new story URL, the tests that ran and their result, the
deployment URL, and anything that needs a human decision.
