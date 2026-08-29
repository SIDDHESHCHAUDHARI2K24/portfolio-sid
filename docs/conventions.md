# Conventions & Invariants

The architectural contract. Every agent and every phase inherits these. Violations are mostly silent in a browser — that is why they are written here.

## Domain & hosts
- Production: `siddhesh-chaudhari.com` · Admin: `admin.siddhesh-chaudhari.com` (Railway custom domain; single hostname for SPA + `/api/*`; Cloudflare Tunnel/Access dropped) · Media: served by backend at `admin.siddhesh-chaudhari.com/media` (Railway Volume; R2 dropped)
- Domain renewal price and backup policy recorded here when confirmed (TD-M1, TD-M4).

### Domain registrar facts (TD-M1, 2026-08-28)
- **Zone status:** Active in Cloudflare dashboard (confirmed).
- **Registrar:** Cloudflare Domains.
- **Auto-renew:** enabled.
- **WHOIS privacy:** included (Cloudflare Domains default).
- **Renewal price:** `TBD` — owner to confirm in Cloudflare Domains dashboard and replace this
  placeholder. Price is a dashboard fact only; never committed as a secret.

## Invariants

### 1. Overlay, never replacement (Critical)
The homepage renders the full default overview in server HTML. The intro sequence and category selector compose as overlays ABOVE it. Never `showIntro ? <Intro/> : <Overview/>` — that serves crawlers an animation instead of a portfolio. Verify with `curl` (`scripts/check_ssr.sh`), never with eyes.

### 2. Category state lives in a cookie
`portfolio_category`, one year, `SameSite=Lax`, NOT `HttpOnly` (client reads it). Never `localStorage` — the server must be able to read it (assumption A6).

### 3. No `cookies()` in content server components
Calling `cookies()` in an RSC opts the route into dynamic rendering and silently kills ISR. Highlight/dim and tile filtering are client-side: every content page ships the full dataset + `audience_tag_map` as ONE statically cached default variant. `next build` must report content routes static; checked in CI.

### 4. OverviewIntro exception
Headline/body genuinely differ per audience: server-render the `default` row into HTML, ship all six rows in the payload, client swaps on hydration. A missing default row is forbidden (seed enforces it).

### 5. Feature-sliced backend
`backend/app/features/<name>/` — one dir per feature, self-contained:

```
features/<name>/
├── endpoints/      # APIRouter modules (one per sub-feature if large)
├── tests/          # feature tests (global fixtures from app/conftest.py)
├── models.py       # ORM models
├── schemas.py      # Pydantic request/response schemas
├── repository.py   # queries (never imports FastAPI)
├── service.py      # orchestration (revalidation triggers, validation)
└── utils.py        # feature-local helpers
```

Feature slices never import each other. `app/core/` is the only shared surface. Only `core/storage.py` imports boto3. Repository layer never imports FastAPI. Frontend mirrors the pattern: `frontend/features/<name>/` (components, hooks, lib) with thin `app/` routes; admin: `admin/src/features/<name>/` (components, api, hooks) plus shared field components in `admin/src/components/fields/`.

### 6. Models registry
Every feature's models module is imported in `app/core/models_registry.py`; Alembic env imports the registry. Adding a feature = adding one import line (append, alphabetical, never reorder others). A forgotten line produces a silently empty migration — `scripts/check_registries.py` enforces it in CI.

### 7. Migrations: rebase and regenerate
One migration per feature branch, always generated against current `origin/main` via `scripts/regen_migration.sh`. Never hand-edit `down_revision`. Never merge a migration generated against a stale head. `alembic heads` must return exactly one head (CI-enforced). Adding a value to a Postgres native enum requires manual `ALTER TYPE` — Alembic does not autogenerate it.

### 8. Publishing & public reads
`public_filter` (core/queries.py) is the ONLY sanctioned public read path; public endpoints apply it, admin endpoints bypass explicitly. Revalidation fires after commit, never inside a transaction; webhook failure logs loudly but never rolls back the write. Scheduled publishing latency is up to 5 minutes (cron interval) — by design, not a bug.

### 9. Topic tags vs collection tags
Topic tags (`#ai`, `#fundraising`) drive audience relevance. Collection tags (`TECH_RABBITHOLE`, `HOW_I_USE_AI`, `VC_FOR_FOUNDERS`) and `ProsePage.group` route entries to pages. Separate relationships, never one vocabulary — conflating them silently corrupts site-wide highlighting.

### 10. Relevance parity
`is_relevant` exists twice (Python `core/relevance.py`, TypeScript `lib/relevance.ts`), both pure functions over plain data. A shared fixture asserts identical outputs; drift fails CI.

### 11. Revalidation tags are shared constants
Tag names live in one source (`frontend/lib/cacheTags.ts` + backend constant) — never duplicated string literals. A mismatch means the site silently never updates.

### 12. Design tokens only
Colours come from CSS custom properties/Tailwind token references in both apps. No hex literals, no `rgb(`, no default Tailwind palette classes (`bg-slate-800` etc.) in component code. Phase 3 re-skin must be a token swap.

### Guard rule (lint/review)
No hex color literal (`#[0-9a-fA-F]{3,8}`) or `rgb(` call may appear in component
code outside the two token-definition files (`frontend/app/globals.css`,
`admin/src/index.css`). Check: `git grep -nE "#[0-9a-fA-F]{6}" -- frontend/ admin/`
(excluding the two token files and config files).

### 13. Noindex until launch
`NEXT_PUBLIC_INDEXABLE` defaults to `false`; the Railway hostname must never be indexed. Flip only in TD-36 after every route is verified on the custom domain.

### 14. Admin security posture
`CORS_ALLOW_ORIGINS` is empty in production (same-origin by construction — admin SPA + `/api/*` share one hostname, no Cloudflare Tunnel). Router-level `Depends(require_admin)` — never per-endpoint decorators. Honeypot + per-IP rate-limit before any DB write (replaces Turnstile); identical generic responses for accepted/discarded submissions. `pull_request_target` with a checkout of PR code is forever prohibited in CI.

### 15. Secrets
Secrets live only in Railway env vars, GitHub `production` environment secrets, and local gitignored `.env`. Nothing secret ever enters git, logs, or response bodies. `.mcp.json` uses `${VAR}` expansion only.

## General
- All timestamps stored UTC, rendered viewer-local (A5). English only (A4). Single author/admin user (A2, A7).
- REST at `/api/v1`. npm per app; OpenAPI types generated per app from committed `openapi.json` (no hand-written API response types).
- Tests never mock the database for query-logic tests. E2E runs on PRs to `main` and `main` only; full suite always on `main`.
- CodeGraph does not model Next.js App Router routes (FastAPI ~98%); frontend gets symbol indexing only.
- Commits: conventional (`feat(backend): ...`, `fix(frontend): ...`, `chore: ...`). One logical change per commit.
- WSL2 note (not applicable here, recorded for completeness): keep the repo on the Linux-native filesystem; SQLite locking across `/mnt/c` breaks the CodeGraph index.

## Contention protocol (Phase 2)
Five files are shared across the six parallel tracks: `models_registry.py`, `app.py` router block, the Alembic chain, `frontend/lib/tiles.ts`, `frontend/lib/cacheTags.ts`. Registries use sentinel append-zones, alphabetical insertion, keep-both-canonical-order conflict resolution. Merge queue: Track A first, then completion order, one merge at a time; after each merge remaining branches rebase + regenerate. Full machinery: `scripts/regen_migration.sh`, `scripts/check_registries.py` (TD-24).

## Tile contract (Phase 1 / TD-22)

The homepage renders a grid of *tiles* below the per-audience overview intro. Every Phase 2 content feature contributes one tile as the final sub-task of its own track. The contract lives in `frontend/lib/tiles.ts`.

### Interface

```typescript
export interface Tile {
  id: string;          // stable identifier, e.g. "timeline", "books"
  title: string;       // display title
  summary: string;     // one-paragraph plain-text or short markdown
  href: string;        // link target
  audiences: string[]; // which audience segments see this tile (empty = all)
  priority: number;    // higher = earlier in the grid
  isEmpty: boolean;    // set true to omit this tile entirely
}
```

### Rules

- **Omission, not dimming.** A tile irrelevant to the current audience is absent from the grid (`isEmpty` or filtered by `audiences`). Unlike timeline entries, tiles are never dimmed.
- **Server-render the full grid.** The homepage ships all tile data in one static payload; audience filtering is client-side only.
- **Empty tile.** When a feature has no published content, its tile factory returns `isEmpty: true`. The grid omits it without a gap.
- **Priority ordering.** Higher `priority` tiles appear first. Timeline defaults to `20`, other features adjust relative to that baseline.

### Worked example: TimelineTile

`frontend/components/tiles/TimelineTile.tsx`:

```typescript
export function buildTimelineTile(entries: Entry[]): Tile {
  if (entries.length === 0) {
    return { id: "timeline", title: "", summary: "", href: "/timeline",
             audiences: [], priority: 20, isEmpty: true };
  }
  const latest = entries[0];
  return { id: "timeline", title: "Timeline",
           summary: latest.summary ?? `${latest.title} at ${latest.organisation}`,
           href: "/timeline", audiences: [], priority: 20, isEmpty: false };
}
```

A Phase 2 feature (e.g. Books) would create `frontend/components/tiles/BooksTile.tsx` exporting a `buildBooksTile(entries: Book[]): Tile` function, add it to the homepage data fetch, and append the tile to the grid array.
