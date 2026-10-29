#!/usr/bin/env bash
# Publish a news story end to end: generate, tests, commit, push, deploy, announce.
#
# The news counterpart of publish_guide.sh, for the same reason: the daily run
# was budgeted 30 minutes and spent most of it running a dozen separate commands
# and waiting on each turn, so it kept being killed before the deploy. The story
# itself is written by the agent; the shipping steps are fixed and live here.
#
# Usage:
#   tools/publish_news.sh <slug> [more paths...]
#
# The slug is the news story slug in tools/news.json, e.g.
# `rupee-falls-to-95-22-what-it-costs-importers-exporters`.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SLUG="${1:?usage: publish_news.sh <slug> [paths...]}"
shift || true
PATHS=("/$SLUG" "$@")

: "${GITHUB_PERSONAL_ACCESS_TOKEN:?GITHUB_PERSONAL_ACCESS_TOKEN is not set}"
: "${VERCEL_TOKEN:?VERCEL_TOKEN is not set}"

echo "==> gen_news (validates the story, writes pages/sitemap/llms.txt)"
python3 tools/gen_news.py

echo "==> rebuild (whole derived pipeline in the one correct order)"
bash tools/rebuild.sh

echo "==> tests"
for t in test_news test_blog test_layout test_blog_tabs test_contact_form \
         test_interlinks test_sitemap test_pwa test_nav; do
  printf '    %-18s ' "$t"
  if python3 "tools/$t.py" >/tmp/pn_test.log 2>&1; then
    echo PASS
  else
    echo FAIL
    grep -E "FAIL|problem" /tmp/pn_test.log | head -5 | sed 's/^/        /'
    echo "    refusing to publish a red suite" >&2
    exit 1
  fi
done

echo "==> sync_gsc_list"
python3 tools/sync_gsc_list.py

if ! grep -q "/$SLUG<" public/sitemap.xml; then
  echo "error: /$SLUG is not in public/sitemap.xml" >&2
  exit 1
fi
echo "    /$SLUG is in the sitemap"

echo "==> deploy"
bash tools/deploy.sh -m "Publish news story: /$SLUG" "${PATHS[@]}"

echo "==> verify live"
for p in "${PATHS[@]}"; do
  printf '    %-52s %s\n' "$p" \
    "$(curl -s -o /dev/null -w '%{http_code}' "https://tankmetrics.in${p}?cb=${RANDOM}")"
done

echo "==> done: https://tankmetrics.in/$SLUG"
