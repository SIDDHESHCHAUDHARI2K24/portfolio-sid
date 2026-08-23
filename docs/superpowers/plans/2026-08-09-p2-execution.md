# P2 Execution Plan — Sessions 3+

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unblock remaining P0 blockers (GitHub push, Stitch design, tokens), then fan out P2 content tracks A-F with TD-24 contention protocol as the gate.

**Architecture:** Sequential unblocking (push → design → tokens), then TD-24 foundation, then parallel tracks (TD-25 critical path + TD-30 no-migration) followed by serial merge queue (TD-26→27→28→29) with rebase-and-regenerate after each merge.

**Tech Stack:** FastAPI 0.141, SQLAlchemy 2.0.51, Alembic, Next.js 16.3, Vite 8 + TS 6, Tailwind v4, Framer Motion, PostgreSQL 16, MinIO, Docker Compose

**Spec reference:** `development_plan/todos/p0/TD-10-stitch-design.md`, `development_plan/todos/p0/TD-11-design-tokens.md`, `development_plan/todos/p2/TD-24-contention-protocol.md`, `development_plan/todos/p2/TD-25-track-a-projects.md`, `development_plan/todos/p2/TD-30-track-f-intro-audio.md`, `overall_context/ui-design-brief.md`, `docs/conventions.md`

## Global Constraints

- **Revalidation in router, not service** — ORM operations + dict serialization in service, commit in service, revalidate in router after response is built (Session 2 §4.1)
- **No `from_attributes=True`** — all feature routers serialize ORM to dict in service, then Pydantic constructor (Session 2 §4.2)
- **Service returns dicts, not ORM objects** — `service.create_dict()`, `service.update_dict()`, `service.get_dict()` (Session 2 §4.3)
- **Always initialize M2M relationships** — set `entry.topic_tags = []` when empty, touch relationship in update (Session 2 §4.4)
- **Enum coercion in service** — convert Pydantic-dumped strings back to enum members for ORM construction (Session 2 §4.5)
- **`create_type=False` for all pre-existing native Postgres enum types** in migrations; only new enums get `create_type=True` (Session 2 §4.6)
- **Backend commands from `backend/`**; local services via `docker compose up -d` from repo root
- **One migration per feature branch**, always generated against current `origin/main` via `scripts/regen_migration.sh`
- **`alembic heads` must return exactly one head** (CI-enforced)
- **Append-only in shared registries** (`models_registry.py`, `app/app.py`, `tiles.ts`, `cacheTags.ts`), alphabetical, never reorder
- **Never call `cookies()` in content RSCs** — kills ISR silently. `next build` must report content routes static
- **Conventional commits** (`feat(p2): ...`, `fix(backend): ...`, `chore: ...`)
- **Never commit secrets**; `.env` files stay gitignored
- **Tile contract** documented in `docs/conventions.md` §80-100; every P2 content feature contributes one `Tile`
- **UI design brief** (`overall_context/ui-design-brief.md`): dark theme `#0A0A0A`, tiles `#16161A`, borders `#2A2A31`, text `#F2F2F0`, muted `#8A8A94`, accent amber `#E8B34B` for relevance only, near-square 4px corners, no shadows/glows, no hexagons
- **Display type**: Archivo Black or Space Grotesk Bold, uppercase, tight tracking; body: Inter; utility: JetBrains Mono
- **Tile grid responsive** on all breakpoints — no separate mobile pattern
- **Dimmed content must still meet WCAG AA**
- **Intro is overlay above server-rendered content** — never `showIntro ? <Intro/> : <Overview/>`
- **Stitch output**: take tokens only, never import generated HTML/markup into apps

---

### Task 1: GitHub Authentication + Push Pending Commits

**Files:**
- Modify: git remote origin (set URL with token)
- Verify: `git push origin main`

**Depends on:** Token provided by user (one-time use, never stored)
**Produces:** 7 pending commits pushed to `origin/main`, clean local/remote sync

- [ ] **Step 1: Configure git remote with token**

```bash
git remote set-url origin "https://SIDDHESHCHAUDHARI2K24:REDACTED-PAT@github.com/SIDDHESHCHAUDHARI2K24/portfolio-sid.git"
```

- [ ] **Step 2: Verify remote reconfiguration**

```bash
git remote -v
```
Expected: origin URL contains token (masked in display), both fetch and push set.

- [ ] **Step 3: Push pending commits**

```bash
git push origin main
```
Expected: 7 commits pushed successfully to `origin/main`.

- [ ] **Step 4: Verify remote is in sync**

```bash
git fetch origin && git log --oneline origin/main -5
```
Expected: HEAD matches `origin/main` exactly.

- [ ] **Step 5: Sanitize remote URL (remove token)**

```bash
git remote set-url origin "https://github.com/SIDDHESHCHAUDHARI2K24/portfolio-sid.git"
```

- [ ] **Step 6: Verify remote is clean (no token in URL)**

```bash
git remote -v | grep -v "ghp_" || true
git remote -v
```
Expected: URLs show `github.com/SIDDHESHCHAUDHARI2K24/portfolio-sid.git` with no token.

- [ ] **Step 7: Commit (if any env files changed) or mark complete**

No commit needed — this is infrastructure setup. Move to Task 2.

---

### Task 2: TD-10 — Stitch MCP Verification + DESIGN.md Export

**Files:**
- Verify: `.mcp.json` (already committed, uses `${STITCH_API_KEY}`)
- Create: `docs/DESIGN.md`
- Reference: `overall_context/ui-design-brief.md` §11 (Stitch prompts), `development_plan/todos/p0/TD-10-stitch-design.md`

**Depends on:** Task 1 (GitHub push)
**Produces:** Verified Stitch MCP connection, `docs/DESIGN.md` with colour tokens, typography, spacing

**Context:** `.mcp.json` already committed with `x-goog-api-key: ${STITCH_API_KEY}` expansion. The key exists in local gitignored `.env`. Verify the HTTP transport connects, then generate DESIGN.md using the ui-design-brief prompts.

- [ ] **Step 1: Verify STITCH_API_KEY is present in .env**

```bash
grep "STITCH_API_KEY" .env | head -1 | cut -c1-20
```
Expected: `STITCH_API_KEY=sk-...` (prefix visible, value not shown). If absent, abort and request the key.

- [ ] **Step 2: Test Stitch MCP HTTP connectivity**

```bash
source .env && curl -s -o /dev/null -w "%{http_code}" \
  -H "x-goog-api-key: ${STITCH_API_KEY}" \
  "https://stitch.googleapis.com/mcp" || echo "Fallback: try @google/stitch-mcp npx server or @_davideast/stitch-mcp proxy"
```
Expected: HTTP response received (2xx = connected, 4xx = key invalid, other = network issue). Note the response code for DESIGN.md rationale.

- [ ] **Step 3: Generate DESIGN.md using Stitch prompts from ui-design-brief.md §11**

Use each Stitch prompt from `overall_context/ui-design-brief.md` §11 (Screens 1-9) to generate design outputs.

- [ ] **Step 4: Write DESIGN.md with extracted tokens**

Write `docs/DESIGN.md` containing the complete token set from `ui-design-brief.md` §4-6 plus any refinements from Stitch generation:

```markdown
# DESIGN.md — Portfolio Dark Theme

## Colour Tokens
--ink:            #0A0A0A  (page base)
--surface:        #16161A  (tile background)
--surface-raised: #1F1F24  (hover, elevated tile)
--line:           #2A2A31  (borders, dividers)
--text:           #F2F2F0  (primary text)
--text-muted:     #8A8A94  (metadata, captions)
--relevant:       #E8B34B  (warm amber — relevance signal ONLY)
--relevant-dim:   #6B5423  (relevant border at rest)

## Typography
- Display: Archivo Black or Space Grotesk Bold (900 weight, uppercase, tight tracking)
- Body: Inter (400 weight, 1rem/1.6)
- Utility: JetBrains Mono (tabular-nums, 0.02em tracking)

## Type Scale
display-xl:  clamp(2.5rem, 8vw, 5rem)    900 uppercase -0.04em
display-lg:  clamp(2rem, 5vw, 3.5rem)     900 -0.03em
title:       1.5rem                         700 -0.02em
body:        1rem / 1.6                     400
small:       0.875rem / 1.5                 400
mono-sm:     0.8125rem                      tabular-nums 0.02em
label:       0.6875rem                      uppercase 0.2em --text-muted

## Spacing Scale
4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96

## Radius
tile: 4px · control: 3px · pill: 999px

## Grid
12 columns, 24px gutter, max-width 1280px

## Elevation
Borders only — no drop shadows, no glows.
--surface against --ink + --line border.
Hover: --surface-raised + brighter border.

## Relevant Signal
Amber (#E8B34B) used exclusively for relevance.
Never on general buttons, headings, or as decoration.
Relevant tiles: --relevant-dim border at rest.
Relevant entries: amber left rule + chromatic accents.
```

- [ ] **Step 5: Verify DESIGN.md exists with required sections**

```bash
grep -c "\-\-ink" docs/DESIGN.md
grep -c "\-\-relevant" docs/DESIGN.md
grep -c "Archivo" docs/DESIGN.md
grep -c "clamp" docs/DESIGN.md
```
Expected: all grep hits > 0 (tokens, typography, type scale present).

- [ ] **Step 6: Verify no secrets committed**

```bash
git log -p .mcp.json | grep -c "sk-" || true
grep -c "sk-" docs/DESIGN.md .mcp.json || true
```
Expected: 0 hits (no API keys in any tracked file).

- [ ] **Step 7: Commit**

```bash
git add docs/DESIGN.md .mcp.json
git commit -m "chore: Stitch MCP verified + DESIGN.md dark palette tokens"
```

---

### Task 3: TD-11 — Design Tokens → Tailwind/shadcn Both Apps

**Files:**
- Modify: `frontend/app/globals.css`, `frontend/tailwind.config.ts`
- Modify: `admin/src/index.css`, `admin/tailwind.config.ts`
- Modify: `docs/conventions.md` (hardcoded-hex guard rule)
- Reference: `docs/DESIGN.md`, `development_plan/todos/p0/TD-11-design-tokens.md`

**Depends on:** Task 2 (`docs/DESIGN.md` present)
**Produces:** CSS custom properties in both apps wired to Tailwind/shadcn, hex-literal guard rule

**Context:** Map all DESIGN.md tokens to CSS custom properties in both apps' stylesheets, wire into Tailwind `theme.extend`, map onto shadcn's CSS variable names. Add guard: no hardcoded hex values outside token definition files.

- [ ] **Step 1: Define CSS custom properties in `frontend/app/globals.css`**

Add after existing imports/content:

```css
@theme {
  --color-ink: #0A0A0A;
  --color-surface: #16161A;
  --color-surface-raised: #1F1F24;
  --color-line: #2A2A31;
  --color-text: #F2F2F0;
  --color-text-muted: #8A8A94;
  --color-relevant: #E8B34B;
  --color-relevant-dim: #6B5423;
  
  --font-display: 'Archivo Black', 'Space Grotesk Bold', sans-serif;
  --font-body: 'Inter', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```

- [ ] **Step 2: Wire Tailwind config to CSS tokens in `frontend/tailwind.config.ts`**

```typescript
// In theme.extend:
colors: {
  ink: 'var(--color-ink)',
  surface: 'var(--color-surface)',
  'surface-raised': 'var(--color-surface-raised)',
  line: 'var(--color-line)',
  text: {
    DEFAULT: 'var(--color-text)',
    muted: 'var(--color-text-muted)',
  },
  relevant: {
    DEFAULT: 'var(--color-relevant)',
    dim: 'var(--color-relevant-dim)',
  },
},
fontFamily: {
  display: ['var(--font-display)'],
  body: ['var(--font-body)'],
  mono: ['var(--font-mono)'],
},
```

- [ ] **Step 3: Map onto shadcn CSS variables in `frontend/app/globals.css`**

Add shadcn variable mapping referencing the same custom properties:

```css
:root {
  --background: var(--color-ink);
  --foreground: var(--color-text);
  --primary: var(--color-relevant);
  --primary-foreground: var(--color-ink);
  --muted: var(--color-surface);
  --muted-foreground: var(--color-text-muted);
  --border: var(--color-line);
  --radius: 4px;
}
```

- [ ] **Step 4: Repeat Steps 1-3 for `admin/src/index.css` and `admin/tailwind.config.ts`**

Same tokens, same wiring. Admin uses identical palette.

- [ ] **Step 5: Add hardcoded-hex guard rule to `docs/conventions.md`**

Append to invariant 12:

```markdown
### Guard rule (lint/review):
No hex color literal (`#[0-9a-fA-F]{3,8}`) or `rgb(` call may appear in component
code outside the two token-definition files (`frontend/app/globals.css`,
`admin/src/index.css`). Check: `git grep -nE "#[0-9a-fA-F]{6}" -- frontend/app admin/src`
(excluding the two token files).
```

- [ ] **Step 6: Verify frontend builds with tokens**

```bash
cd frontend && npm run build 2>&1 | tail -20
```
Expected: build succeeds, no errors.

- [ ] **Step 7: Verify admin builds with tokens**

```bash
cd admin && npx tsc --noEmit
```
Expected: no TypeScript errors.

- [ ] **Step 8: Hex scan — confirm no hardcoded colours in component code**

```bash
git grep -nE "#[0-9a-fA-F]{6}" -- frontend/app frontend/components admin/src | grep -v "globals.css" | grep -v "index.css"
```
Expected: empty output (or only intentional hits in token files). Fix any leaked hex values found.

- [ ] **Step 9: Token-swap proof — change one CSS variable, verify both apps change**

```bash
# Temporarily change --color-relevant to a test value in globals.css
# Verify in dev server both apps render the changed colour
# Revert the change
```

- [ ] **Step 10: Commit**

```bash
git add frontend/app/globals.css frontend/tailwind.config.ts admin/src/index.css admin/tailwind.config.ts docs/conventions.md
git commit -m "feat: design tokens — DESIGN.md mapped to Tailwind/shadcn in both apps"
```

---

### Task 4: TD-24 — Contention Protocol

**Files:**
- Create: `scripts/regen_migration.sh`
- Create: `scripts/check_registries.py`
- Modify: `docs/conventions.md` (contention section already exists at §77-78)
- Modify: `backend/app/core/models_registry.py` (add append-zone sentinels)
- Modify: `backend/app/app.py` (add append-zone sentinels)
- Modify: `frontend/lib/tiles.ts` (add append-zone sentinels)
- Modify: `frontend/lib/cacheTags.ts` (add append-zone sentinels)
- Reference: `development_plan/todos/p2/TD-24-contention-protocol.md`

**Depends on:** Task 3 (design tokens)
**Produces:** Regen script, registry checker, append-zone sentinels in all shared files

**Context:** Five shared files are touched by every P2 track. Encode coordination as scripts + CI. The migration chain is highest risk — six branches autogenerating produce six heads. TD-24 mechanizes the rebase-and-regenerate discipline.

- [ ] **Step 1: Add APPEND-ZONE sentinel comments to `backend/app/core/models_registry.py`**

Read current file, wrap the import block with:

```python
# === APPEND-ZONE-START: feature model imports ===
# Add new feature model imports below, alphabetical, never reorder others
from app.features.auth.models import OTPChallenge, LoginAttempt  # auth
from app.features.overview.models import OverviewIntro  # overview
from app.features.relevance.models import AudienceTagMap, TopicTag  # relevance
from app.features.timeline.models import TimelineEntry  # timeline
# === APPEND-ZONE-END: feature model imports ===
```

- [ ] **Step 2: Add APPEND-ZONE sentinel comments to `backend/app/app.py` router block**

In `register_routers()`:

```python
# === APPEND-ZONE-START: feature router registration ===
# Register new feature routers below, alphabetical, never reorder others
app.include_router(auth_router)
app.include_router(overview_admin_router)
app.include_router(overview_public_router)
app.include_router(relevance_admin_router)
app.include_router(relevance_public_router)
app.include_router(tag_admin_router)
app.include_router(timeline_admin_router)
app.include_router(timeline_public_router)
# === APPEND-ZONE-END: feature router registration ===
```

- [ ] **Step 3: Add APPEND-ZONE sentinel comments to `frontend/lib/tiles.ts`**

```typescript
// === APPEND-ZONE-START: tile registrations ===
// Add new tiles below, alphabetical by id, never reorder others
// === APPEND-ZONE-END: tile registrations ===
```

- [ ] **Step 4: Add APPEND-ZONE sentinel comments to `frontend/lib/cacheTags.ts`**

```typescript
// === APPEND-ZONE-START: cache tag constants ===
// Add new cache tags below, alphabetical, never reorder others
// === APPEND-ZONE-END: cache tag constants ===
```

- [ ] **Step 5: Create `scripts/regen_migration.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Usage: bash scripts/regen_migration.sh "<migration message>"
# Must run from the repo root.

MESSAGE="${1:?Missing migration message}"

# a. Assert rebased on origin/main
git fetch origin
if ! git merge-base --is-ancestor origin/main HEAD; then
  echo "ERROR: HEAD is not a descendant of origin/main. Rebase onto origin/main first."
  exit 1
fi

# b. Assert clean tree
if ! git diff --quiet --exit-code; then
  echo "ERROR: uncommitted changes present. Commit or stash them first."
  exit 1
fi
if ! git diff --cached --quiet --exit-code; then
  echo "ERROR: staged changes present. Commit or unstage them first."
  exit 1
fi

# c. Delete branch-local migrations (absent from origin/main)
echo "Removing branch-local migrations..."
for f in backend/alembic/versions/*.py; do
  if ! git cat-file -e "origin/main:$f" 2>/dev/null; then
    echo "  Removing: $f"
    rm "$f"
  fi
done

# d. Generate new migration
echo "Generating new migration..."
(cd backend && uv run alembic revision --autogenerate -m "$MESSAGE")

# e. Assert single head
HEAD_COUNT=$(cd backend && uv run alembic heads | wc -l)
if [ "$HEAD_COUNT" -ne 1 ]; then
  echo "ERROR: expected 1 alembic head, found $HEAD_COUNT"
  exit 1
fi

echo "Migration generated successfully. Single head confirmed."
```

Make executable: `chmod +x scripts/regen_migration.sh`

- [ ] **Step 6: Create `scripts/check_registries.py`**

```python
#!/usr/bin/env python3
"""Check that every feature model is registered and every router is wired."""

import sys
import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_APP = REPO_ROOT / "backend" / "app"
FEATURES_DIR = BACKEND_APP / "features"

def find_feature_files(directory: Path, pattern: str) -> list[str]:
    """Find feature files matching pattern (relative to features/)."""
    results = []
    for item in sorted(directory.iterdir()):
        if item.is_dir() and (item / pattern).exists():
            results.append(f"features/{item.name}/{pattern}")
    return results

def extract_class_names(file_path: Path) -> list[str]:
    """Extract top-level class names from a Python file."""
    try:
        tree = ast.parse(file_path.read_text())
        return [node.name for node in ast.iter_child_nodes(tree) 
                if isinstance(node, ast.ClassDef)]
    except Exception:
        return []

def check_models_registry() -> list[str]:
    """Check every features/*/models.py is imported in models_registry.py."""
    errors = []
    registry_path = BACKEND_APP / "core" / "models_registry.py"
    registry_content = registry_path.read_text() if registry_path.exists() else ""
    
    model_files = find_feature_files(FEATURES_DIR, "models.py")
    for mf in model_files:
        feature_name = mf.split("/")[1]
        # Check import exists
        import_line = f"from app.features.{feature_name}.models import"
        if import_line not in registry_content:
            # Also check just feature name is mentioned
            if f"features.{feature_name}" not in registry_content:
                errors.append(f"UNREGISTERED_MODEL: {mf}")
    
    return errors

def check_router_registration() -> list[str]:
    """Check every feature has routers registered in app.py."""
    errors = []
    app_py = BACKEND_APP / "app.py"
    if not app_py.exists():
        return ["APP_PY_NOT_FOUND"]
    
    app_content = app_py.read_text()
    
    endpoint_dirs = find_feature_files(FEATURES_DIR, "endpoints")
    for ed in endpoint_dirs:
        feature_name = ed.split("/")[1]
        if f"features.{feature_name}" not in app_content:
            errors.append(f"UNREGISTERED_ROUTER: {feature_name}")
    
    return errors

def main() -> int:
    model_errors = check_models_registry()
    router_errors = check_router_registration()
    
    errors = model_errors + router_errors
    
    if errors:
        for e in errors:
            print(f"  {e}")
        print(f"\n{len(errors)} registration error(s) found.")
        return 1
    
    print("All features registered.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

Make executable: `chmod +x scripts/check_registries.py`

- [ ] **Step 7: Verify regen script syntax**

```bash
bash -n scripts/regen_migration.sh
```
Expected: no errors.

- [ ] **Step 8: Verify registry checker runs**

```bash
python3 scripts/check_registries.py
```
Expected: "All features registered." with exit code 0.

- [ ] **Step 9: Simulated stale branch test (regen aborts)**

```bash
# Simulate: create a test branch diverged from origin/main
git checkout -b test-stale origin/main
git commit --allow-empty -m "test: stale commit"
# The regen script should detect origin/main is not ancestor
bash scripts/regen_migration.sh "test" 2>&1 || echo "Aborted as expected"
git checkout main
git branch -D test-stale
```
Expected: "ERROR: HEAD is not a descendant of origin/main" message, non-zero exit.

- [ ] **Step 10: Verify conventions.md contention section is adequate**

Read `docs/conventions.md` §77-78. It already documents the contention protocol. Confirm it references `scripts/regen_migration.sh` and `scripts/check_registries.py`.

- [ ] **Step 11: Commit**

```bash
git add scripts/regen_migration.sh scripts/check_registries.py docs/conventions.md backend/app/core/models_registry.py backend/app/app.py frontend/lib/tiles.ts frontend/lib/cacheTags.ts
git commit -m "chore: contention protocol — regen script, registry checks, append zones"
```

---

### Task 5: TD-25 (Track A — Projects) + TD-30 (Track F — Intro+Audio)

**IMPORTANT:** These two tracks run in PARALLEL (subagents). They touch disjoint file sets:
- TD-25: `backend/app/features/projects/`, `frontend/app/projects/`, admin project screens, migration
- TD-30: `frontend/components/intro/`, `frontend/components/audio/`, root layout, HUD — NO migration

Both depend on TD-24 (append zones in registries). Only TD-25 touches the migration chain and shared registries. TD-30 touches only frontend components.

**Execution protocol:**
1. Dispatch TWO parallel sub-agents: one for TD-25, one for TD-30
2. TD-25 agent: implements full Track A (model → slice → admin → public pages → tile)
3. TD-30 agent: implements full Track F (intro port → morph → guards → audio)
4. TD-25 must register its model/router/tile per append-zone protocol
5. After both complete, review results, run full test suite
6. Merge TD-25 first (critical path, has migration), then TD-30

**Note:** This is a dispatch task — the detailed implementation steps are in the respective todo cards:
- Track A: `development_plan/todos/p2/TD-25-track-a-projects.md` + `development_plan/development-plan-P2.md` Track A
- Track F: `development_plan/todos/p2/TD-30-track-f-intro-audio.md` + `development_plan/development-plan-P2.md` Track F

#### Pre-dispatch checklist

- [ ] Step 1: Verify Docker services are running

```bash
docker compose ps
```
Expected: postgres and minio running healthy.

- [ ] Step 2: Verify backend tests pass baseline

```bash
cd backend && uv run pytest -q
```
Expected: 93 passed.

- [ ] Step 3: Verify frontend builds clean

```bash
cd frontend && npm run build 2>&1 | tail -15
```
Expected: build succeeds, content routes static.

#### Sub-agent: TD-25 (Track A — Projects)

**Dispatch prompt:** Implement TD-25 Track A (Projects) per the todo card at `development_plan/todos/p2/TD-25-track-a-projects.md` and `development_plan/development-plan-P2.md` Track A.

Key implementation notes:
- `Project` model: standard mixins, `title`, `slug` (unique), `summary`, `description` (markdown), `timeline_entry_id` (nullable FK `ondelete="SET NULL"`), `video_url`, `topic_tags` M2M, `audience_override`
- `ProjectAttachment`: one-to-many, `kind` (PDF/PPT/IMAGE), `storage_key`, `label`, `sort_order`
- Service returns dicts (not ORM), no `from_attributes=True`, revalidation in router
- `create_type=False` for all pre-existing enums in migration
- Admin reuses `TagSelect`, `AudienceOverrideSelect`, `PublishStatusField`, `MarkdownField`
- New `AttachmentUploader` component for admin
- Public pages: RSC + client relevance component; YouTube via `youtube-nocookie.com`
- Cross-link to `/timeline#entry-{id}` clears filter chips
- Tile: Recruiters/Techies/Investors/Founders, omitted for Personal
- Register model in `models_registry.py` (APPEND-ZONE), router in `app/app.py` (APPEND-ZONE), tile in `tiles.ts` (APPEND-ZONE), cache tag in `cacheTags.ts` (APPEND-ZONE)
- Run `scripts/regen_migration.sh "projects"` then verify `alembic heads` == 1

Return: list of files created/modified, test results summary, any issues encountered.

#### Sub-agent: TD-30 (Track F — Intro + Audio)

**Dispatch prompt:** Implement TD-30 Track F (Intro Sequence + Ambient Audio) per the todo card at `development_plan/todos/p2/TD-30-track-f-intro-audio.md` and `development_plan/development-plan-P2.md` Track F.

Key implementation notes:
- **F.T1**: Port intro animation to Framer Motion React component. Six adjectives at ~0.45s intervals (CURIOUS, NERDY, CREATIVE, SCRAPPY, AMBITIOUS, BOLD), accumulating not replacing. Six squares fill in step, end as 2×3 grid. ~3s total. Use `useEffect`, not `window.onload`. Scope `overflow: hidden` to intro lifetime only. Relabel counter from "Status" to something non-claim. Use `cubic-bezier(0.16, 1, 0.3, 1)` easing.
- **F.T2**: Framer Motion `layoutId` shared layout animation linking loader squares → category selector tiles. One continuous motion. Keep both states mounted through transition.
- **F.T3**: `sessionStorage` bypass for returning visitors. `useReducedMotion` skip. Click and Escape skip. **Critical overlay invariant**: intro is overlay ABOVE server-rendered content. NEVER `showIntro ? <Intro/> : <Overview/>`. Verify with `curl`.
- **F.T4**: Single `<audio>` element in root layout (App Router preserves across navigation). Tracks from static config (R2 keys). HUD controls: play/pause, volume, track switch. `sessionStorage` persistence. On hard reload: restore state but do NOT auto-resume. Off by default on first visit.
- Design tokens from Task 3: `--color-ink`, `--color-surface`, `--color-relevant`, etc.
- Fonts: Display = Archivo Black/Space Grotesk (900 weight, uppercase, tight tracking). Mono = JetBrains Mono for counter.
- NO migrations in this track

Return: list of files created/modified, test results summary, any issues encountered.

---

### Tasks 6-9: TD-26 → TD-29 (Tracks B, C, D, E)

**DEFERRED.** These are serial merge-queue tracks executed after TD-25 and TD-30 are merged. Detailed plans will be added to this document after each preceding track merges. Execution order:

| Task | Track | Card | Depends on |
|---|---|---|---|
| 6 | TD-26 — Skills + Certifications | `p2/TD-26-track-b-skills-certs.md` | TD-25 merged |
| 7 | TD-27 — Thesis + Posts | `p2/TD-27-track-c-thesis-posts.md` | TD-26 merged |
| 8 | TD-28 — Collections + ProsePages | `p2/TD-28-track-d-collections-prose.md` | TD-27 merged |
| 9 | TD-29 — Resume + Forms | `p2/TD-29-track-e-resume-forms.md` | TD-28 merged |

After each merge: remaining branches rebase + `scripts/regen_migration.sh`. `alembic heads` stays at 1.
