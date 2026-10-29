# Search Console findings - 2026-10-29

First real Search Console data for tankmetrics.in, read via the OAuth credential
in `tools/gsc.py` (property `sc-domain:tankmetrics.in`, permission `siteOwner`).

## The numbers

| Window | Clicks | Impressions | CTR | Avg position |
|---|---|---|---|---|
| 28 days | 28 | 721 | 3.9% | 27.3 |
| 90 days | 30 | 728 | 4.1% | 27.3 |

154 distinct queries earned at least one impression in 90 days. Average
position 27 means the site sits on **page 3** for almost everything - present,
but effectively invisible.

## What is actually happening

1. **The site is indexed.** Home, `/blog`, `/percentage-calculator`,
   `/implied-valuation`, `/burn-rate-and-runway` all inspect as
   `PASS - Submitted and indexed`, robots `ALLOWED`, canonical matching. So the
   "59 not indexed" figure is the long tail, not a site-wide block.

2. **The tail is not being crawled or kept.** This is the near-duplicate
   problem the repo already measures: `tools/content_uniqueness.py` reports a
   median 68% text overlap between calculator pages (they share one per-category
   prose template). Google crawls the cluster, indexes one representative, and
   leaves the rest as "Crawled - currently not indexed" / "Discovered - not
   indexed". More thin pages does not add indexed pages; it adds to the tail.

3. **The sitemap had gone stale.** GSC last downloaded `sitemap.xml` on
   **2026-10-21**, eight days before this run - before the Day-1 keyword pages
   existed. Every new page therefore read "URL is unknown to Google". Re-submitted
   on 2026-10-29.

4. **Legacy `/site/*.html` URLs are still indexed as separate pages.** The 90-day
   page report shows `/site/index.html` (11 clicks, 92 impressions),
   `/site/contact.html` (25 impressions) and `/site/about.html` (24 impressions)
   ranking alongside the clean URLs. They now 308-redirect to the clean form, so
   this is consolidating, but the duplicate signals have not fully cleared.

5. **Nothing on the site has real search demand behind it.** The queries with
   impressions are tiny and unbranded ("ask calculator", "bill splitter",
   "break even point", "burn rate"). There is no head term and no branded
   search, which is the signature of a site with no backlinks.

## What this means

The bottleneck is **not** technical SEO (0 problems), **not** indexing
permission (pages pass), and **not** the sitemap (now refreshed). It is:

- **content depth** - the tail is near-duplicate, so it cannot be indexed, and
- **authority** - with no referring domains, Google both crawls slowly and ranks
  the site on page 3.

Adding 30 more pages on top of 81 near-duplicates would grow the tail, not the
indexed count. The order that works is: fix the duplicates, then earn links,
then scale content.

## Recommended order of work

1. **De-duplicate the existing calculators (highest impact).** Replace the shared
   per-category template with real per-page copy in `tool_guides.json`
   (`calcs.<id>`) and `tool_guides_hinglish.json`, ~3 calculators per daily run.
   Drive `content_uniqueness.py` median overlap down and watch the "Crawled -
   currently not indexed" count fall in the next GSC export.
2. **Earn the first real backlinks.** A handful of genuine referring domains
   (tool directories, a useful free template, a data study) does more for crawl
   rate and ranking than another 30 pages.
3. **Keep the sitemap fresh and re-submitted** after every deploy
   (`deploy.sh` already submits to IndexNow; `gsc.py submit` covers Google).
4. **Let the legacy `/site/*.html` redirects consolidate** - do not remove them.
5. **Only then scale new pages**, and only ones with real demand and unique copy.

## Note on the sitemap "indexed: 0"

The sitemaps API reports `indexed: 0`; Google deprecated that field, so it is not
a signal. Use `urlInspection` per page (`gsc.py inspect <url>`) for the real
verdict.
