# portfolio-sid — Agent Guide

## Workspace boundary (read first)

- **`Portfolio/` is the project root.** Every file an agent creates, edits, or leaves behind stays inside it. Never write outside it: no sibling folders, no system temp dirs, no backups elsewhere.
- **Worktrees** go in `Portfolio/.worktrees/<epic-or-ticket>/` (gitignored), never `../`. Remove them when the work is merged.
- **Epic docs** must be visible at `Portfolio/docs/epics/<epic>/`. When an epic is built in a worktree, symlink that path to the worktree's `docs/epics/<epic>` and remove the symlink before the main checkout pulls the merged epic.
- **Scratch files**, logs and local scripts go in a gitignored folder inside the worktree (e.g. `.preview/`), never in the main checkout's tracked paths.
- **Local databases and processes** must use this project's ports (`247xx`, see `docs/epics/E01-auth/E01-W7-local-nonstandard-ports/SPEC.md`). Drop throwaway databases and stop processes you started.

## Stack

- **Public site:** Next.js (`frontend/`), SSR/ISR, Railway service `frontend`; rewrites `/api` to the private backend.
- **Admin:** Vite + React SPA (`admin/`), served by nginx on Railway service `admin` (`admin.siddhesh-chaudhari.com`), proxying `/api` and `/media` to the backend.
- **Backend:** FastAPI (`backend/app/`), feature slices in `backend/app/features/<name>/`, shared code in `backend/app/core/`; Railway service `backend`, private network only.
- **Data:** Postgres behind pgbouncer (Railway); Alembic migrations in `backend/alembic/`.
- **Media:** S3-compatible storage (MinIO locally).
- **Email:** Resend (`backend/app/core/email.py`).
- **Jobs:** Railway service `cron` (same backend image, scheduled tasks).
- **DNS:** Cloudflare (registrar and DNS only).
- **Deploys:** a push to `main` triggers Railway's native deploy of every service. Pushing to `main` is deploying to production.

## Where things live

- **Architectural contract:** `docs/conventions.md`. Never violate its invariants; changing one needs user approval.
- **System design:** `docs/tech-stack-analysis.md`, `docs/dependency-map.md`, `docs/DESIGN.md` (UI tokens), `docs/DEPLOYMENT.md`.
- **Per-feature docs:** `docs/features/<feature>.md` (purpose, API, data flow, invariants, files). Update the doc in the same change as the code.
- **Specs:** `docs/specs/`. Historical plans: `docs/development-plan-P*.md`, `development_plan/todos/`.
- **Epics:** `docs/epics/E<nn>-<slug>/EPIC.md`. Work items: `docs/epics/E<nn>-<slug>/E<nn>-W<n>-<ticket_name>/SPEC.md`.
- **Operations:** `docs/handoff/` (latest steady-state handoff, `env-vars-registry.md`, `restore-procedure.md`). Local run: `LOCAL.md`.

## Code navigation

Use CodeGraph before grep or reading files: the `codegraph_explore` MCP tool, or `codegraph explore "<symbols or question>"` in the shell. Name a file or symbol to get its current source and call paths. Fall back to grep only for literals and config.

## Roles

**Orchestrator**
- Spins up each coordinator as an independent session, so every coordinator keeps its own transcript.
- Assigns work as a whole epic or part of one, sized to fit a coordinator's context.
- Receives product questions from coordinators and answers them or escalates to the user.
- Token ceiling: 400K–450K. Before reaching it, while coordinators are running, it starts a new orchestrator with a handoff covering:
  - running coordinators (session ID, epic, current work item, status);
  - open questions;
  - decisions made.
  It then tells every coordinator that the new orchestrator is taking over.

**Coordinator**
- The executing layer: brainstorming, planning, spec writing, implementation, verification for its epic.
- Decides per task whether to use sub-agents and prefers them. Sub-agents run in the foreground, never in the background.
- Routes product questions and decisions to the orchestrator, with context and a recommendation.
- At 350K–450K context, asks the orchestrator for a replacement coordinator and writes a handoff:
  - done and pending work items;
  - branch state;
  - open issues;
  - next step.
- Transcript: at each milestone (plan approved, each work item done, epic closed), copies its session JSONL to `docs/epics/<epic>/transcripts/` (gitignored, never committed) and records the session ID under "Sessions" in `EPIC.md`.

**Sub-agent models**

| Task | Model |
|---|---|
| Easy (lookups, mechanical edits, single-file changes) | Haiku 5.5 |
| Medium (a feature slice with a clear spec) | Sonnet 5.5, medium effort |
| Hard (cross-cutting, security, unclear root cause) | Sonnet 5.5, high or xhigh effort |
| Retry after a failure | Opus 5.5 |

A sub-agent failure that is not a context limit means it could not solve the task. The coordinator then stops, gets the issue checked, brainstorms, plans, and spins a new sub-agent on Opus 5.5.

## Task loop (every task)

Use `superpowers:using-superpowers` to pick the right skill at each stage. Use the `react-doctor` skill for any frontend or admin change.

1. **Brainstorm.** Find gaps. Decide small gaps where data exists, and state each decision explicitly. Ask (via the orchestrator) on big gaps.
2. **Plan.** Cover why, what, where, tests and acceptance criteria, and order and dependencies.
3. **Execute.** Split the work into sub-agent tasks along the dependency map. Run in parallel only what is truly independent.
4. **Code.** Implement with tests and a checklist. If the same error appears three times, stop and run `superpowers:systematic-debugging`, then have a sub-agent brainstorm and plan the fix.
5. **Test.** Run every test and acceptance criterion in the spec, add missing tests, and run lint and type checks.
6. **Code review.** Review the code and test results for errors and logic issues (`superpowers:requesting-code-review`).
7. **Verify.** Check every spec item is delivered (`superpowers:verification-before-completion`). Send any gap back into the loop.
8. **Commit.**

## Epic and work-item workflow

1. The coordinator orients itself, diagnoses with evidence, and writes `EPIC.md`: goal, scope, non-goals, findings, work items with dependencies, acceptance criteria, verification plan, sessions.
2. One folder and `SPEC.md` per work item, kept short. Sections: epic and ticket number, ticket name, purpose, goal, reference files, functionality, edge cases, testing, acceptance criteria, rollback.
3. User approval of the plan comes before any code.
4. Run the task loop per work item. Tick the spec checkboxes and update `EPIC.md` status when done.
5. Close the epic: every acceptance criterion is checked, the docs are synced, and the handoff is updated.

## Definition of done

- Every spec acceptance criterion is checked off, with evidence.
- Tests, lint, and type checks pass for every touched app (commands below).
- `docs/features/*.md`, `docs/handoff/env-vars-registry.md`, and the steady-state handoff in `docs/handoff/` reflect the change.
- If an API schema changed, `backend/openapi.json` is regenerated, along with `admin/src/api.d.ts` and `frontend/src/api.d.ts`.
- No secrets in code, logs, docs, or commits.

## Commands

| App | Checks |
|---|---|
| Backend (`backend/`) | `uv run ruff check . && uv run mypy app && uv run pytest -q` (needs local Postgres per `LOCAL.md`) |
| Backend OpenAPI | `uv run python scripts/export_openapi.py`, then `npm run openapi:generate` in `admin/` and `frontend/` |
| Admin (`admin/`) | `npm run lint && npm run build` |
| Frontend (`frontend/`) | `npm run lint && npm test && npm run build` |
| Local stack | see `LOCAL.md` |

## Git

- One branch per epic, `epic/E<nn>-<slug>`, cut from `main`.
- One conventional commit per work item, e.g. `fix(auth): ... (E01-W2)`.
- Stage only the files the work item touched. Never commit, revert, or stage unrelated dirty or untracked files.
- Never commit transcripts, `.env` files, or secrets.
- Merging or pushing to `main` deploys production, so it needs explicit user approval each time.

## Stop and ask

Ask before:
- Any production action: deploy, push to `main`, env var change, production DB read or write, DNS change.
- Changing a `docs/conventions.md` or feature-doc invariant.
- Making a product decision or building beyond the spec.
- Continuing when a spec is ambiguous or contradicts the code.
- Continuing after the same failure persists through the Opus retry.

When asking, state the question, context, options, and a recommendation.

<!-- CODEGRAPH_START -->
## CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- **MCP tool** (when available): `codegraph_explore` answers most code questions in one call — the relevant symbols' verbatim source plus the call paths between them, including dynamic-dispatch hops grep can't follow. Name a file or symbol in the query to read its current line-numbered source. If it's listed but deferred, load it by name via tool search.
- **Shell** (always works): `codegraph explore "<symbol names or question>"` prints the same output.

If there is no `.codegraph/` directory, skip CodeGraph entirely — indexing is the user's decision.
<!-- CODEGRAPH_END -->
