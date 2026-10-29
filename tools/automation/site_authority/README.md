# Site authority worker (daily, 4x a day)

Sir asked for 1,000 links + 1,000 guest posts + 1,000 site submissions a day
to reach DA 90 / authority 80+. That is not a thing that can be done, and an
automation that tried would get the site deindexed. This automation does the
real half instead and says so in the file header.

What it does each run (deterministic, no LLM):

1. Checks a curated registry of 24 genuinely free, login-free places that
   accept a tool listing, a resource suggestion or an editor pitch. Dead
   prospects are dropped, not emailed.
2. Prepares up to `DAILY_QUOTA` (3) submission packets, one per real prospect
   and one real page on the site, and commits them to
   `tools/outreach/authority/`. A prospect is never prepared twice.
3. Checks the citation profile on the free, login-free web (Hacker News
   Algolia) and classifies each hit.
4. Writes `tools/outreach/authority/ledger.json` with totals.

It never posts, submits, emails or pays for a link. Sir sends from his own
accounts. That is why the links are worth having.

    python3 main.py            # real run
    python3 main.py --dry-run  # report only, commit nothing

## Deploy

    tar -czf auth.tar.gz main.py
    # upload, then POST /api/automation/v1 with trigger 0 */6 * * * Asia/Kolkata

Automation id `cb80a5e4-ad01-40e4-97f5-df12c169359d`.
