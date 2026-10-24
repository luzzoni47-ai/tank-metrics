#!/usr/bin/env bash
# Build, ship to Vercel, point the domain at it, and announce what changed.
#
# A push to main does NOT trigger a Vercel build: the project's stored
# link.repoId is stale (1383270195 vs the real 1399625774), so Vercel never
# matches the push. Until that link is repaired the deploy has to be asked for
# explicitly, which is what this script does.
#
# Usage:
#   tools/deploy.sh                          # ship whatever is committed
#   tools/deploy.sh -m "message" /new-post   # commit, push, ship, announce
#
# The deployment is built from GitHub, not from this working tree, so anything
# uncommitted would silently not ship. With -m the script commits and pushes
# first and the deployed commit always matches main. Without it, a dirty tree
# is a hard error rather than a quiet no-op.
#
# Needs VERCEL_TOKEN in the environment. Any paths given are submitted to
# IndexNow AFTER the domain points at the new build, because the engines fetch
# the key file from the live site and answer 403 if it is not there yet.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TEAM="team_TXJMGXfZ9VZ9ZemmkKmoOuYw"
PROJECT="prj_Y6MHqnmDyyD5U239ecqEMbrxh4ei"
REPO_ID="1399625774"

: "${VERCEL_TOKEN:?VERCEL_TOKEN is not set}"

MESSAGE=""
if [ "${1:-}" = "-m" ]; then
  MESSAGE="${2:?usage: deploy.sh -m \"message\" [paths...]}"
  shift 2
fi

# Generate first, so the derived files are part of the commit rather than left
# behind as a dirty tree that the GitHub build never sees.
echo "==> refreshing generated files"
python3 tools/gen_updates.py

if [ -n "$(git status --porcelain)" ]; then
  if [ -z "$MESSAGE" ]; then
    echo "working tree is dirty and no -m message was given." >&2
    echo "Vercel builds from GitHub, so uncommitted files would not ship." >&2
    echo "Re-run as: tools/deploy.sh -m \"what changed\" [paths...]" >&2
    exit 1
  fi
  echo "==> committing"
  git add -A
  git commit -q -m "$MESSAGE"
fi

echo "==> pushing main"
git push -q origin main

# The deployment is built by Vercel from GitHub (gitSource below), so a local
# `next build` ships nothing - it is only a pre-flight check. A fresh clone has
# no node_modules (gitignored), and there `npx` tries to DOWNLOAD next from npm
# (the wrong version) and hangs, which is what killed every automation run.
# So: build only when the dependency tree is actually present, and never let it
# hang the run.
if [ -d node_modules ]; then
  echo "==> building (local pre-flight)"
  timeout 600 npx next build >/dev/null || echo "    local build failed; Vercel builds from GitHub anyway"
else
  echo "==> no node_modules; skipping the local build (Vercel builds from GitHub)"
fi

echo "==> deploying to production"
DEPLOY=$(curl -s -X POST \
  "https://api.vercel.com/v13/deployments?teamId=${TEAM}&forceNew=1" \
  -H "Authorization: Bearer ${VERCEL_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"tankmetrics\",\"project\":\"${PROJECT}\",\"target\":\"production\",\"gitSource\":{\"type\":\"github\",\"repoId\":${REPO_ID},\"ref\":\"main\"}}")
DPL=$(printf '%s' "$DEPLOY" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("id") or "")')
if [ -z "$DPL" ]; then
  echo "deploy request failed:" >&2
  printf '%s\n' "$DEPLOY" >&2
  exit 1
fi
echo "    deployment ${DPL}"

echo "==> waiting for READY"
for _ in $(seq 1 60); do
  STATE=$(curl -s "https://api.vercel.com/v13/deployments/${DPL}?teamId=${TEAM}" \
    -H "Authorization: Bearer ${VERCEL_TOKEN}" \
    | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("readyState") or d.get("status") or "")')
  echo "    ${STATE}"
  case "$STATE" in
    READY) break ;;
    ERROR|CANCELED)
      echo "deployment ended as ${STATE}" >&2
      exit 1 ;;
  esac
  sleep 10
done
[ "$STATE" = "READY" ] || { echo "timed out waiting for READY" >&2; exit 1; }

echo "==> pointing the domain at it"
for ALIAS in tankmetrics.in www.tankmetrics.in; do
  curl -s -X POST \
    "https://api.vercel.com/v2/deployments/${DPL}/aliases?teamId=${TEAM}" \
    -H "Authorization: Bearer ${VERCEL_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"alias\":\"${ALIAS}\"}" >/dev/null
  echo "    ${ALIAS}"
done

sleep 6
for PATH_CHECK in / /sw.js /site/pwa.js; do
  printf '    %-18s %s\n' "$PATH_CHECK" \
    "$(curl -s -o /dev/null -w '%{http_code}' "https://tankmetrics.in${PATH_CHECK}?cb=${RANDOM}")"
done

if [ "$#" -gt 0 ]; then
  echo "==> announcing the change"
  python3 tools/indexnow_submit.py "$@"
fi

echo "==> done: https://tankmetrics.in"
