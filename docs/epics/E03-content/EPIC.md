# Epic E03: Content — collection covers, native articles, local samples

**Status:** Implemented locally; review fixes applied; awaiting deploy approval
**Coordinator:** Coordinator 1 (session `fd08bb3a-b07e-4a18-a7f4-032a1fb0a404`)
**Opened:** 2026-10-17 · **Branch:** `epic/E03-content` in worktree `../Portfolio-E03`

## Goal

Collection covers appear on the site without manual steps. The owner can publish native articles on the themed pages (`/how-i-use-ai`, `/tech-rabbithole`, `/vc-for-founders`). The local stack shows realistic samples of every content type, including covers and native articles.

## Scope

- Collections: a public `cover_url`, and an automatic cover lookup on save.
- Posts: an `internal` platform with `slug` and markdown `body`, rendered at `/writing/<slug>`.
- Admin: the post editor for internal posts; cover status in the collection form.
- `backend/scripts/seed_demo.py` (local-only samples), extended for covers and native articles.
- Docs: `docs/features/collections.md`, `docs/features/posts.md`, env registry.

## Non-goals

- UI redesign (E02 owns the visual direction).
- Comments, drafts beyond the existing publish workflow, rich-text WYSIWYG, image upload inside articles.
- Seeding production. The sample script never runs outside local development.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | Covers are fetched only when the admin clicks "Look up cover"; create and update never fetch. | `admin/src/routes/collections/CollectionsForm.tsx:162`, `docs/features/collections.md` |
| F2 | The frontend builds cover URLs from `NEXT_PUBLIC_R2_PUBLIC_URL`, which is unset locally and on Railway (R2 was dropped; media is served from `/media` via `MEDIA_BASE_URL`). Every cover would render as `undefined/<key>`. | `frontend/app/anime-manga/AnimeMangaClient.tsx:19`, `BooksClient.tsx`, `.railway/railway.ts` frontend env |
| F3 | Certifications already return a server-built `file_url`; collections return only `cover_key`. | `backend/app/features/certifications/schemas.py:28` |
| F4 | Posts are outbound links only: `url` is required and there is no body or slug. Themed pages cannot host native writing. | `backend/app/features/posts/models.py:63-81` |
| F5 | Prose pages already render markdown with `react-markdown` + `remark-gfm` (no raw HTML), a safe renderer to reuse. | `frontend/app/[slug]/ProseClient.tsx`, `frontend/package.json` |
| F6 | `GET /api/v1/prose?group=` ignores the filter. | Local check 2026-10-17 |

## Work items

| ID | Title | Depends on |
|----|-------|-----------|
| [E03-W1](E03-W1-collection-covers/SPEC.md) | Collection covers: `cover_url` and lookup on save | none |
| [E03-W2](E03-W2-native-posts/SPEC.md) | Native articles: internal posts at `/writing/<slug>` | none |
| [E03-W3](E03-W3-local-samples/SPEC.md) | Local samples: covers and native articles in `seed_demo.py` | W1, W2 |
| [E03-W4](E03-W4-prose-group-filter/SPEC.md) | Fix `?group=` filter on `/api/v1/prose` | none |
| [E03-W5](E03-W5-anilist-cover-fallback/SPEC.md) | AniList fallback for anime and manhwa covers | W1 |
| [E03-W6](E03-W6-media-caching/SPEC.md) | Media caching: long-lived cache headers (Part A), Cloudflare edge cache (Part B, user) | W1 |

W1, W2 and W4 touch separate slices and can run in parallel. W3 runs last.

## Acceptance criteria

1. Locally and on production, a collection item with a cover shows the image; an item without one shows the existing fallback.
2. Saving a collection item without a cover triggers one lookup; a failed lookup saves the item without a cover and without an error.
3. An internal post appears on each themed page in its collections and opens at `/writing/<slug>`, rendered from markdown with no raw HTML.
4. External posts behave exactly as before.
5. `npm run build` reports `/writing/[slug]` as static/ISR (conventions invariant 3: no `cookies()` in content RSCs).
6. `seed_demo.py` fills every content type locally, including covers and 3 native articles.
7. CI, E2E, lint, types and builds pass for all apps.

## Verification plan

- Local: the full checks in `AGENTS.md`; browse every themed page, `/books`, `/anime-manga` and three `/writing/<slug>` pages on 24730; create an internal post and a collection item in admin on 24752.
- Production (user-approved deploy): one collection item with a cover renders; one internal post renders at `/writing/<slug>` (the owner creates real content; no samples in production).

## Sessions

- Coordinator 1: `fd08bb3a-b07e-4a18-a7f4-032a1fb0a404`
