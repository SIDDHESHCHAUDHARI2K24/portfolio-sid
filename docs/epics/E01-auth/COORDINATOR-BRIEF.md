# Coordinator 1 Brief — Epic E01: Auth System

You are **Coordinator 1**, an independent Claude Code session. The user works with you directly and will give you the detailed requirements. The orchestrator session that spawned you only set this up.

## Background

The system is deployed and working in production (Next.js public site, Vite admin SPA, FastAPI backend, Postgres, R2, Railway, Cloudflare). Source of truth is `docs/`; `docs/conventions.md` is the architectural contract and must never be violated. Related material:

- `docs/features/auth.md`: auth feature doc
- `docs/specs/email-provider/`: email provider spec
- `docs/handoff/HANDOFF-2026-09-03-STEADY-STATE.md`: latest steady-state handoff
- `docs/handoff/env-vars-registry.md`: env vars
- `LOCAL.md`: local run notes

For codebase questions, run `graphify query "<question>"` first. After code changes, run `graphify update .`.

## Epic goal

The user reports that **email OTP is not working** in the deployed system. The scope is the **entire auth system**: OTP issue and verify, email provider delivery, sessions, tokens and cookies, admin vs. public auth, rate limiting, env vars, and CORS and cookie domains across Railway and Cloudflare.

## Deliverables

1. **Diagnosis.** Diagnose the OTP failure with evidence-ranked hypotheses and no guessed fixes. If confirming one needs production logs, dashboards or secrets, tell the user exactly what to check. Never print secrets.
2. **Epic plan.** Write `docs/epics/E01-auth/EPIC.md` covering goal, scope, non-goals, findings, the ordered work-item list with dependencies, acceptance criteria, and the verification plan.
3. **Work-item specs.** Write one `docs/epics/E01-auth/WI-NN-<slug>.md` per work item, covering problem, evidence, design, files touched, test plan, acceptance criteria, and rollback.
4. **AGENTS.md conventions.** Improve `AGENTS.md` (and the root `CLAUDE.md` that mirrors it) so agents can work autonomously. Cover the epic and work-item workflow, where specs live, definition of done, test and verification commands per app, branch and commit rules, handoff updates, and when to stop and ask. Agree the changes with the user first.
5. **Execution.** Carry out the work items once the user approves the plan.

## Constraints

- Don't take any production-affecting action (deploys, prod DB writes, env changes, pushes) without the user's explicit approval.
- The working tree has an unrelated uncommitted change in `backend/app/features/contact/service.py` and untracked files (`.agents/`, `.openhands/`, `LOCAL.md`, `resumes/`, `doctor.config.ts`, `.github/workflows/react-doctor.yml`, `.claude/skills/react-doctor/`). Do not touch, revert or commit them.
- Write docs in normal prose.

## Transcript archiving

Your session transcript must be preserved. Claude Code writes it as JSONL under `~/.claude/projects/-Users-siddheshc2001gmail-com-Coding-Projects-Portfolio/<session-id>.jsonl`, and retention there is set to 3650 days. You also keep a copy in the epic folder:

- At each milestone (plan approved, each work item done, epic closed), copy your current session's JSONL to `docs/epics/E01-auth/transcripts/coordinator-1-<session-id>.jsonl`, overwriting the previous copy. To find your session, take the newest `.jsonl` in that directory that contains the phrase `COORDINATOR-BRIEF.md`.
- `docs/epics/*/transcripts/` is gitignored because transcripts may contain sensitive output. Never commit transcripts.
- Record the session id in `EPIC.md` under a "Sessions" heading.

## Start

Do a quick orientation on the auth system and OTP flow. Then give the user a short summary and ask for their detailed requirements before you finalize the plan.
