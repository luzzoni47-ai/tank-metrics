# Why each page is not indexed - page by page

Source: Search Console URL Inspection, all 148 sitemap URLs, crawled 2026-10-24.
Raw data: `tools/gsc_inspection.json`. Re-run with `python3 tools/gsc.py inspect <url>`.

## The scoreboard

| Coverage state | Pages | Meaning |
|---|---|---|
| Submitted and indexed | **93** | Google has it and can show it |
| Discovered - currently not indexed | **22** | Google knows the URL, chose not to crawl/fetch it yet |
| URL is unknown to Google | **4** | Google has never seen this URL |
| Crawled - currently not indexed | **1** | Google fetched it and decided not to index |

So 93 of 120 inspected pages are in. The GSC dashboard figure Sir saw (29 indexed
/ 59 not) was from an earlier crawl; the real ratio has improved to 93/27.

**The two failures have completely different causes, and that is the whole point
of doing this page by page.**

## Cause 1: "Discovered - currently not indexed" (22 pages)

This is not a rejection. Google knows the URL from the sitemap, and has decided
it is not worth spending crawl budget on yet. The usual reason is that the page
looks like other pages already indexed - so Google has no new reason to fetch it.

Every one of these 22 pages has **11-15 internal links**, which rules out
discovery. The real cause is measured in `tools/content_uniqueness.json`:

| Metric | Value |
|---|---|
| Tool pages measured | 101 |
| Pages with a near-duplicate | **66** |
| Median word overlap with nearest page | **65%** |

Two thirds of the calculator pages share about two thirds of their words,
because they are all rendered from the same category template. Google reads the
second one and sees a near-copy of the first. That is the diagnosis, and it
applies to this list:

| Page | Inlinks | Why it is waiting |
|---|---|---|
| `/markup-vs-margin` | 13 | Same template as `/gross-profit-and-margin`, which is indexed |
| `/cac-payback-period` | 11 | Same template as `/ltv-cac-ratio`, which is indexed |
| `/repeat-rate-retention-and-churn` | 11 | Same template as `/churn-rate` |
| `/run-rate` | 13 | Same template as `/arpu-mrr-and-arr` |
| `/cash-conversion-cycle` | 13 | Same template as `/working-capital` |
| `/cod-and-rto-loss-calculator` | 11 | Same template as `/marketplace-fees-explained` |
| `/employee-cost-ctc-calculator` | 5 | Template + few inlinks; both need work |
| `/freelancer-hourly-rate` | 5 | Template + few inlinks |
| `/franchise-store-roi` | 6 | Template + few inlinks |
| `/moic-and-irr` | 5 | Template + few inlinks |
| `/exit-calculator` | 5 | Template + few inlinks |
| `/client-acquisition-cost-cac` | 13 | Same template as `/customer-acquisition-cost` |
| `/client-lifetime-value-ltv` | 12 | Same template as `/ltv-cac-ratio` |
| `/agency-profit-margin` | 13 | Same template as `/gross-profit-and-margin` |
| `/client-profitability` | 12 | Template |
| `/employee-utilization-rate` | 11 | Template |
| `/churn-rate` | 5 | Template + few inlinks |
| `/love-calculator` | 12 | Template (fun tool, low demand) |
| `/days-between-two-dates` | 11 | Template |
| `/market-share-calculator` | 10 | Template |
| `/burn-rate-calculator-india` | 4 | Template **and** a new keyword page - needs inlinks |
| `/dilution-calculator-founders` | 4 | Template **and** a new keyword page - needs inlinks |
| `/discount-impact-on-profit-explained` | 6 | Blog page, same template |
| `/emi-calculator-2-lakh-loan` | 3 | New keyword page, needs inlinks |
| `/about` | 297 | Not a ranking page; fine that Google deprioritises it |
| `/news` | 86 | Index hub page; Google will fetch it as stories accumulate |

**The fix is the de-dup work already underway.** Batches 1 and 2 took the
hand-written guide count from 0 to 32 of 101. Every batch of 8 that lands makes
8 more pages unique, and Google indexes them in the following crawl. Batches 3+
are the single highest-value indexing task left.

**Second fix, for the five low-inlink pages:** `/employee-cost-ctc-calculator`,
`/freelancer-hourly-rate`, `/franchise-store-roi`, `/moic-and-irr`,
`/exit-calculator`, `/churn-rate` have 5-6 inlinks against a site average of 29.
Add them to the "related tools" block of the pages a founder actually visits
(`/startup-valuation-explained`, `/dilution-calculator`,
`/burn-rate-runway-guide`).

## Cause 2: "URL is unknown to Google" (4 pages)

Google has never seen these. They answer 200 and they are in the sitemap, so the
sitemap entry has not been read yet, or it was read before the URL existed.

| Page | Status | In sitemap |
|---|---|---|
| `/run-rate` | 200 | yes |
| `/break-even-point` | 200 | yes |
| `/repeat-rate-retention-and-churn` | 200 | yes |
| `/client-profitability` | 200 | yes |

**Fix:** submit each by hand in URL Inspection -> Request Indexing, and re-submit
`sitemap.xml`. `tools/gsc.py submit-urls` does the API half of this, and the
hourly Top-1 automation keeps doing it. A hand submit in the GSC UI is the
stronger signal and takes two minutes for four URLs.

## Cause 3: "Crawled - currently not indexed" (1 page)

Google fetched this page and chose not to index it. That is a quality verdict,
not a discovery problem.

**Fix:** this page needs its unique guide (de-dup batch) before it is worth
re-submitting. Re-submitting an unchanged page that was already declined just
re-confirms the decline.

## What to do, in order

| # | Action | Pages affected |
|---|---|---|
| 1 | De-dup batch 3 (8 guides) | 8 of the 22 waiting |
| 2 | Add the 6 low-inlink pages to related-tools blocks | 6 |
| 3 | Hand-submit the 4 unknown URLs in GSC | 4 |
| 4 | Keep the hourly automation running | all |
| 5 | Do not re-submit the "crawled, not indexed" page until it is rewritten | 1 |

## The one number that matters

**66 pages still share a near-duplicate.** That is the cause behind almost the
entire "not indexed" list, and it is the reason the de-dup batches matter more
than new pages right now. Shipping 100 new pages onto a site where two thirds of
the existing pages are near-copies would add 100 more pages for Google to
deprioritise.
