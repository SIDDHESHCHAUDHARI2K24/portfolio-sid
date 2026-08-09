# Handoff Directory

Runtime artifacts that support execution across sessions and between human/agent work.

| File | Purpose |
|---|---|
| `env-vars-registry.md` | Every env var per service, where it lives (Railway / GitHub env secret / local .env / public), which To-Do consumes it |
| `manual-checklists.md` | Step checklists for user-executed infra To-Dos (TD-M1..M6): Cloudflare, R2, Turnstile, Resend, Railway, Tunnel/Access |
| `content-authoring-checklist.md` | P3.T6.S6 content population checklist |
| `restore-procedure.md` | Postgres backup restore drill procedure (TD-36 / gap G12) |
| `HANDOFF-SESSION-N.md` | Per-session state transfer: done/in-progress/blocked, decisions taken, next actions |

Rules: no secrets in these files (references only, e.g. `R2_ACCESS_KEY_ID → Railway backend env`). Session handoffs are written at every session end.
