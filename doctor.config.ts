// React Doctor configuration — https://www.react.doctor/ci
// Mirrors the invariant in docs/conventions.md #14: React-only coverage; the
// backend's quality is ruff/mypy's job (CI). react-doctor is diff-scoped on PRs
// (the GitHub Action posts findings, never red-Xing on pre-existing backlog).
//
// Advisory: findings are reported, never failing the check (E04 decision).
const config = {
  blocking: "none",
  // On PRs the Action scans only changed files vs the merge base (scope=changed).
  // Locally, `npx react-doctor .` uses this default and never exits non-zero (blocking: none).
  scope: "changed",
  base: "main",
};

export default config;
