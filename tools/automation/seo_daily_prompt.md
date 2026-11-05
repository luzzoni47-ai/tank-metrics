# Tank Metrics — daily SEO runbook (measure + fix only)

This run owns exactly these tools from Sir's 20-tool list: **Search Console,
PageSpeed, Yoast/Rank Math (title + canonical + schema), Ahrefs/SEMrush
(content-uniqueness proxy)**. The other tools belong to other automations - see
`tools/automation/TOOL_DIVISION.md`. Do NOT do Bing, backlink drafting, brand
monitoring or blog/news publishing here; those are separate runs and doing them
twice is what pushed this run past its 30-minute budget.

## The one thing to understand first

Most of the 20 tools cannot be driven by an agent (no login). Yoast, Rank Math,
Ahrefs and SEMrush are replaced by the two scripts below. An agent that claims
to have "run Ahrefs" is lying. Do not do that. This run measures with the real
free tools and fixes what is fixable in code.

## Time budget
The run is killed at 30 minutes. Do steps 1-2 first: they are the value. If you
are short on time, commit and push what you have rather than leaving it
uncommitted. Skip PageSpeed if it answers 429.

## Read first
1. `AGENTS.md` — build rules and gotchas.
2. `tools/content_uniqueness.json` from the last run, if it exists — this run
   writes the new one, and the diff is the progress report.

## Task, in order

### 1. Measure the site (deterministic, ~1 minute)

```
python3 tools/seo_monitor.py --local
python3 tools/content_uniqueness.py --top 12
```

`content_uniqueness.py` prints the share of calculator pages that are
near-duplicates of another page, and the median overlap. On 2026-10-22 that was
**94 of 101 pages, median 66%**. It is now near zero — keep it there. If the
number rose, that is the finding and the fix is step 2.

### 1b. Search Console (the run's best evidence)

OAuth is set up (`GSC_OAUTH_JSON`), so use it - it is Google's own verdict.

```
python3 tools/gsc_triage.py                   # every page, its state, its fix
python3 tools/gsc.py sitemaps                 # submitted vs indexed
python3 tools/gsc.py pages 28                 # per-page clicks/imp/CTR/position
```

`gsc_triage.py` inspects every sitemap URL (cached a week in
`tools/gsc_inspection.json`) and buckets each page indexed / not-seen /
discovered / crawled / canonical, with the one action that fixes that state.
`gsc.py pages` is the per-page view the query view hides - run it first, a
page-1 ranker with 0 clicks only shows up here.

Act on the two fixable buckets:
- **not-seen** (Google never saw the URL): add 2-3 internal links from indexed
  pages, re-submit the sitemap.
- **discovered / crawled** (seen, not indexed): unique per-tool copy - step 2.

Report the bucket counts and the worst pages in the summary.

### 2. Write real copy for the worst offenders (the actual indexing fix)

`gen_tool_pages.py` falls back to a shared per-CATEGORY template for any
calculator with no hand-written guide, so every calculator in a category renders
the same prose. Google does not index near-duplicates. That is the whole problem.

Pick the **2** calculators from the top of `content_uniqueness.py`'s "worst
pages" list (2, not 3 - keep the run inside its budget) and give each a real
guide entry in `tools/tool_guides.json` under `calcs`, keyed by the calculator id
(find the id in `tools/calcs.json`). Write:

- `what` — 2 paragraphs that only make sense for THIS calculator. Name the
  decision it settles. If the text would read fine on a sibling page, it is not
  specific enough and does not count as progress.
- `formula` — the actual arithmetic, with the variable names the tool uses.
- `mistakes` — 3 errors specific to this calculation.
- `when` — 3 situations where someone reaches for it.

Also add the Hinglish twin to `tools/tool_guides_hinglish.json` (same keys,
romanised, zero Devanagari). Then rebuild and re-measure:

```
python3 tools/gen_tool_pages.py
python3 tools/content_uniqueness.py --top 12
```

The median must not rise. If it does, the copy was not specific enough — rewrite
it rather than declaring success.

### 3. PageSpeed (free, no key)

```
curl -s "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https%3A%2F%2Ftankmetrics.in%2F&strategy=mobile"
```

Read `lighthouseResult.categories.performance.score` and the largest
`audits[*].score < 1` with a real saving. If the API answers 429 (daily quota),
skip it - it is a nice-to-have, not a blocker. Report the score in the summary.

### 4. Publish and report

```
python3 tools/lastmod_stamp.py    # stamp any page this run rewrote (honest lastmod)
tools/deploy.sh -m "SEO run <date>: real copy for <ids>, median overlap X% -> Y%"
```

Then print a short summary, in this shape:

```
SEO run <date>
  duplicate-blocking pages: A of 101 (was B), median overlap C% (was D)
  guides written this run: <ids>
  GSC buckets: indexed X, not-seen Y, discovered Z, crawled W
  PageSpeed mobile: <score or "quota exceeded">
  Sir's to-dos (agent cannot do): the backlink/listings work is in the
    site-authority run's output; nothing here needs a human
```

## Hard rules
- Never claim to have used a tool that needs a login.
- Never post anywhere, never send an email, never submit a listing, never buy a
  link. (This run does not touch those anyway.)
- Never invent keyword data. Use `keyword_radar.py` output only where relevant.
- Title <= 60 chars including " | Tank Metrics"; description 150-158.
- Worked examples use round numbers (10,000 / 6,000 / 8%).
- Tool pages stay >= 400 words.
- Run the test suite before deploying. It takes ~8 seconds.
