# Tank Metrics — daily SEO runbook (the 20-tool list)

Sir listed 20 SEO tools and asked for a daily run that works through them. This
is that run. Read it top to bottom before doing anything.

## The one thing to understand first

Most of the 20 tools cannot be driven by an agent. Yoast, Rank Math, Ahrefs,
SEMrush, Screaming Frog, Keyword Planner, AnswerThePublic, HARO, Google My
Business, Crunchbase, Product Hunt and Indie Hackers all need a logged-in
account, and Sir cannot log into Google at all (the account sits behind an MFA
loop he cannot clear). An agent that claims to have "run Ahrefs" is lying. Do not
do that.

What an agent CAN do, every day, with no login:

| Tool Sir named | How this run covers it |
|---|---|
| Google Search Console | Cannot log into the UI, but `tools/gsc.py` drives the API with OAuth (`~/.gsc_oauth.json`) or a service-account key. If either is set, USE IT (step 1b) - it gives Google's own index verdict per page. If it is not set, substitute the sitemap + `tools/content_uniqueness.py`. Setup: `tools/automation/gsc_setup.md`. |
| PageSpeed Insights | Free public API, no key for a handful of calls. Measure the home page and one calculator. Report the score and the top opportunity. |
| Screaming Frog | Replaced by `tools/seo_monitor.py --local` and `tools/automation/site_health` - the same crawl (status, title, canonical, description, noindex, dead internal links). |
| Google Keyword Planner | Needs a Google Ads login. Substitute: `tools/keyword_radar.py` (Google autocomplete, free, no key). |
| AnswerThePublic | Needs a login. Substitute: keyword_radar's `+` gap phrases. |
| ChatGPT for ideas | The agent's own reasoning, grounded in keyword_radar output - never invented topics. |
| Yoast / Rank Math | Not applicable (this is a static HTML site, not WordPress). Their job - title/description length, canonical, schema - is done by `tools/seo_monitor.py` and the tests. |
| Quora / Reddit / Medium / LinkedIn / GuestPostTracker / HARO | These need a human account to post from. Do NOT post. Instead, PREPARE one draft answer per run for Sir to paste himself. |
| Google My Business / Crunchbase / Product Hunt / Indie Hackers | One-time account creation, not a daily task. Listed in the runbook as "Sir's to do", never actioned by the agent. |

So this run is: measure, fix what is fixable in code, and hand Sir the human-only
pieces ready to paste. Never claim a login-walled tool was used.

## Time budget
The run is killed at 30 minutes. Work briskly. If you are short on time, commit
and push what you have rather than leaving it uncommitted.

## Read first
1. `AGENTS.md` — build rules and gotchas.
2. `tools/content_uniqueness.json` from the last run, if it exists — this run
   writes the new one, and the diff is the progress report.

## Task, in order

### 1. Measure the site (deterministic, ~1 minute)

```
python3 tools/seo_monitor.py --local
python3 tools/content_uniqueness.py --top 12
python3 tools/keyword_radar.py --top 20
```

`content_uniqueness.py` prints the share of calculator pages that are
near-duplicates of another page. On 2026-10-22 that was **94 of 101 pages, median
66% overlap** — this is the reason only 5 pages are indexed in Google. Every run
must drive this number down. It is the single most important metric here.

### 1b. Search Console, when the key is present

If OAuth is set up (`~/.gsc_oauth.json` or `GSC_OAUTH_JSON`) or a service-account
key exists (`GSC_SA_JSON` / `~/.gsc_service_account.json`), this is the run's best
evidence - Google's own verdict, not a proxy. (`tools/gsc.py` prefers OAuth
automatically when it is present.)

```
python3 tools/gsc_triage.py                   # every page, its state, its fix
python3 tools/gsc.py sitemaps                 # submitted vs indexed
python3 tools/gsc.py analytics 28             # top queries + pages
```

`gsc_triage.py` is the one to run first: it inspects every sitemap URL (caching
the result for a week in `tools/gsc_inspection.json`) and buckets each page as
indexed / not-seen / discovered / crawled / canonical, with the single action
that fixes that state. On 2026-10-29 it read: 105 indexed, 20 not-seen, 17
discovered, 1 crawled.

Then act on the two fixable buckets:
- **not-seen** (Google never saw the URL): add 2-3 internal links from indexed
  pages, re-submit the sitemap, and Request Indexing in the GSC UI for the few
  that matter most.
- **discovered / crawled** (seen, not indexed): unique per-tool copy - the dedup
  worklist - plus internal links.

Report the bucket counts and the worst pages in the summary. If no credential is
present, say so plainly and continue - do NOT claim a Search Console run. Setup
is in `tools/automation/gsc_setup.md`.

### 2. Write real copy for the worst offenders (the actual indexing fix)

`gen_tool_pages.py` falls back to a shared per-CATEGORY template for any
calculator with no hand-written guide, so every calculator in a category renders
the same prose. Google does not index near-duplicates; it indexes one and drops
the rest. That is the whole problem.

Pick the 3 calculators from the top of `content_uniqueness.py`'s "worst pages"
list and give each a real guide entry in `tools/tool_guides.json` under `calcs`,
keyed by the calculator id (find the id in `tools/calcs.json`). Write:

- `what` — 2 paragraphs that only make sense for THIS calculator. Name the
  decision it settles. If the text would read fine on a sibling page, it is not
  specific enough and does not count as progress.
- `formula` — the actual arithmetic, with the variable names the tool uses.
- `mistakes` — 3 errors specific to this calculation.
- `when` — 3 situations where someone reaches for it.

Also add the Hinglish twin to `tools/tool_guides_hinglish.json` (same keys,
romanised, zero Devanagari).

Then rebuild and re-measure:

```
python3 tools/gen_tool_pages.py
python3 tools/content_uniqueness.py --top 12
```

The median must fall. If it does not, the copy was not specific enough — rewrite
it rather than declaring success.

Do 3 calculators per run. At that rate the 94 duplicates are gone in about a
month, which is far more valuable than any submission ping.

### 3. PageSpeed (free, no key)

```
curl -s "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https%3A%2F%2Ftankmetrics.in%2F&strategy=mobile"
```

Read `lighthouseResult.categories.performance.score` and the largest
`audits[*].score < 1` with a real saving. If the API answers 429 (daily quota),
skip it - it is a nice-to-have, not a blocker. Report the score in the summary.

### 4. Prepare backlinks and one human-posted answer (no login needed)

Two jobs, both "prepare, never post":

```
python3 tools/link_builder.py --top 3
```

This walks the curated list of real prospects (Product Hunt, AlternativeTo,
Hacker News, Crunchbase, Startup India, Indian finance blogs, Quora, Reddit),
checks each is live, and writes submission-ready copy or an outreach email into
`tools/outreach/`. It remembers what it already prepared in the KV store, so a
daily run never repeats a prospect. **Never send or submit anything** - Sir does
that from his own accounts. `tools/test_outreach.py` fails the build if the tool
ever grows a send/post call, because a mail blast or a forum auto-post is what
gets a domain penalised.

Then, from `tools/keyword_radar.py`'s `+` gap phrases, write ONE 150-200 word
answer a real person would post on Quora or Reddit, ending with the relevant
calculator link, saved to `tools/outreach/draft-<date>.md`. Draft only.

That is the honest version of the Quora/Reddit/Medium/LinkedIn/HARO row: an
agent cannot hold those accounts, but it can remove the work of writing.

### 5. Watch for anyone writing about the brand

```
python3 tools/brand_monitor.py
```

Sir's standing ask: if anyone writes "Tank Metrics" or "tankmetrics" anywhere, he
wants to see it. This scans Hacker News, Bing, Google News and DuckDuckGo - all
free, none needing a login - and writes `tools/reports/brand-latest.md`.

**Read the report before reporting it.** The classifier splits every hit three
ways and the split is the whole value:

- **About us** - a page on tankmetrics.in
- **Others linking to us** - a stranger's page that points at us. A real
  citation; the one to be pleased about.
- **Namesakes (not us)** - shares the words only. `tankmetrics.com`, BattleMetrics
  and a fuel-logging Chrome extension all sit here and are NOT about us.

Never tell Sir a namesake is a mention. If only namesakes were found, say so
plainly: nobody wrote about the brand this run. `tools/test_brand_monitor.py`
fails the build if a namesake is ever filed under "About us".

### 6. Publish and report

```
tools/deploy.sh -m "SEO run <date>: real copy for <ids>, median overlap X% -> Y%"
```

Then print a short summary, in this shape:

```
SEO run <date>
  pages indexed-blocking duplicates: A of 101 (was B), median overlap C% (was D)
  guides written this run: <ids>
  PageSpeed mobile: <score or "quota exceeded">
  backlink drafts written: tools/outreach/ (list them)
  outreach answer: tools/outreach/draft-<date>.md
  brand mentions: N about us, M citing us, K namesakes (tools/reports/brand-latest.md)
  Sir's to-dos (agent cannot do these): submit the listings and send the emails
    from his own accounts; set up Google My Business, Crunchbase, Product Hunt,
    Indie Hackers profiles once
```

## Hard rules
- Never claim to have used a tool that needs a login.
- Never post to Quora, Reddit, Medium or LinkedIn, and never send an outreach
  email or submit a directory listing. Draft only; Sir sends from his own account.
- Never buy a link. Paid links are a penalty risk, not a shortcut.
- Never invent keyword data. Use `keyword_radar.py` output.
- Title <= 60 chars including " | Tank Metrics"; description 150-158.
- Worked examples use round numbers (10,000 / 6,000 / 8%).
- Tool pages stay >= 400 words.
- Run the test suite before deploying, including `test_brand_monitor.py`; a
  false "mention" is worse than a missed one. It takes ~8 seconds and is never
  the reason a run is late.
