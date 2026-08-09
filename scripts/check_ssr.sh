#!/usr/bin/env bash
# Verifies crawler-readable HTML: the overlay invariant (docs/conventions.md #1)
# requires page content to be present in server-rendered HTML without JS execution.
# Used by CI from TD-14 onward.
#
# Usage: ./scripts/check_ssr.sh <url> <marker>
# Exits 0 if the marker appears in the fetched HTML, 1 otherwise.

set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <url> <marker>" >&2
  exit 1
fi

URL="$1"
MARKER="$2"

HTML="$(curl --fail --silent --show-error --max-time 30 "$URL")" || {
  echo "FAIL: could not fetch $URL" >&2
  exit 1
}

if printf '%s' "$HTML" | grep -qF -- "$MARKER"; then
  echo "PASS: marker found in server-rendered HTML: $MARKER"
  exit 0
fi

echo "FAIL: marker missing from server-rendered HTML at $URL: $MARKER" >&2
exit 1
