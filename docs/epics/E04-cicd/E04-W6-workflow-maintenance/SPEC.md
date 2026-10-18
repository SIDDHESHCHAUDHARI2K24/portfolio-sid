# E04-W6: Action version bumps; `react-doctor.yml` decision

**Epic:** E04 CI/CD hardening · **Ticket:** E04-W6 · **Depends on:** none

## Purpose

Workflows pin older action majors that run on deprecated Node runtimes. `react-doctor.yml` sits untracked in the repo, so it neither runs nor goes away.

## Goal

Every action is on its current major. `react-doctor.yml` is either committed in a form that does not slow gated deploys, or deleted.

## Reference files

- `.github/workflows/ci.yml`, `e2e.yml`, `deploy.yml`
- `.github/workflows/react-doctor.yml` (untracked), `doctor.config.ts` (untracked)
- `.claude/skills/react-doctor/` (untracked; out of scope)

## Functionality

- Bump `actions/checkout`, `actions/setup-node`, `astral-sh/setup-uv`, `actions/upload-artifact` to their latest major, checked on each action's releases page at implementation time. Read each changelog for breaking inputs (e.g. `setup-uv` cache defaults, `upload-artifact` hidden-file rules).
- Bump the pinned Railway CLI in `deploy.yml` only if the current pin fails; otherwise leave it.
- `react-doctor.yml` (decided by the user 2026-10-18: the recommended option):
  - commit it advisory-only (no `blocking`);
  - trigger on `pull_request` only, dropping `push: main`, so W3's gate never waits on it;
  - pin the action and the `version` input instead of `latest`;
  - commit `doctor.config.ts` with it if the workflow reads it.

## Edge cases

- `upload-artifact` major bumps change artifact naming rules; the E2E trace upload has a single fixed name, so it is safe, but verify.
- `react-doctor` needs `pull-requests: write`; on fork pull requests the token is read-only and the comment step is skipped. Acceptable.

## Testing

- The epic pull request runs every workflow green on the new majors, with no deprecation warnings in the run annotations.
- If kept, react-doctor posts its summary comment on the epic pull request.

## Acceptance criteria

- [ ] No workflow uses a deprecated action major; runs show no Node deprecation annotations.
- [x] `react-doctor.yml` is committed: pull-request only, pinned, advisory.
- [ ] CI and E2E pass on the epic pull request.

## Rollback

Revert the commit.
