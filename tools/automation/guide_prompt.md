# Tank Metrics — daily guide runbook

You publish ONE new guide (an evergreen blog post) on the Tank Metrics website
(tankmetrics.in): free Indian business calculators plus a small blog. This run
writes a guide only. A separate run handles the news desk — do not touch
`tools/news.json` here.

## Time budget
The run is killed at 30 minutes. Work briskly, do not re-read files you have
already seen, and do not run anything the guardrails forbid. If you are running
short on time, commit and push what you have rather than leaving it uncommitted.

## Read first
1. `AGENTS.md` — build rules and gotchas. (`.openhands/` is gitignored, so no
   memory file ships in this clone.)
2. The existing posts `public/site/blog-*.html` — copy their structure exactly.

## Task, in order
1. Pick ONE new topic an Indian small-business owner or first-time founder would
   search for (cost, tax, pricing, cash flow, margins, GST, unit economics).
   Start from real query data instead of a guess:

   ```
   python3 tools/keyword_radar.py --top 30
   ```

   That reads Google's autocomplete for this site's own subjects and prints the
   phrases people actually type, ranked. A `+` in front means the site has no
   page that answers the phrase yet — prefer those, because a guide that fills a
   real gap earns traffic; one that repeats a calculator you already have does
   not. If the radar fails (no network), fall back to picking by hand.

   Read the existing `blog-*.html` titles as well and do not repeat a topic the
   blog already covers. The guides are evergreen, so no web research is needed.

2. Write `public/site/blog-<slug>.html` with the same shell as the existing posts:
   - `<head>`: title, meta description, canonical `https://tankmetrics.in/<slug>`,
     og tags, GA4 tag `G-MHZ0V6HFC6`, the Google site verification meta, the
     favicon links and `/site/style.css`. Copy the head of an existing post and
     change only the title, description and canonical.
   - Length limits, because Google truncates past them and the search result
     starts to look broken: the `<title>` must be **60 characters or fewer
     including " | Tank Metrics"**, and the meta description must be **150-158
     characters**. Shorten the headline wording to fit — never drop the brand
     suffix to make room.
   - Body: tricolor bar, topbar, `.main > .page-hero` (tag `📖 Tank Metrics Blog`,
     one `<h1>`, one `<p>`), then `.page-wrap`.
   - `.post-meta` with the category tag, the date and the `#langToggle` button
     (badge `H`, label `Hinglish`, title "Read in Hinglish").
   - One `.post-lang[data-lang="en"]` block holding the English article.
   - Worked examples stay under ₹10,000 and must reconcile with each other.
   - Use ROUND numbers in every example (10,000 / 6,000 / 60%), never odd
     figures like 580 or 7,180.
   - End with a CTA linking to the calculator the guide is really about.

3. Write the Hindi source `tools/hindi/blog-<slug>.hi.html` (body only, starting
   with the intro paragraphs — NEVER with the post title), then run
   `python3 tools/hinglish.py --rebuild` to generate the Hinglish block.
   That block must contain zero Devanagari and exactly the same number of
   headings as the English block.

4. Add a card for the new post to `public/site/blog.html`, inside the
   `id="paneGuides"` grid, matching the existing cards: `<a class="blog-card"
   href="/<slug>" style="border-top-color:#RRGGBB">` with a `.cat` span, an
   `<h2>`, a `<p>` and a `.readmore` span. Keep the grid
   `repeat(2,minmax(0,1fr))` and do not touch the `id="paneNews"` pane.

5. Link the new post to the calculators that answer it, then run the pipeline
   and the Python tests. All must pass before continuing:
   `python3 tools/wire_blog_tools.py` - adds the "Run the numbers" section to
   the new post and a "Read the guide" back-link on the matching calculator
   pages. It picks the tools from the post title when there is no hand-written
   entry, so it always finds something. Run it BEFORE `clean_urls.py`.
   `python3 tools/wire_crawl_graph.py` - rebuilds `public/sitemap.xml` from the
   files on disk. `clean_urls.py` only rewrites URLs that are ALREADY in the
   sitemap, so a brand-new post is invisible to Google until this runs. Run it
   BEFORE `clean_urls.py` too.
   `python3 tools/clean_urls.py`
   `python3 tools/add_blog_schema.py`
   `python3 tools/test_blog.py`
   `python3 tools/test_news.py`
   `python3 tools/test_layout.py`
   `python3 tools/test_blog_tabs.py`
   `python3 tools/test_contact_form.py`
   `python3 tools/test_interlinks.py` - every blog post must link to real
   calculators and every internal link must resolve, not 404.
   `python3 tools/seo_monitor.py .` - must report 0 problems. This is the guard
   that catches an over-long title or description, a missing canonical, or
   missing og:title/og:description on the new post. Fix and re-run until clean.
   Fix any failure and re-run. Never commit a red suite.
   `python3 tools/sync_gsc_list.py` - regenerates `tools/gsc_submit_list.txt`
   from the sitemap, so the new URL is included without hand-editing.
   Do NOT run `pnpm install`, `npm install` or `next build`, and do NOT run
   `tools/dom_smoke_tools.js`. They need a full dependency tree, they take
   longer than this run is allowed, and none of them is needed to publish a
   post — Vercel builds the site on its own servers.

6. Commit and push to `main` with `GITHUB_PERSONAL_ACCESS_TOKEN`
   (plain `GITHUB_TOKEN` is read-only and returns 403). If the push is
   rejected, `git pull --rebase origin main` first, then push again.

7. Deploy to Vercel: `tools/deploy.sh /<slug>` (pass every new path). It pushes,
   ships, waits for READY, points tankmetrics.in and www at the new deployment,
   checks the live paths, and announces each path through IndexNow afterwards -
   so the submit step below is already covered when you pass the slug.
   Vercel builds the site from GitHub, so the script does NOT run a local
   `next build`; never run one yourself either.
   A push to `main` does NOT trigger a Vercel build: the project's stored
   link.repoId is stale, so Vercel never matches the push. That is why the
   deploy is explicit.

8. Submit the new URL to the search engines. Google Search Console needs a
   Google login the agent does not have, but IndexNow does not. A sweep already
   runs a few times a day and picks up anything the sitemap gained, so this step
   is the belt to that suspenders - it announces the page the moment it is live
   instead of waiting for the next sweep:
   `python3 tools/indexnow_submit.py /<slug>`
   It should print `HTTP 200 accepted` or `202`. A 403 means the key file
   `https://tankmetrics.in/<key>.txt` is not live yet - deploy first, then retry.

9. Verify `https://tankmetrics.in/<slug>` returns 200 and contains
   `data-lang="en"` and `data-lang="hinglish"`, and that
   `https://tankmetrics.in/blog` shows the new card in the Guides tab.
   Then run `python3 tools/seo_monitor.py https://tankmetrics.in` - it must
   report 0 problems across the whole live site.

10. Check the security headers on https://tankmetrics.in/ (CSP, X-Frame-Options,
   X-Content-Type-Options, Referrer-Policy, Permissions-Policy). If any are
   missing, add them in `next.config.mjs` and redeploy.

## Guardrails
- Never commit `.vercel/`, `node_modules/`, `tools/__pycache__/`, or any token.
- Never add `vercel` to `package.json` — Vercel installs with
  `pnpm install --frozen-lockfile` and the build aborts.
- Do not change the worked-example numbers in the existing posts.
- Do not edit `tools/news.json`, the news pane or the home page.
- If a required secret is missing, stop and report it instead of guessing.

## Report
One short summary: the new post URL, the tests that ran and their result, the
deployment URL, and anything that needs a human decision.
