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
2. Nothing else. Do NOT read the existing `public/site/blog-*.html` posts: they
   are ~175 KB between them and their shell is already baked into the scaffolder
   you are about to run. Reading them was most of what pushed this run past its
   30-minute budget. Read only a file the step below tells you to.

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

2. Write the page with the scaffolder — do NOT hand-write HTML. The shell
   (doctype, head, footer, language toggle) is identical on every post, so
   `tools/new_blog_post.py` stamps it from an existing post. You supply only the
   article body and the CTA target.

   a. Write the English article to a temp file, e.g. `/tmp/en.html`: HTML
      fragment only, starting with `<p>` — no `<html>`, no `<head>`, no
      `.main`, no `.page-hero`, no footer, no CTA (the scaffolder adds the CTA).
      Use `<h2>` for sections, `<ul>`/`<ol>` for lists. Worked examples stay
      under ₹10,000, reconcile with each other, and use ROUND numbers
      (10,000 / 6,000 / 60%), never odd figures like 580 or 7,180.
   b. Write the Hindi source to `/tmp/hi.html` the same way: body only, starting
      with the intro paragraphs, NEVER with the post title.
   c. Run the scaffolder:

      ```
      python3 tools/new_blog_post.py \
        --slug <slug> --title "<headline without the brand>" \
        --desc "<meta description>" --cat "<category>" \
        --accent "#RRGGBB" --hero "<one-line hero sentence>" \
        --cta-card <calculator card id, e.g. importduty> \
        --en /tmp/en.html --hi /tmp/hi.html
      ```

   It refuses to write a page that breaks the rules, so fix what it complains
   about instead of working around it:
   - `--title` is the headline WITHOUT " | Tank Metrics"; the full `<title>`
     must be **60 characters or fewer including " | Tank Metrics"**. Shorten the
     wording to fit — never drop the brand suffix.
   - `--desc` must be **150-158 characters**.
   - `--cta-card` is the id after `card_` on the home page, e.g. the Import Duty
     calculator is `importduty`. A wrong id gives a CTA that jumps nowhere.
   It writes `public/site/blog-<slug>.html`, `tools/hindi/blog-<slug>.hi.html`
   and the card in `public/site/blog.html` in one go.

3. Generate the Hinglish block:
   `python3 tools/hinglish.py --rebuild`. It discovers every post from the
   `tools/hindi/` sources, so there is no list to update. The block must contain
   zero Devanagari and exactly the same number of headings as the English block.

4. The blog card is already added by the scaffolder in step 2 — do not add a
   second one. Just confirm it landed inside the `id="paneGuides"` grid and
   that you did not touch the `id="paneNews"` pane.

   Also add an explicit entry for the new post at the top of the mapping dict in
   `tools/wire_blog_tools.py`: `"blog-<slug>": ["<calc-slug>", "<calc-slug>"]`.
   Without it that script guesses the calculators from the post title, and the
   guess is often wrong — "Import Duty" once matched **Stamp Duty** and
   **Average Order Value**, and wrote back-links from both to the new guide.
   List the one or two calculators the guide is really about.

5. Publish it: `tools/publish_guide.sh <slug>`. That one command runs the rest of
   this runbook for you, in the one order that works — `wire_blog_tools.py`,
   the whole `rebuild.sh` chain (which is what puts the new post in
   `public/sitemap.xml`), the blog schema, the social tags, every test, the
   commit and push, the Vercel deploy, the IndexNow announce and a live check.
   Do NOT run the pipeline commands, the tests, `deploy.sh` or
   `indexnow_submit.py` one by one; the script does all of them and stops before
   deploying if any test fails or the post is missing from the sitemap. If it
   reports a failure, fix it and run it again. Never commit a red suite.

   Do NOT run `pnpm install`, `npm install` or `next build`, and do NOT run
   `tools/dom_smoke_tools.js`. They need a full dependency tree, they take
   longer than this run is allowed, and none of them is needed to publish a
   post — Vercel builds the site on its own servers.

6. Verify what shipped: `https://tankmetrics.in/<slug>` returns 200 and contains
   `data-lang="en"` and `data-lang="hinglish"`, and
   `https://tankmetrics.in/blog` shows the new card in the Guides tab.
   Then run `python3 tools/seo_monitor.py https://tankmetrics.in` - it must
   report 0 problems across the whole live site.

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
