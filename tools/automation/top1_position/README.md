# Top-1 position push (6-hourly)

Brings the pages that already rank into position 1, and keeps an eye on AEO
(answer-engine) coverage. Registered as the automation
**"Tank Metrics Top-1 position push (6-hourly)"**, cron `30 */6 * * *`,
Asia/Kolkata.

Why not hourly: the platform allows 20 sandboxes/day and an hourly job alone
demanded 24, so most runs were skipped with `daily_sandbox_limit` and the other
automations starved. Search Console position data lags about a day anyway, so
four reads a day lose nothing. The cron is staggered to `:30` so it does not
collide with the site-authority job on `:00`.

## What it does each run

1. Pulls queries + pages from the Search Console API.
2. Buckets each query by what it needs to reach #1:
   - **TITLE FIX** - ranks <=10, zero clicks. The title does not contain the words
     the searcher typed. Cheapest win on the site.
   - **PUSH** - position 11-30. Needs depth and one internal link.
   - **BUILD** - impressions but no page of ours in the top 30.
   - **WATCH** - too little data to act on.
3. Diffs positions against the previous run and reports any move >= 1.0.
4. Opens (or comments on) one GitHub issue titled
   "Top-1 push: title fixes and position moves".

## Credentials

The GSC refresh token lives in the automation secret store as `GSC_OAUTH_JSON`
(same JSON shape as the gitignored `tools/.gsc_oauth.json`: client_id,
client_secret, refresh_token). `GITHUB_TOKEN` is used for the issue.

## Running it by hand

    GSC_OAUTH_JSON="$(cat tools/.gsc_oauth.json)" python3 main.py --dry-run

The same logic also exists in-repo as `tools/query_plan.py`, which writes
`tools/reports/query-plan.md`. This automation is the always-on copy.
