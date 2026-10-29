# Position #1 strategy - TankMetrics.in

Built from Search Console data (28 days to 2026-10-29), not from guesswork.
Regenerate the numbers with `python3 tools/query_plan.py 28`.

## The honest starting point

| Metric | 28 days | 90 days |
|---|---|---|
| Clicks | 30 | 32 |
| Impressions | 831 | 838 |
| Queries earning clicks | 0 | 0 |
| Pages with impressions | 80 of 148 | 80 |

Two things follow from this, and they decide the whole strategy.

**First: we already rank.** 27 queries sit inside the top 10. The site is not
invisible - it is ranked and unclicked. That is a much better problem than being
unranked, because it is fixable with titles and depth rather than with authority.

**Second: 100,000 clicks in a week is not reachable from this base.** It would
need roughly 14,000 clicks a day against a current 1. That is not a content
problem, it is a scale problem - it needs either a viral distribution channel or
years of authority. Anyone who promises it this week is guessing. What *is*
reachable, in weeks, is: turn 27 top-10 rankings into clicks, then convert the
highest-volume clusters into page-1 rankings. That is the path, and it compounds.

## Why nothing gets clicked: the CTR audit

The pattern in GSC is unmistakable.

| Query | Position | Impressions | Clicks |
|---|---|---|---|
| implied valuation | 6.7 | 6 | 0 |
| polygons spoons net worth | 9.1 | 19 | 0 |
| return on capital employed calculator | 6.3 | 3 | 0 |
| property valuation calculator free | 9.7 | 3 | 0 |
| home appraisal calculator | 9.0 | 3 | 0 |

Position 6-9 with zero clicks means the result is being *seen and skipped*. Two
causes, both now fixed in code:

1. **All 101 tool pages shared one description sentence** ("Free, instant and
   private - it runs in your browser, no sign-up needed."). Google could not tell
   them apart. Every page now builds its description from its own desc plus its
   own unique `bench` line - 101 unique, 0 duplicates.
2. **The titles did not contain the query words.** A searcher typing "implied
   valuation calculator" saw "Implied Valuation - Free Online Calculator | Tank
   Metrics" and moved on. `calcs.json` now carries `seo_title` / `seo_desc`
   overrides written in the query's own words, and `gen_tool_pages.py` honours
   them.

## The clusters worth winning

Rankings are not won one query at a time. They are won as a cluster: several
pages covering one topic, interlinked, so Google reads the site as the authority
on it. GSC shows four clusters where we already have a foothold.

### Cluster 1 - Implied valuation (best #1 candidate)

Six queries, all top-10, all zero clicks: `implied valuation` (6.7), `what is
implied valuation` (5.0), `implied valuation meaning` (10.0), `implied value
formula` (8.0), `50 lakh ka 5% kitna hota hai` (8.0), `home valuation calculator`
(19.5). The page has 1,297 words but is on the shared category template, so it
never says the words "implied valuation meaning" anywhere.

Actions, in order:
1. Write a unique guide for `impval` (what / formula / when / mistakes) using the
   query's own vocabulary - "meaning", "formula", "example".
2. Add an FAQ block answering the literal questions: what does implied valuation
   mean, how is it calculated, what is the formula, is it the same as pre-money.
3. Link to it from `/pre-money-and-post-money-valuation`, `/dilution-calculator`
   and `/shark-tank-valuation-calculator-in-crores` with the anchor "implied
   valuation".
4. Target #1 within 3-4 weeks. It is a low-volume, low-competition term - a US
   finance blog owns it now, not an Indian one.

### Cluster 2 - Pre/post money valuation

Five queries, positions 11-58, all zero clicks: `pre money and post money
valuation calculator` (11), `pre money valuation post money valuation` (11),
`premoney valuation calculator` (19), `pre money and post money valuation` (24),
`pre vs post money valuation` (58.8). One page, and it is 48 impressions - the
highest-impression calculator page on the site.

Action: deepen the page with a pre-money vs post-money comparison table, the
dilution arithmetic, and a worked Shark Tank example. Then internal links from
every valuation page. This cluster can carry the whole "valuation" topic.

### Cluster 3 - Property valuation

Four queries: `property valuation calculator free` (9.7), `home valuation
calculator` (19.5), `home appraisal calculator` (9.0), `on line property
valuation` (8.0). Three of these rank on `/property-valuation-calculator` and one
on `/implied-valuation`, which is a mismatch worth fixing with a dedicated
property page.

### Cluster 4 - Polygons / Shark Tank USA (the viral one)

Six queries, 40+ impressions, positions 8.9-11: `polygons spoons net worth` (19
impressions at 9.1), `polygon spoon net worth` (9), `polygons shark tank net
worth` (7), `polygons spoons valuation`, `polygons spoons founder`, `polygons
shark tank`.

This is the only cluster with real volume, because it is news. The title now
matches the query ("Polygons Spoons Net Worth After Shark Tank USA Deal"). The
next move is a **dedicated calculator page** - `/shark-tank-usa-valuation-calculator`
- because the searchers are asking a money question and we sell money tools.

## The recurring move: news -> calculator

Every Shark Tank episode creates a burst of "X net worth" and "X valuation"
queries. Those searchers arrive with a number in mind and want to check it. That
is precisely a calculator. So the repeatable engine is:

1. `tools/gen_news.py` publishes the story while the query is rising.
2. The story links to a calculator that does that story's arithmetic.
3. The calculator carries the story's slug in its "worked example".

The Polygons story already ranks top-10 for six queries. Turning it into a
calculator page is the highest-leverage single page we can ship this week.

## What to do in what order

| # | Action | Why | Effort |
|---|---|---|---|
| 1 | Unique guide + FAQ for `impval` | 6 top-10 queries, no page matches their words | 1 hour |
| 2 | Dedicated `/shark-tank-usa-valuation-calculator` | 40+ impressions, news-driven, top-10 | 2 hours |
| 3 | Deepen pre/post money page + internal links | Highest-impression cluster, positions 11-58 | 2 hours |
| 4 | Apply CTR titles to the remaining top-10 queries | 27 queries already rank and go unclicked | 1 hour |
| 5 | Continue de-dup batches 3+ | 71 of 101 pages still on the shared template | ongoing |
| 6 | Ship Day 3-6 keyword pages | Already planned, already specced | ongoing |

## The metric to watch

Not clicks - **clicks per 100 impressions on page-1 queries.** Today it is 0.
Every fix above is aimed at that number, and it is the leading indicator that
precedes a click rise by one to two weeks.
