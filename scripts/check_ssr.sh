#!/usr/bin/env bash
# Verifies crawler-readable HTML: the overlay invariant (docs/conventions.md #1)
# requires page content to be present in server-rendered HTML without JS execution.
# Used by CI from TD-14 onward.
#
# Usage:
#   ./scripts/check_ssr.sh <url> <marker>          # single URL+marker check (legacy)
#   ./scripts/check_ssr.sh --all <base_url>         # check all routes against known markers
#   ./scripts/check_ssr.sh --seo <base_url>         # check SEO assets (sitemap, robots, llms.txt)
#
# Exits 0 if all checks pass, 1 otherwise.

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:3000}"

check_url() {
  local url="$1" marker="$2"
  local html
  html="$(curl --fail --silent --show-error --max-time 30 "$url")" || {
    echo "FAIL: could not fetch $url" >&2
    return 1
  }
  if printf '%s' "$html" | grep -qF -- "$marker"; then
    echo "PASS: $url — found: $marker"
    return 0
  fi
  echo "FAIL: marker missing from $url: $marker" >&2
  return 1
}

check_http_200() {
  local url="$1" label="${2:-}"
  local status
  status="$(curl --silent --show-error --max-time 30 -o /dev/null -w '%{http_code}' "$url")" || {
    echo "FAIL: could not fetch $url" >&2
    return 1
  }
  if [ "$status" = "200" ]; then
    echo "PASS: $url ($label) — HTTP $status"
    return 0
  fi
  echo "FAIL: $url ($label) — HTTP $status" >&2
  return 1
}

check_all_routes() {
  local base="$1"
  local failed=0

  # Static pages with expected content markers
  local routes=(
    "/|Siddhesh Chaudhari"
    "/timeline|Timeline"
    "/projects|Projects"
    "/skills|Skills"
    "/certifications|Certifications"
    "/tech-rabbithole|Tech Rabbithole"
    "/how-i-use-ai|How I Use AI"
    "/vc-for-founders|VC for Founders"
    "/thesis|Investment Thesis"
    "/books|Bookshelf"
    "/anime-manga|Anime"
    "/contact|Contact"
    "/dealflow|Dealflow"
  )

  for route_spec in "${routes[@]}"; do
    local route="${route_spec%%|*}"
    local marker="${route_spec##*|}"
    check_url "${base}${route}" "$marker" || ((failed++))
  done

  return "$failed"
}

check_seo_assets() {
  local base="$1"
  local failed=0

  # sitemap.xml
  check_http_200 "${base}/sitemap.xml" "sitemap" || ((failed++))

  # robots.txt
  local robots
  robots="$(curl --silent --show-error --max-time 30 "${base}/robots.txt")" || {
    echo "FAIL: could not fetch robots.txt" >&2
    ((failed++))
  }
  if printf '%s' "$robots" | grep -qF "GPTBot"; then
    echo "PASS: robots.txt allows GPTBot"
  else
    echo "FAIL: robots.txt missing GPTBot allow" >&2
    ((failed++))
  fi
  if printf '%s' "$robots" | grep -qF "ClaudeBot"; then
    echo "PASS: robots.txt allows ClaudeBot"
  else
    echo "FAIL: robots.txt missing ClaudeBot allow" >&2
    ((failed++))
  fi
  if printf '%s' "$robots" | grep -qF "Sitemap:"; then
    echo "PASS: robots.txt contains Sitemap directive"
  else
    echo "FAIL: robots.txt missing Sitemap directive" >&2
    ((failed++))
  fi

  # llms.txt
  check_http_200 "${base}/llms.txt" "llms.txt" || ((failed++))

  # JSON-LD on homepage
  local hp
  hp="$(curl --silent --show-error --max-time 30 "$base")" || {
    echo "FAIL: could not fetch homepage for JSON-LD check" >&2
    ((failed++))
  }
  if printf '%s' "$hp" | grep -qF 'application/ld+json'; then
    echo "PASS: homepage contains JSON-LD structured data"
  else
    echo "FAIL: homepage missing JSON-LD structured data" >&2
    ((failed++))
  fi

  return "$failed"
}

# --- main ---

if [ "$#" -lt 1 ]; then
  echo "Usage:" >&2
  echo "  $0 <url> <marker>              single URL check" >&2
  echo "  $0 --all [base_url]            check all routes" >&2
  echo "  $0 --seo [base_url]            check SEO assets" >&2
  exit 1
fi

case "$1" in
  --all)
    BASE="${2:-$BASE_URL}"
    echo "=== SSR Route Check ($BASE) ==="
    failed=0
    check_all_routes "$BASE" || failed=$?
    if [ "$failed" -eq 0 ]; then
      echo "All SSR route checks passed."
      exit 0
    else
      echo "$failed SSR route check(s) failed." >&2
      exit 1
    fi
    ;;
  --seo)
    BASE="${2:-$BASE_URL}"
    echo "=== SEO Asset Check ($BASE) ==="
    failed=0
    check_seo_assets "$BASE" || failed=$?
    if [ "$failed" -eq 0 ]; then
      echo "All SEO asset checks passed."
      exit 0
    else
      echo "$failed SEO asset check(s) failed." >&2
      exit 1
    fi
    ;;
  *)
    if [ "$#" -ne 2 ]; then
      echo "Usage: $0 <url> <marker>" >&2
      exit 1
    fi
    check_url "$1" "$2" || exit 1
    ;;
esac
