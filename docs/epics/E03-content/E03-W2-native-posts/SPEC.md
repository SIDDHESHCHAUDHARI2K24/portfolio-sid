# E03-W2 — Native articles (internal posts)

**Epic:** E03 Content · **Ticket:** E03-W2 · **Status:** Draft · **Depends on:** none

## Purpose
Posts are outbound links only (EPIC F4). The owner wants to write articles on the site itself, shown on `/how-i-use-ai`, `/tech-rabbithole` and `/vc-for-founders`.

## Goal
An `internal` post has a slug and a markdown body, appears on every themed page in its collections, and opens at `/writing/<slug>`.

## Reference files
- `backend/app/features/posts/{models,schemas,service,repository}.py`, `endpoints/router.py`, `tests/`
- `backend/alembic/versions/` (new migration)
- `frontend/app/how-i-use-ai/page.tsx`, `tech-rabbithole/`, `vc-for-founders/`, `frontend/features/posts/PostList.tsx`
- `frontend/app/[slug]/ProseClient.tsx` (markdown renderer to reuse), `frontend/app/sitemap.ts`, `frontend/lib/jsonld.ts`, `frontend/lib/cacheTags.ts`
- `admin/src/routes/posts/` (post form)
- `backend/openapi.json`, `admin/src/api.d.ts`, `frontend/src/api.d.ts`
- `docs/features/posts.md`, `docs/conventions.md` (invariant 3)

## Functionality
- **Model:** add `internal` to `PostPlatform`; add `slug: str | None` (unique, `[a-z0-9-]`, max 200) and `body: str | None` (markdown). `url` becomes nullable.
- **DB rules:** `CHECK`: internal ⇒ `slug` and `body` not null; non-internal ⇒ `url` not null.
- **API:**
  - `PostPublic` adds `slug` and `platform`; the list never includes `body`.
  - New `GET /api/v1/posts/slug/{slug}` → `PostDetail` with `body`; 404 if missing, unpublished, or not internal.
  - Admin create and update validate the rules above, returning 422 with field errors.
- **Frontend:**
  - `PostList` cards link internal posts to `/writing/<slug>` (same tab); external posts are unchanged.
  - New `app/writing/[slug]/page.tsx` renders title, date, tags and the markdown body with the prose renderer (`react-markdown` + `remark-gfm`, no `rehype-raw`).
  - The page uses `generateStaticParams` + `revalidate`, cache tag `posts`, canonical `/writing/<slug>`, `generateMetadata`, and Article JSON-LD.
  - Sitemap includes internal posts.
- **Admin:** a platform select of `internal` shows a slug field (auto-suggested from the title, editable) and a markdown textarea with live preview; it hides `url`.

## Edge cases
- Migration: `ALTER TYPE post_platform ADD VALUE 'internal'` is committed before the CHECK constraint uses it (separate migration step or `autocommit_block`). Downgrade drops the column and constraint; the enum value is left in place, as documented.
- Slug collisions → 422 `slug already exists`; slugs are normalized to lowercase.
- Switching a post from internal to external requires `url`; the body may stay stored but is not served.
- An unpublished or scheduled internal post → 404 on `/writing/<slug>` and absent from the sitemap.
- Raw HTML or `<script>` in the body renders as text, never executes (test it).
- A post in several collections appears on each themed page; the single canonical URL avoids duplicate content.
- A large body (more than 100 KB) → 422.
- Relevance and audience highlighting work unchanged (tags are shared).

## Testing
- Backend: model and schema rules per edge case; slug endpoint 200, 404 for unpublished, 404 for external; the list excludes the body; migration up/down on a scratch DB; alembic single head.
- Frontend: `npm run lint && npm test && npm run build`; the build lists `/writing/[slug]` as static/ISR; a vitest test for the card link split; a Playwright journey for themed page → article → back.
- Admin: `npm run lint && npm run build`; the react-doctor skill.
- Local: create, publish and view an internal post through admin → site.

## Acceptance criteria
- [ ] EPIC criteria 3, 4 and 5 hold.
- [ ] XSS test passes (no raw HTML execution).
- [ ] OpenAPI and both `api.d.ts` files regenerated; `docs/features/posts.md` updated.

## Rollback
Revert the code and redeploy. If internal posts already exist, unpublish them first. Downgrade the migration only after deleting internal rows.
