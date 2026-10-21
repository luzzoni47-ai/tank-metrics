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
2. `tools/news.json` — copy an existing entry for the exact field list.
3. `tools/gen_news.py` — the generator that renders the pages and the pane.

## Task, in order
1. Research ONE current story with web search. The desk exists to pull in
   traffic from whatever is being talked about today, so the topic must be
   current, not evergreen. Look at:
   - Indian startup funding rounds from the last few days
   - Shark Tank India and Shark Tank USA episodes
   - GST and tax rule changes
   - anything a small-business owner would search for this week
   US funding news counts too when it says something about India.
   Do not repeat a story already in `tools/news.json`.

2. Append ONE object to `items` in `tools/news.json`. Copy an existing entry for
   the exact field list:
   `slug, title, dek, category, date, date_display, source_name, source_url,
   cta, related, body_en, body_hinglish`.
   - Write for a reader who runs a shop or is building a startup. Explain the
     numbers in the story with arithmetic, and end with what it means for them.
   - Use ROUND numbers in every example (10,000 / 6,000 / 60%), never odd
     figures like 580 or 7,180.
   - Never invent a fact, figure or quote — use only what the sources say, and
     put the source name and URL in `source_name` / `source_url`.
   - `title` must be **60 characters or fewer on its own** (the page renders it
     as "<title> | Tank Metrics", and anything past 60 gets truncated in the
     search result). `dek` must be **150-158 characters**.
   - `body_en` and `body_hinglish` must have the same number of `<h2>`/`<h3>`
     headings, at least 400 English words, and the Hinglish block must be roman
     script with zero Devanagari.
   - Point `cta` at the calculator the story is really about, and add one or two
     `related` guides.
   - Keep the newest story first in the list, so it shows up first on /news.

3. Run `python3 tools/gen_news.py`. It refreshes the news pages, the /news
   index, the `id="newsGrid"` pane on `/blog`, the sitemap, `llms.txt` and
   `tools/url-map.json`. Do not edit those by hand. If it reports a legacy
   `<section class="news-strip">` it will migrate it — that is expected.

4. Run the pipeline and the Python tests. All must pass before continuing:
   `python3 tools/clean_urls.py`
   `python3 tools/test_news.py`
   `python3 tools/test_blog.py`
   `python3 tools/test_layout.py`
   `python3 tools/test_blog_tabs.py`
   `python3 tools/test_contact_form.py`
   `python3 tools/seo_monitor.py .` - must report 0 problems. This is the guard
   that catches an over-long title or description, a missing canonical, or
   missing og:title/og:description on the new story. Fix and re-run until clean.
   Fix any failure and re-run. Never commit a red suite.
   `python3 tools/sync_gsc_list.py` - regenerates `tools/gsc_submit_list.txt`
   from the sitemap, so the new URL is included without hand-editing.
   Do NOT run `pnpm install`, `npm install` or `next build`, and do NOT run
   `tools/dom_smoke_tools.js`. They need a full dependency tree, they take
   longer than this run is allowed, and none of them is needed to publish a
   story — Vercel builds the site on its own servers.

5. Commit and push to `main` with `GITHUB_PERSONAL_ACCESS_TOKEN`
   (plain `GITHUB_TOKEN` is read-only and returns 403). If the push is
   rejected, `git pull --rebase origin main` first, then push again.

6. Deploy to Vercel. A push to `main` does NOT trigger a Vercel build, so the
   deploy must be run by hand:
   - Write `.vercel/project.json` =
     {"projectId":"prj_Y6MHqnmDyyD5U239ecqEMbrxh4ei",
      "orgId":"team_TXJMGXfZ9VZ9ZemmkKmoOuYw"} — without it the CLI fails with
     "User not found", because the token cannot read the team.
   - `npx vercel deploy --prod --yes --token "$VERCEL_TOKEN"`
   - The custom domain stays on the old deployment. Move it through the REST API:
     POST https://api.vercel.com/v2/deployments/<new_dpl_id>/aliases?teamId=team_TXJMGXfZ9VZ9ZemmkKmoOuYw
     with body {"alias":"tankmetrics.in"}.

7. Submit the new URL to the search engines. Google Search Console needs a
   Google login the agent does not have, but IndexNow does not:
   `python3 tools/indexnow_submit.py /<slug>`
   It should print `HTTP 200 accepted` or `202`. A 403 means the key file
   `https://tankmetrics.in/<key>.txt` is not live yet - deploy first, then retry.

8. Verify `https://tankmetrics.in/<slug>` returns 200 and contains
   `data-lang="en"` and `data-lang="hinglish"`, and that `https://tankmetrics.in/news`
   lists the new story first.
   Then run `python3 tools/seo_monitor.py https://tankmetrics.in` - it must
   report 0 problems across the whole live site.

9. Check the security headers on https://tankmetrics.in/ (CSP, X-Frame-Options,
   X-Content-Type-Options, Referrer-Policy, Permissions-Policy). If any are
   missing, add them in `next.config.mjs` and redeploy.

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
