#!/usr/bin/env bash
# Publish a guide end to end: pipeline, tests, commit, push, deploy, announce.
#
# Why this exists: the guide runbook asked the agent to run ~12 separate
# commands, then commit, then deploy, then verify - each one a turn, and each
# turn a round trip to the model. The whole run was budgeted 30 minutes and the
# publishing half alone was eating it, so runs kept dying at the cap with the
# post written but never shipped. The steps are fixed and their order is fixed,
# so they belong in one script the agent calls once.
#
# The article itself is written by the agent (that is the part that needs
# judgement). Everything after it is deterministic.
#
# Usage:
#   tools/publish_guide.sh <slug> [more paths...]
#
# The slug is the clean URL path without the leading slash, e.g.
# `import-duty-explained`. Extra paths are passed to IndexNow after the deploy.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SLUG="${1:?usage: publish_guide.sh <slug> [paths...]}"
shift || true
PATHS=("/$SLUG" "$@")

: "${GITHUB_PERSONAL_ACCESS_TOKEN:?GITHUB_PERSONAL_ACCESS_TOKEN is not set}"
: "${VERCEL_TOKEN:?VERCEL_TOKEN is not set}"

echo "==> hinglish blocks"
python3 tools/hinglish.py --rebuild

echo "==> wire_blog_tools (Run the numbers + back-links)"
python3 tools/wire_blog_tools.py

echo "==> rebuild (whole derived pipeline in the one correct order)"
bash tools/rebuild.sh

echo "==> blog schema"
python3 tools/add_blog_schema.py

echo "==> fix_blog_meta (social tags derive from each page)"
python3 tools/fix_blog_meta.py

echo "==> tests"
for t in test_blog test_news test_layout test_blog_tabs test_contact_form \
         test_interlinks test_sitemap test_pwa test_nav test_landing; do
  printf '    %-18s ' "$t"
  if python3 "tools/$t.py" >/tmp/pg_test.log 2>&1; then
    echo PASS
  else
    echo FAIL
    grep -E "FAIL|problem" /tmp/pg_test.log | head -5 | sed 's/^/        /'
    echo "    refusing to publish a red suite" >&2
    exit 1
  fi
done

echo "==> sync_gsc_list"
python3 tools/sync_gsc_list.py

# The new post must be in the sitemap, or it ships invisible to search.
if ! grep -q "/$SLUG<" public/sitemap.xml; then
  echo "error: /$SLUG is not in public/sitemap.xml" >&2
  exit 1
fi
echo "    /$SLUG is in the sitemap"

echo "==> deploy"
bash tools/deploy.sh -m "Publish guide: /$SLUG" "${PATHS[@]}"

echo "==> verify live"
for p in "${PATHS[@]}"; do
  printf '    %-40s %s\n' "$p" \
    "$(curl -s -o /dev/null -w '%{http_code}' "https://tankmetrics.in${p}?cb=${RANDOM}")"
done

echo "==> done: https://tankmetrics.in/$SLUG"
