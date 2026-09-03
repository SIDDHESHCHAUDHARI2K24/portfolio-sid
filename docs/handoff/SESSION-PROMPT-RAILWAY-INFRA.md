# Session Prompt — Railway Infra & Hosting (Cloudflare-removal follow-up)

> Copy everything below the line into a new session.

---

You are continuing the Cloudflare-removal project `portfolio-sid` (Next.js public site + Vite admin SPA + FastAPI backend + Postgres, being moved off all Cloudflare *services* to Railway, keeping `siddhesh-chaudhari.com` at Cloudflare as registrar+DNS only).

The CODE phase is DONE and verified (Turnstile removed → honeypot+rate-limit; R2 → backend `/media` + Railway Volume; CF analytics → env-gated Umami; API now returns full `file_url`/`icon_url`). **Do not re-implement any code changes.** Your job now is the INFRA & HOSTING phase.

## Required reading first (authoritative)
- `docs/handoff/HANDOFF-CLOUDFLARE-REMOVAL-PLAN.md` — the locked decision + code edit map.
- `docs/handoff/HANDOFF-RAILWAY-INFRA-PLAN.md` — status (code done) + per-task plan, agent/user split, verify commands. THIS is your task list.
- `docs/handoff/env-vars-registry.md` — the target env-var shape (record locations only, never values).
- `docs/conventions.md` — you MUST preserve invariants: **#13** `NEXT_PUBLIC_INDEXABLE` stays `false` until launch; **#14** `CORS_ALLOW_ORIGINS` empty in prod; **#15** no secrets in git/logs/responses.

## Workflow (follow the sub-agent loop for each task)
1. **Brainstorm** — before acting on a task, check for gaps. Small gaps with data available: make the call and state it. Big gaps: STOP and ask me.
2. **Plan** — restate acceptance criteria, agent vs user steps, dependency/order, verify commands.
3. **Execute** — do agent steps (code/CLI); when a step needs a dashboard/account/secret *value*, **PAUSE and ask me** (do not invent secrets). Use sub-agents for parallelizable work, respecting dependencies.
4. **Verify** — run the task's Verify commands; report **PASS/FAIL** explicitly. Do NOT advance until acceptance criteria are met.
5. **Record** — write ONLY locations into `env-vars-registry.md` (no values). Note backup policy in `conventions.md` where required.
6. **Commit** — conventional (`feat`/`fix`/`chore`); docs-only changes get `doc:` commits; **never commit secrets**; stage only intended files (there is unrelated uncommitted work in the repo — leave it alone).

## Execution order (do not reorder)
TD-M2 → TD-M3 → TD-M4 → TD-M5 → TD-M6 → TD-36 (partial) → prepare-for-hosting → **(only then)** UI TD-34 / TD-35 → host on Railway.
**Hard rule: do NOT start TD-34/TD-35 until infra + prepare-for-hosting are complete.**

## For each task, structure as:
- **Agent:** steps you can do (Railway CLI, code, setting non-secret env).
- **User (PAUSE):** dashboard/account actions and secret *values* — Resend verify, Railway Volume attach, SESSION_SECRET / ADMIN_PASSWORD_HASH / RESEND_API_KEY / REVALIDATION_SECRET / RAILWAY_TOKEN / GLITCHTIP_DSN generation, Cloudflare DNS record edits, custom-domain cutover.
- **Verify:** the exact commands from the handoff (e.g. `dig +short admin.siddhesh-chaudhari.com`, `curl $BACKEND/health` → `{"status":"ok"}`, `bash scripts/check_ssr.sh $FRONTEND`, `curl -sI https://admin.siddhesh-chaudhari.com` → SPA).
- **Report:** PASS/FAIL before moving on.

## Open decisions to raise when reached
- **Umami hosting:** self-host as a separate Railway service + DB, or elsewhere? Needed before final `NEXT_PUBLIC_UMAMI_SRC`/`_WEBSITE_ID`.
- **Postgres backup policy** text for `conventions.md`.
- **Restore drill** runbook (`restore-procedure.md`) creation if missing.

Start by reading the four docs above, then propose your plan for **TD-M2** (Railway Volume + `STORAGE_KIND=local`) and PAUSE for my Volume-attach + secret steps.
