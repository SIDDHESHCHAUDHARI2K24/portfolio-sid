#!/usr/bin/env bash
set -euo pipefail

# Usage: bash scripts/regen_migration.sh "<migration message>"
# Run from the repo root. Regenerates the feature branch's migration
# against the latest origin/main. One migration per branch, always the
# newest. Invariant: alembic heads must return exactly one head.

MESSAGE="${1:?Missing migration message}"

echo "--- Fetching origin ---"
git fetch origin

echo "--- Checking HEAD is a descendant of origin/main ---"
if ! git merge-base --is-ancestor origin/main HEAD; then
  echo "ERROR: HEAD is not a descendant of origin/main."
  echo "       Rebase onto origin/main first: git rebase origin/main"
  exit 1
fi

echo "--- Checking clean working tree ---"
if ! git diff --quiet --exit-code; then
  echo "ERROR: uncommitted changes present. Commit or stash them first."
  exit 1
fi
if ! git diff --cached --quiet --exit-code; then
  echo "ERROR: staged changes present. Commit or unstage them first."
  exit 1
fi

echo "--- Removing branch-local migrations (absent from origin/main) ---"
for f in backend/alembic/versions/*.py; do
  [ -f "$f" ] || continue
  if ! git cat-file -e "origin/main:$f" 2>/dev/null; then
    echo "  Removing: $f"
    rm "$f"
  fi
done

echo "--- Generating new migration ---"
(cd backend && uv run alembic revision --autogenerate -m "$MESSAGE")

echo "--- Verifying single head ---"
HEAD_COUNT=$(cd backend && uv run alembic heads | grep -c . || true)
if [ "$HEAD_COUNT" -ne 1 ]; then
  echo "ERROR: expected 1 alembic head, found $HEAD_COUNT"
  echo "       Run: cd backend && uv run alembic heads"
  exit 1
fi

echo "--- Migration generated successfully. Single head confirmed. ---"
echo "Next: verify with 'cd backend && uv run alembic upgrade head && uv run pytest -q'"
