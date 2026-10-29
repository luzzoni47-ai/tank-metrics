# Top-1 position push (hourly)

Brings the pages that already rank into position 1, and keeps an eye on AEO
(answer-engine) coverage. Registered as the automation
**"Tank Metrics Top-1 position push (hourly)"**, cron `0 * * * *`, Asia/Kolkata.

Why hourly: Search Console position data lags about a day, so the loop mostly
re-reads the same numbers; hourly is cheap because the script is deterministic
(no LLM, ~30 HTTP calls) and it means a move is noticed the hour it appears in
the API rather than the next day. If quota ever becomes a concern, change the
cron to `0 */6 * * *`.

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
