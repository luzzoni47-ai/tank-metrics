# Daily runbook - kill duplicate content (the real indexing blocker)

The site is technically clean (seo_monitor: 0 problems) and Google is allowed to
index every page, yet only a fraction of the 101 calculators are indexed. The
cause is measured, not guessed: 80 of 101 calculator pages are a >= 50%
near-duplicate of another (median 65%), because 86 of them have no guide of
their own and `gen_tool_pages.py` renders a shared per-CATEGORY template for
them. Google indexes one page per cluster and leaves the rest as
"Crawled - currently not indexed".

This runbook fixes that, a few pages at a time, every day, until
`dedup_worklist.py` reports zero remaining.

## What "done" looks like

- `python3 tools/dedup_worklist.py` -> "still on the category template: 0"
- `python3 tools/content_uniqueness.py` -> median closest-overlap well below 50%
- `python3 tools/validate_guides.py` -> OK
- the "Crawled - currently not indexed" count in Search Console falling over the
  following weeks (check with `python3 tools/gsc.py inspect <url>`)

## The daily run

1. **Pick the batch.** Run:

   ```
   python3 tools/content_uniqueness.py        # refresh the overlap numbers
   python3 tools/dedup_worklist.py --limit 8
   ```

   Take the top 3-5 ids from "next up". The list is already ordered by impact
   (biggest category first, half-written pages first).

2. **Write the guides.** For each id, add an entry to `tools/tool_guides.json`
   under `calcs.<id>` AND to `tools/tool_guides_hinglish.json` under the same id.
   Read the calculator's `name`, `desc` and its worked example in
   `tools/tool_examples.json` first - the example is generated from the real
   COMPUTE function, so quote its numbers, never invented ones.

   Fields (both languages):
   - `what`   - 220+ chars. What this ONE tool answers and why it matters. Not
                the category template with the name swapped in.
   - `formula`- 80+ chars. The actual arithmetic, in words.
   - `when`   - 3+ bullets. Real situations this tool is reached for.
   - `mistakes` - 3+ bullets. The errors people make with THIS calculation.
   - `intro`, `outro` - optional framing for the worked example.

   Rules: ₹ Lakhs and Crores only (never `$`, never "million"); Hinglish stays
   romanised (no Devanagari); every claim must match what the tool computes.

3. **Validate before building.**

   ```
   python3 tools/validate_guides.py
   ```

   It fails on a short guide, a missing field, a leftover `{name}`/`{desc}`, a
   `$`, a "5 million" figure, Devanagari in Hinglish, or copy too close to the
   category template. Fix and re-run until it says OK.

4. **Build and prove it.**

   ```
   bash tools/rebuild.sh        # runs validate_guides + dedup_worklist itself
   python3 tools/content_uniqueness.py
   ```

   The median overlap should tick down. If it did not move, the new guides are
   too close to the template - go back to step 2.

5. **Ship it.**

   ```
   bash tools/publish_guide.sh <one-of-the-slugs>   # tests, commit, push, deploy, IndexNow
   python3 tools/gsc.py submit                       # tell Google the sitemap changed
   ```

## Why this order and not "write 30 new pages"

Adding pages on top of 80 near-duplicates grows the tail, not the indexed count -
Google crawls the cluster, indexes one, drops the rest. De-duplicating the
existing 101 is the only change that converts "crawled" pages into "indexed"
pages. New keyword pages come after, and only with unique copy.

## Guard rails (do not weaken)

- `validate_guides.py` is a gate, not advice. A guide that fails it does not
  ship.
- `test_dedup.py` proves the guard still fires. Keep it in the suite.
- Never hand-type a figure that a page shows; the worked example is generated
  from the calculator itself. See `tools/gen_examples.py`.
- The two bugs fixed on 2026-10-29 must not return: a literal `{desc}` shipped
  on live pages because hand-written Hinglish guides are returned as-is, and a
  guide keyed `savingsgoal` when the id is `savegoal` was dead data. Both are now
  covered by `test_dedup.py`.
