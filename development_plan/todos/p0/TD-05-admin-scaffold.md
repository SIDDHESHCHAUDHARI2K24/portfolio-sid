# TD-05: Admin SPA Scaffold (Vite + React + TS)

**Phase:** P0 · **Wave:** 1 · **Executor:** agent · **Effort:** M (4 hrs)
**Source:** development-plan-P0.md → P0.T3.S6
**Depends on:** TD-00 · **Blocks:** TD-09, TD-11

## Purpose
Deliberately not Next.js: no SEO requirement, no SSR benefit, faster builds.
The admin SPA is served by FastAPI from the same origin in production
(TD-09); the dev server proxies `/api` to mirror that arrangement.

## Paths
- Create: `admin/` (Vite react-ts template), admin shell under `admin/src/`
- Modify: `admin/vite.config.ts` (dev proxy), `admin/package.json` (deps)

## Steps
1. `npm create vite@latest admin -- --template react-ts`
2. `npm i react-router-dom @tanstack/react-query`
3. `npx shadcn@latest init` — consume the same token variable names as frontend (real values land in TD-11)
4. `vite.config.ts`: dev server proxy `/api` → `http://localhost:8000`, so development matches production's same-origin arrangement as closely as possible
5. React Router shell with a placeholder route; TanStack QueryClientProvider wired at the root
6. Confirm build output lands at `admin/dist`
7. With the TD-03 backend running: `npm run dev`, confirm a proxied `/api` call reaches localhost:8000

## Tests
- `npm run dev` serves the shell; fetch to `/api/health` (proxied) returns the backend health payload
- `npm run build` emits `admin/dist/index.html`

## Acceptance Criteria
- [ ] `npm run dev` serves the admin shell and proxies API calls to the backend
- [ ] `npm run build` emits to `admin/dist`
- [ ] shadcn initialised with the same token variable names as frontend

## Verify
`cd admin && npm run build && ls dist/index.html`

## Commit
`feat(admin): Vite+React scaffold — router, TanStack Query, dev proxy`

## Invariants
- Dev is cross-origin, production same-origin — the one deliberate divergence;
  CORS_ALLOW_ORIGINS handles dev and must be empty in production
- Admin SPA + API share ONE hostname in production (admin.siddhesh-chaudhari.com)
- Same tokens as frontend; no hardcoded colours (TD-11)
