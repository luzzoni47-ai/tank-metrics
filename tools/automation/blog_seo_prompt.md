# Tank Metrics — blog + SEO automation

You maintain the Tank Metrics website (tankmetrics.in): free Indian business
calculators plus a small blog. Work only inside the cloned repo.

## Read first
1. `AGENTS.md` and `.openhands/memory/MEMORY.md` — build rules and gotchas.
2. The existing posts `public/site/blog-*.html` — copy their structure exactly.

## Task, in order
1. Pick ONE new topic an Indian small-business owner or first-time founder would
   search for (cost, tax, pricing, cash flow, margins, GST). Do not repeat a
   topic the blog already covers.
2. Write `public/site/blog-<slug>.html` with the same shell as the existing posts:
   - `<head>`: title, meta description, canonical `https://tankmetrics.in/<slug>`,
     og tags, GA4 tag `G-MHZ0V6HFC6`.
   - One `<h1>` in the page header. `.post-meta` with tag, date and the
     `#langToggle` button (badge `H`, label `Hinglish`, title "Read in Hinglish").
   - One `.post-lang[data-lang="en"]` block holding the English article.
   - Worked examples stay under ₹10,000 and must reconcile with each other.
3. Write the Hindi source `tools/hindi/blog-<slug>.hi.html` (body only, starting
   with the intro paragraphs — NEVER with the post title), then run
   `python3 tools/hinglish.py --rebuild` to generate the Hinglish block.
   That block must contain zero Devanagari and exactly the same number of
   headings as the English block.
4. Add a card for the new post to `public/site/blog.html`, matching the existing
   cards and keeping the grid `repeat(2,minmax(0,1fr))`.
5. Add ONE news story to the news desk (`tools/news.json`), then run
   `python3 tools/gen_news.py`. The desk exists to pull in traffic from whatever
   is being talked about today, so the topic must be current, not evergreen.
   - Research first with web search. Look at Indian startup funding rounds from
     the last few days, Shark Tank India and Shark Tank USA episodes, GST and
     tax rule changes, and anything a small-business owner would search for
     this week. US funding news counts too when it says something about India.
   - Write for a reader who runs a shop or is building a startup. Explain the
     numbers in the story with arithmetic, and end with what it means for them.
     Never invent a fact, figure or quote — use only what the sources say, and
     put the source name and URL in `source_name` / `source_url`.
   - Append one object to `items` in `tools/news.json`. Copy an existing entry
     for the exact field list. `body_en` and `body_hinglish` must have the same
     number of `<h2>`/`<h3>` headings, at least 400 English words, and the
     Hinglish block must be roman script with zero Devanagari.
   - Point `cta` at the calculator the story is really about, and add one or two
     `related` guides.
   - `gen_news.py` also refreshes the news strip on the home page and the blog,
     the sitemap, `llms.txt` and `tools/url-map.json`. Do not edit those by hand.
6. Run the pipeline and the Python tests. All must pass before continuing:
   `python3 tools/wire_blog_tools.py`
   `python3 tools/clean_urls.py`
   `python3 tools/test_blog.py`
   `python3 tools/test_news.py`
   `python3 tools/test_layout.py`
   `python3 tools/test_contact_form.py`
   Fix any failure and re-run. Never commit a red suite.
   Do NOT run `pnpm install`, `npm install` or `next build`, and do NOT run
   `tools/dom_smoke_tools.js`. They need a full dependency tree, they take
   longer than this run is allowed, and none of them is needed to publish a
   blog post — Vercel builds the site on its own servers.
7. Commit and push to `main` with `GITHUB_PERSONAL_ACCESS_TOKEN`
   (plain `GITHUB_TOKEN` is read-only and returns 403). If the push is
   rejected, `git pull --rebase origin main` first, then push again.
8. Deploy to Vercel: `tools/deploy.sh /<slug>` (pass every new path). It builds,
   ships, waits for READY, points tankmetrics.in and www at the new deployment,
   checks the live paths, and announces each path through IndexNow afterwards -
   so the submit step below is already covered when you pass the slug.
   A push to `main` does NOT trigger a Vercel build: the project's stored
   link.repoId is stale, so Vercel never matches the push. That is why the
   deploy is explicit.
9. Verify `https://tankmetrics.in/<blog-slug>` and
   `https://tankmetrics.in/<news-slug>` both return 200 and contain
   `data-lang="en"` and `data-lang="hinglish"`. Also confirm `/news` lists the
   new story.
10. Check the security headers on https://tankmetrics.in/ (CSP, X-Frame-Options,
   X-Content-Type-Options, Referrer-Policy, Permissions-Policy). If any are
   missing, add them in `next.config.mjs` and redeploy.

## Guardrails
- Never commit `.vercel/`, `node_modules/`, `tools/__pycache__/`, or any token.
- Never add `vercel` to `package.json` — Vercel installs with
  `pnpm install --frozen-lockfile` and the build aborts.
- Do not change the worked-example numbers in the existing four posts.
- If a required secret is missing, stop and report it instead of guessing.

## Report
One short summary: the new post URL, the tests that ran and their result, the
deployment URL, and anything that needs a human decision.

