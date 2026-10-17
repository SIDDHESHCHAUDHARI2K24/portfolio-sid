# E03-W2 Native Posts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox syntax.

**Goal:** An `internal` post has a slug and markdown body, appears on every themed page of its collections, and opens at `/writing/<slug>`.

**Architecture:** Extend the `posts` slice in place (model, migration, schemas, service, repository, router). The public list stays body-free; a new `GET /api/v1/posts/slug/{slug}` returns the body for published internal posts. The frontend adds a statically generated ISR route `app/writing/[slug]` (server-rendered markdown, no cookies). Admin gains slug + markdown editor with preview.

**Tech Stack:** FastAPI, SQLAlchemy 2 async, Alembic, Postgres enum, Next.js 16 RSC/ISR, react-markdown + remark-gfm + rehype-sanitize, Vite admin, vitest.

**Spec:** `docs/epics/E03-content/E03-W2-native-posts/SPEC.md`

## Global Constraints

- Route is `/writing/<slug>` (user-approved). Slug `[a-z0-9-]`, max 200, stored lowercase, unique.
- Conventions invariant 3: no `cookies()` in `/writing/[slug]`; build must list it static/ISR.
- Invariant 7: exactly one alembic head; enum value added via manual `ALTER TYPE`.
- No `rehype-raw`; raw HTML/`<script>` in body renders as text.
- Body > 100 KB (102400 bytes UTF-8) is 422. Cache tag `posts`. Canonical `/writing/<slug>`.
- Do not touch `.env`, other worktrees, or push.

## Decisions (small gaps, recorded)

1. **DB enum label is `INTERNAL`** (uppercase). `PostPlatform` uses SQLAlchemy name-based labels (`SUBSTACK`...); the API/Python value stays `internal`.
2. **One migration**, `ALTER TYPE post_platform ADD VALUE IF NOT EXISTS 'INTERNAL'` inside `op.get_context().autocommit_block()` before columns/CHECK.
3. **Downgrade** drops CHECK, unique index, `slug`/`body`, restores `url NOT NULL`; the enum value stays. If internal rows exist it raises with a clear message (spec rollback: delete internal rows first).
4. **Cross-field rules live in the service** (merged state for PATCH), raising `PostRuleError(field, msg)`; the router maps it to 422 with pydantic-shaped `detail: [{loc:["body", field], msg, type}]`. Field-only rules (slug pattern, body size) live in schema validators. The DB CHECK is the backstop.
5. **Blank strings count as missing** (`url`, `slug`, `body` stripped). Slug is `strip().lower()` then validated against `^[a-z0-9]+(-[a-z0-9]+)*$`.
6. **Slug lookup is lowercased** (`/posts/slug/Foo` finds `foo`).
7. **Admin responses include `body`** (needed for editing); public list and public `PostPublic` never do. Public `slug` is exposed on the list (needed for card links); `url` becomes nullable there.
8. **Slug unique across all posts** (including external posts that keep a slug). Collision pre-checked in service (excluding self on PATCH) plus `IntegrityError` backstop, both 422 `slug already exists`.
9. **Sitemap and `generateStaticParams`** derive internal posts from `GET /posts` filtered on `platform === "internal"`; no extra endpoint. `generateStaticParams` returns `[]` if the API is unreachable at build (route stays ISR, on-demand).
10. **Renderer:** new shared server component `frontend/components/Markdown.tsx` (react-markdown + remark-gfm, no rehype-raw, no rehype-sanitize: raw HTML renders as visible escaped text, as the spec says; react-markdown's default urlTransform strips `javascript:` links). `ProseClient` is left untouched. Article typography is a small `.article-body` block in `globals.css` (design tokens only) because no typography plugin is installed.
13. **Admin refactor:** `PostForm.tsx` helpers were split into `postFormUtils.ts`, `LinkFields.tsx`, `MarkdownEditor.tsx` to keep react-doctor clean; admin gains `react-markdown` + `remark-gfm` for the preview.
14. **Playwright journey** (`frontend/tests/journeys/writing.spec.ts`) skips itself when no published internal post exists in `how_i_use_ai`; the repo config pins port 24730, so it was run with a throwaway config on 24731.
11. **Article JSON-LD** type `Article`; `datePublished` = `published_date ?? created_at`.
12. **Migration head reconciliation** with sibling branches (W1 adds its own migration) is the coordinator's job.

## File Structure

Backend (`backend/`):
- Create `alembic/versions/<rev>_native_posts.py`
- Modify `app/features/posts/{models,schemas,repository,service}.py`, `endpoints/router.py`
- Create `app/features/posts/tests/test_internal_posts.py`; modify `test_posts.py` only if existing assertions break
- Regenerate `openapi.json`

Frontend (`frontend/`):
- Create `components/Markdown.tsx`, `components/Markdown.test.tsx`
- Create `features/posts/postLink.ts`, `features/posts/postLink.test.ts`
- Modify `features/posts/PostList.tsx`, `app/sitemap.ts`, `lib/jsonld.ts` (+ `lib/jsonld.test.ts`), `vitest.config.mts` (jsx automatic)
- Create `app/writing/[slug]/page.tsx`
- Create `tests/journeys/writing.spec.ts` (Playwright)
- Regenerate `src/api.d.ts`

Admin (`admin/`): modify `src/routes/posts/PostForm.tsx`, `PostList.tsx` (label), regenerate `src/api.d.ts`.

Docs: `docs/features/posts.md`, SPEC checkboxes/status, `EPIC.md` status row if appropriate.

## Review Focus

1. Unicode/uppercase/underscore/leading-hyphen slugs ("Hello World!" -> 422; "My-Post" -> stored `my-post`). Tested in Task 2.
2. PATCH that flips platform to `internal` without slug/body, or to external without url. Task 3.
3. Draft/scheduled-future internal post leaking via slug endpoint or list. Task 4.
4. Body exactly 100 KB OK vs 100 KB + 1 byte rejected; multi-byte chars counted as bytes. Task 2.
5. Markdown link with `javascript:` URL and `<img onerror>`. Task 7 (sanitize drops/neutralizes).

## Tasks (ordered; dependencies in brackets)

### Task 1: Model + migration [none]

**Files:** `app/features/posts/models.py`, `alembic/versions/*_native_posts.py`, test `tests/test_internal_posts.py`.

**Interfaces — Produces:** `PostPlatform.INTERNAL = "internal"`; `Post.slug: str|None` (String(200), unique index), `Post.body: str|None` (Text), `Post.url: str|None`; table CHECK `ck_posts_platform_fields`: `(platform = 'INTERNAL' AND slug IS NOT NULL AND body IS NOT NULL) OR (platform <> 'INTERNAL' AND url IS NOT NULL)`; also slug format CHECK is not added (service/schema own it).

- [ ] Write failing DB tests (direct `Post(...)` inserts via `session`): `test_check_rejects_internal_without_slug_or_body`, `test_check_rejects_external_without_url`, `test_check_allows_internal_without_url`, `test_slug_unique_in_db`. Expect IntegrityError / success.
- [ ] Run: `pytest app/features/posts/tests/test_internal_posts.py -q` -> FAIL (no `INTERNAL`).
- [ ] Edit model (add enum member, columns, `__table_args__` with `CheckConstraint(..., name="ck_posts_platform_fields")`). Test DB uses `metadata.create_all`, so this exercises the CHECK.
- [ ] Generate migration with `alembic revision -m native_posts` (head auto-picked), hand-write body: `autocommit_block` ADD VALUE; `add_column slug/body`; `alter_column url nullable=True`; `create_index ix_posts_slug unique`; `create_check_constraint`. Downgrade per Decision 3.
- [ ] Run tests -> PASS. Scratch DB: `alembic upgrade head`; insert external + internal rows via SQL; `alembic downgrade -1` (internal present -> expect clear error; delete internal rows -> succeeds); `alembic upgrade head`; `alembic heads` -> one head.
- [ ] Commit `feat(posts): internal platform, slug and body columns (E03-W2)`.

### Task 2: Schemas validation [Task 1]

**Files:** `schemas.py`, tests.

**Interfaces — Produces:** `PostPublic` + `slug: str | None`, `url: str | None`; `PostDetail(PostPublic)` + `body: str`; `PostAdmin` + `body: str | None`; `PostCreate`/`PostUpdate` gain `slug: str | None`, `body: str | None`, `url: str | None` (Create default None). Validators: `slug` normalize+pattern+max 200 (422 on bad); `body` UTF-8 size <= 102400.

- [ ] Failing unit tests on the schema classes: `test_slug_normalized_lowercase`, `test_slug_rejects_invalid_chars` (`"Hello World!"`, `"-a"`, `"a_b"`, 201 chars), `test_body_100kb_ok_100kb_plus_one_rejected`, `test_body_multibyte_counts_bytes`.
- [ ] Implement `field_validator`s. Run -> PASS.
- [ ] Commit with Task 3.

### Task 3: Service + repository rules [Tasks 1-2]

**Files:** `service.py`, `repository.py`, `endpoints/router.py` (error mapping only), tests.

**Interfaces — Produces:** `class PostRuleError(ValueError)` with `.field`, `.message`; `service.validate_rules(platform, url, slug, body)`; `repository.get_by_slug(session, slug)`, `repository.slug_exists(session, slug, exclude_id)`; `service.get_internal_by_slug_dict(session, slug) -> dict | None`; `_post_to_dict` adds `slug`, `body`.

- [ ] Failing API tests (admin client, copy `_login` pattern; `calls`-free revalidate monkeypatch): `test_create_internal_requires_slug_and_body` (422, `loc` has `slug`/`body`), `test_create_external_requires_url`, `test_create_internal_ok_without_url`, `test_slug_collision_422_slug_already_exists`, `test_slug_collision_case_insensitive`, `test_patch_to_internal_without_slug_body_422`, `test_patch_internal_to_external_requires_url`, `test_patch_internal_to_external_keeps_body_not_served` (body stored, slug endpoint 404), `test_patch_own_slug_not_collision`, `test_oversize_body_422`, `test_external_posts_unchanged` (existing behaviour, url required).
- [ ] Implement; wrap commit in `IntegrityError` -> rollback + `PostRuleError("slug","slug already exists")`. Router `except PostRuleError` before `ValueError`.
- [ ] Run whole posts test dir -> PASS. Commit `feat(posts): validate internal post rules (E03-W2)`.

### Task 4: Public slug endpoint + list shape [Task 3]

**Files:** `endpoints/router.py`, `schemas.py` (PostDetail wiring), tests.

**Interfaces — Produces:** `GET /api/v1/posts/slug/{slug}` -> `PostDetail`, 404 unless `public_filter` AND platform internal. Route declared before `/{post_id}`.

- [ ] Failing tests: `test_slug_endpoint_returns_body_for_published_internal`, `test_slug_endpoint_404_unpublished` (draft), `test_slug_endpoint_404_scheduled_future`, `test_slug_endpoint_scheduled_past_ok`, `test_slug_endpoint_404_external_even_with_slug`, `test_slug_endpoint_404_missing`, `test_slug_lookup_case_insensitive`, `test_public_list_has_slug_no_body_key`, `test_get_by_id_has_no_body`, `test_internal_post_in_multiple_collections_on_each_page`, `test_internal_post_tags_and_audience_override_returned` (relevance inputs unchanged), `test_admin_response_includes_body`, `test_revalidate_fires_for_internal_create`.
- [ ] Implement; run full backend suite -> PASS.
- [ ] Commit `feat(posts): slug detail endpoint for internal posts (E03-W2)`.

### Task 5: Backend checks + OpenAPI [Task 4]

- [ ] `uv run ruff check .`, `uv run mypy app`, `uv run pytest -q` all green.
- [ ] `uv run python scripts/export_openapi.py`; in `admin/` and `frontend/`: `npm ci && npm run openapi:generate`.
- [ ] Commit `chore(openapi): regenerate for internal posts (E03-W2)`.

### Task 6: Frontend link split + card [Task 5] (frontend and admin tasks 6-9 are independent of each other)

**Files:** `features/posts/postLink.ts`, `PostList.tsx`, tests.

**Interfaces — Produces:** `postHref(post: {platform: string; slug: string | null; url: string | null}): { href: string; external: boolean }`. internal -> `{href: "/writing/<slug>", external: false}`; else `{href: url ?? "#", external: true}`.

- [ ] Failing vitest `postLink.test.ts`: internal -> `/writing/my-post` same-tab; substack -> url external; internal with missing slug falls back to `#` external false-safe (no crash).
- [ ] Implement; `PostList` uses `next/link` `Link` for internal (no `target`), `<a target=_blank rel=noopener noreferrer>` for external; label `internal: "Article"`; widen `PostItem` types.
- [ ] `npm test` PASS. Commit with Task 7.

### Task 7: Markdown component + article page + sitemap + JSON-LD [Task 5]

**Files:** `components/Markdown.tsx(+test)`, `app/writing/[slug]/page.tsx`, `app/sitemap.ts`, `lib/jsonld.ts(+test)`, `vitest.config.mts`.

**Interfaces — Produces:** `Markdown({ body }: { body: string })`; `buildArticleJsonLd(post: PostDetail)`; route exports `revalidate = 3600`, `generateStaticParams`, `generateMetadata` (canonical `/writing/${slug}`, og `article`), default page with `<script type="application/ld+json">`.

- [ ] Add `esbuild: { jsx: "automatic" }` to vitest config.
- [ ] Failing tests (`renderToStaticMarkup`): `test_markdown_renders_gfm_table`, `test_markdown_script_tag_is_text` (no `<script` element in output; text visible escaped), `test_markdown_img_onerror_not_rendered`, `test_markdown_javascript_href_stripped`; `buildArticleJsonLd` has `@type: "Article"`, url `${BASE}/writing/slug`, headline.
- [ ] Implement component, jsonld builder, page (`notFound()` on fetch error; tags `[CACHE_TAGS.posts]`; no `cookies()`), sitemap entries for internal posts with `lastModified: updated_at`.
- [ ] `npm run lint && npm test` PASS. Commit `feat(frontend): /writing/[slug] native article page (E03-W2)`.

### Task 8: Admin form [Task 5]

**Files:** `admin/src/routes/posts/PostForm.tsx`, `PostList.tsx` (platform label, tolerate null url).

- [ ] When `platform === "internal"`: hide URL; show slug input (auto-suggest from title until user edits, kebab-case, editable) and markdown `Textarea` with live preview pane (admin has no markdown lib; preview renders via a small safe renderer — see Decision below), validation mirrors rules; send `slug`/`body`, `url: null`; map 422 `detail` arrays (loc -> field) into field errors; select option `internal` -> "Native article".
- [ ] Preview decision: add dependency `react-markdown` + `remark-gfm` + `rehype-sanitize` to admin (same versions as frontend) so preview matches the site.
- [ ] `npm run lint && npm run build` PASS; run `react-doctor` skill; Commit `feat(admin): internal post editor (E03-W2)`.

### Task 9: Playwright journey + local E2E [Tasks 6-8]

- [ ] `tests/journeys/writing.spec.ts`: themed page -> click internal card -> URL `/writing/<slug>` and h1 visible -> `goBack` -> themed page. Run with backend 24781 + frontend 24731 via a scratch config (repo config pins 24730).
- [ ] `npm run build` against backend 24781 with a published internal post; capture `/writing/[slug]` route-table line (must be `●`/`○`, not `ƒ`).
- [ ] Local admin->site check (create/publish via API, view page). Stop servers.

### Task 10: Docs + verification [all]

- [ ] Update `docs/features/posts.md` (purpose, API table, schema, invariants, files), SPEC checkboxes + Status "Done (local)".
- [ ] `superpowers:verification-before-completion`: re-run all four app checks, migration up/down/up, `alembic heads`.
- [ ] Commit `docs(posts): native articles (E03-W2)`.

## Spec edge case -> test map

| Spec edge case | Test |
|---|---|
| Migration enum committed before CHECK | Task 1 manual `upgrade head` on scratch DB (+ DB CHECK tests) |
| Downgrade drops column/constraint, enum stays | Task 1 manual down/up |
| Slug collision -> 422 `slug already exists`, lowercase | Task 3 `test_slug_collision_*` |
| internal -> external requires url; body kept, not served | Task 3 `test_patch_internal_to_external_*` |
| Unpublished/scheduled -> 404 + not in sitemap | Task 4 `test_slug_endpoint_404_*`; sitemap uses public `GET /posts` which applies `public_filter` (covered by `test_public_list_excludes_drafts`) |
| Raw HTML / script renders as text | Task 7 `test_markdown_script_tag_is_text` |
| Several collections -> each page | Task 4 `test_internal_post_in_multiple_collections_on_each_page` |
| Body > 100 KB -> 422 | Task 2 + Task 3 `test_oversize_body_422` |
| Relevance/audience unchanged | Task 4 `test_internal_post_tags_and_audience_override_returned` |
| CHECK rules | Task 1 DB tests, Task 3 API tests |
| List excludes body; slug endpoint body only for published internal | Task 4 |
| Card link split | Task 6 `postLink.test.ts` |
| `/writing/[slug]` static/ISR | Task 9 build route table |
| Playwright journey | Task 9 |
