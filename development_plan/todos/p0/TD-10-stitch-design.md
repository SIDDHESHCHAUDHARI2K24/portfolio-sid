# TD-10: Stitch MCP (Env Expansion) + DESIGN.md Export

**Phase:** P0 · **Wave:** 3 · **Executor:** paired (user: key + design direction; agent: config + export) · **Effort:** M (half day)
**Source:** development-plan-P0.md → P0.T4.S6, P0.T5.S1
**Depends on:** TD-00 · **Blocks:** TD-11

## Purpose
Design generation from inside the coding agents without ever committing the
API key, plus the DESIGN.md artifact that TD-11 turns into tokens. Stitch's
HTML export is deliberately NOT imported — it would be discarded in the
Phase 3 re-skin.

## Paths
- Create: `.mcp.json` (committed, env expansion), `docs/DESIGN.md`
- Reference: local gitignored `.env` holding `STITCH_API_KEY` (already present — never write the value anywhere)

## Steps
1. User: confirm `STITCH_API_KEY` exists in the local gitignored `.env` (it does); never paste the value into any file, chat, or commit
2. Agent: at execution time fetch the official setup page — https://stitch.withgoogle.com/docs/mcp/setup/ — and follow its invocation exactly
3. Write `.mcp.json` referencing `${STITCH_API_KEY}` (env expansion), never the literal. Fallbacks if the official form fails, in order: `@google/stitch-mcp` npx server → `@_davideast/stitch-mcp proxy` → direct HTTP transport to `stitch.googleapis.com/mcp` with an `X-Goog-Api-Key` header (per P0.T4.S6)
4. Restart the agent session — MCP servers load at session start — and confirm Stitch tools are listed
5. User + agent: generate a dark-themed design pass covering the tile grid and one content page — enough to fix tokens without committing to layouts Phase 3 will revisit
6. Export Stitch's `DESIGN.md` to `docs/DESIGN.md` (colour tokens, typography scale, spacing, component rules)
7. OPTIONAL, only if setup is cheap: openpencil (github.com/open-pencil/open-pencil) as a design-enhancement pass after the Stitch export
8. Reject any impulse to import Stitch HTML into the apps

## Tests
- `git log -p .mcp.json` shows no key was ever committed
- `.mcp.json` contains only the `${STITCH_API_KEY}` expansion
- Agent lists Stitch tools after restart

## Acceptance Criteria
- [ ] `.mcp.json` committed, contains no secret, uses `${STITCH_API_KEY}`
- [ ] Agent lists Stitch tools after restart
- [ ] `docs/DESIGN.md` present with colour, typography, and spacing tokens
- [ ] Dark palette only — no light-mode tokens
- [ ] No Stitch HTML imported into any app

## Verify
`git log -p .mcp.json && grep -c "STITCH_API_KEY" .mcp.json && ls docs/DESIGN.md`

## Commit
`chore: Stitch MCP config (env expansion) + DESIGN.md dark design pass`

## Invariants
- The key value never enters git, docs, or chat — `.env` only, gitignored
- DESIGN.md is the import artifact; the HTML export is throwaway until Phase 3
- Dark theme only, single palette — a light mode nobody wants doubles the token surface
