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
| Google Search Console | Cannot log in. `tools/gsc.py` needs a service-account key that does not exist. Substitute: the sitemap + `tools/content_uniqueness.py` measure what GSC would have told us - which pages are thin or duplicated. |
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

### 4. Prepare ONE human-posted answer (no login needed)

`tools/keyword_radar.py` prints phrases with a `+` that the site has no page for.
Take the top one and write a 150-200 word, genuinely useful answer that a real
person would post on Quora or Reddit, ending with the relevant Tank Metrics
calculator link. Save it to `tools/outreach/draft-<date>.md`. **Do not post it** —
Sir posts it himself. Add a one-line note at the top saying it is agent-drafted.

This is the honest version of the Quora/Reddit/Medium/LinkedIn/HARO row: an
agent cannot hold those accounts, but it can remove the work of writing.

### 5. Publish and report

```
tools/deploy.sh -m "SEO run <date>: real copy for <ids>, median overlap X% -> Y%"
```

Then print a short summary, in this shape:

```
SEO run <date>
  pages indexed-blocking duplicates: A of 101 (was B), median overlap C% (was D)
  guides written this run: <ids>
  PageSpeed mobile: <score or "quota exceeded">
  outreach draft: tools/outreach/draft-<date>.md
  Sir's one-time to-dos (agent cannot do these): Google My Business, Crunchbase,
    Product Hunt, Indie Hackers profiles
```

## Hard rules
- Never claim to have used a tool that needs a login.
- Never post to Quora, Reddit, Medium or LinkedIn. Draft only.
- Never invent keyword data. Use `keyword_radar.py` output.
- Title <= 60 chars including " | Tank Metrics"; description 150-158.
- Worked examples use round numbers (10,000 / 6,000 / 8%).
- Tool pages stay >= 400 words.
- Run the test suite before deploying; it takes ~8 seconds and is never the
  reason a run is late.
