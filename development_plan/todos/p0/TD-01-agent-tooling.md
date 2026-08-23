# TD-01: Agent Tooling — Graphify, CodeGraph, Superpowers

**Phase:** P0 · **Wave:** 0 · **Executor:** agent · **Effort:** M (half day)
**Source:** development-plan-P0.md → P0.T4.S3, P0.T4.S4 (+ master-index fixed tooling facts)
**Depends on:** TD-00 · **Blocks:** TD-12 (codegraph-scoped tests), all agent-driven work

## Purpose
Wire the coding agents (opencode, Claude Code, Codex CLI, cursor-agent —
no blackbox-cli) into a shared tooling baseline: graphify
skills, CodeGraph symbol/call-graph index, and superpowers disciplined-workflow
skills. Every later agent task inherits this environment.

## Paths
- Modify: agent config dirs for opencode, Claude Code, Codex CLI, cursor-agent
- Create: `.codegraph/` index at repo root (gitignored by TD-00)
- Reference: opencode skills config (superpowers already present there)

## Steps
1. Detect agents: `command -v opencode claude codex cursor-agent` — expect all four; stop and report any missing
2. graphify CLI is already installed: run `graphify install --project` for the opencode, Claude Code, and Codex platforms
3. CodeGraph (1.5.0 already installed): run `codegraph install` at repo root — it auto-detects Claude Code, Cursor, Codex CLI, and opencode
4. `codegraph init` at repo root to build the index; `codegraph telemetry off`
5. Confirm `.codegraph/` is gitignored (landed in TD-00): `git check-ignore -v .codegraph/`
6. Superpowers: already available in opencode; install for Claude Code and Codex CLI per the README at `github.com/obra/superpowers`
7. Open a new terminal / restart each agent session so tool registrations load

## Tests
- `codegraph status` reports a populated index
- Each of the four agents lists a `codegraph_explore` tool
- Superpowers skills discoverable in Claude Code and Codex; invoking the TDD skill yields its RED-GREEN-REFACTOR workflow
- graphify skill loads in opencode, Claude Code, and Codex

## Acceptance Criteria
- [ ] `graphify install --project` done for opencode/claude/codex platforms
- [ ] `codegraph status` populated; `codegraph_explore` visible in all four agents
- [ ] `.codegraph/` gitignored; telemetry off
- [ ] superpowers installed for Claude Code + Codex (opencode already has it)

## Verify
`codegraph status && git check-ignore -v .codegraph/`

## Commit
`chore: agent tooling — graphify, codegraph, superpowers`

## Invariants
- CodeGraph recognises FastAPI routes (backend: full value) but NOT Next.js App
  Router routes — frontend indexing is symbol/call-graph only, no route nodes
- WSL2 + repo on a Windows drive (`/mnt/c`) causes SQLite locking — recorded
  caveat, N/A on this macOS setup; keep the repo on the native FS if ever on WSL2
- Never hand-edit inside tool-managed marker fences in CLAUDE.md/AGENTS.md (TD-02)
