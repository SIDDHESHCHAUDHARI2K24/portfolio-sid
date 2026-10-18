#!/usr/bin/env bash
# Post-deploy smoke check: read-only GETs against the public site and admin.
# Backs .github/workflows/smoke.yml and the `health` job in deploy.yml.
#
# Usage:
#   ./scripts/smoke.sh <site-url> <admin-url>
#   ./scripts/smoke.sh https://siddhesh-chaudhari.com https://admin.siddhesh-chaudhari.com
#   ./scripts/smoke.sh http://localhost:24730 http://localhost:24752
#
# Env:
#   SMOKE_RETRIES      retries per request (default 8)
#   SMOKE_RETRY_DELAY  seconds between retries (default 10)
#
# curl runs WITHOUT -f: --retry already retries connection errors and
# transient 5xx (408/429/500/502/503/504), while a plain 404 is returned
# at once, so the expected-404 check does not retry-loop.
#
# Prints one line per check; exits 1 on the first failure.

set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: $0 <site-url> <admin-url>" >&2
  exit 2
fi

SITE="${1%/}"
ADMIN="${2%/}"
RETRIES="${SMOKE_RETRIES:-8}"
DELAY="${SMOKE_RETRY_DELAY:-10}"

check() {
  local url="$1" want="$2" got
  got="$(curl --silent --output /dev/null --write-out '%{http_code}' \
    --max-time 30 --retry "$RETRIES" --retry-delay "$DELAY" --retry-all-errors \
    "$url" || true)"
  if [ "$got" = "$want" ]; then
    echo "ok   $got $url"
  else
    echo "FAIL expected $want, got ${got:-none} $url" >&2
    exit 1
  fi
}

check "$ADMIN/api/v1/health" 200
check "$SITE/" 200
check "$SITE/books" 200
check "$SITE/anime-manga" 200
check "$SITE/how-i-use-ai" 200
check "$SITE/sitemap.xml" 200
check "$SITE/writing/does-not-exist" 404
echo "smoke: all checks passed"
