# Public publication readiness audit

Snapshot reviewed: 2026-10-10, from the supplied clean v0.8.0 source archive.

## Fixed before publication

- The composite GitHub Action previously interpolated task/output/fail-on inputs directly into shell commands and interpolated the output directory into JavaScript source. The workflow-dispatch task input and semantic maintainer base-ref input were also embedded directly in shell code. These values are now passed through environment variables and consumed as data.
- Added `tests/test_public_workflow_input_safety.py` to guard the reviewed surfaces against regression.

## Verification and remaining limits

- Phase 5 focused regression suite: 3 tests passed in this audit environment.
- Workflow-input safety suite: run separately as part of this audit.
- The full suite did not finish in this audit environment before its execution timeout; the earlier Antigravity report records 129 passed and 3 skipped. Do not describe this independent audit run as a full-suite pass.
- The supplied archive contains no `.git` history and no remote configuration; it is a source handoff, not proof of a public release.
- Before claiming external validation or adoption, link a public repository/release and record an authorized maintainer run or external CI usage. The DeepEval before/after evidence remains a locally performed exact-revision reproduction, not maintainer endorsement.


## Final handoff audit additions (2026-10-10)

- Composite action inputs are constrained to the checked-out workspace, fail-on is allow-listed, and boolean action inputs are validated before execution.
- Workflow dispatch/task and ref inputs are passed through environment variables and validated as data rather than inserted into shell script source.
- Third-party GitHub Actions are pinned to reviewed full commit SHAs (checkout v7.0.1, setup-python v7.0.0, upload-artifact v7.0.2, CodeQL Action v4.38.3, github-script v9.0.0). Dependabot is configured to propose future updates; updates still require review and CI.
- The full deterministic test suite now runs on pull requests as well as pushes/manual runs.
- The contract-lock job no longer silently skips when `graderprobe.lock.json` is absent. The publishing agent must create a real lock from a clean committed Git state before publishing.
- Contract-lock metadata records the repository as `.` instead of a machine-specific absolute path.
- Personal email was removed from the public Phase 6 report.

Limits: Action pins must be checked and updated over time through reviewed Dependabot PRs. This source archive intentionally contains no `.git` history, so the real lockfile must be generated in the maintainer's actual Git checkout after code commits are made. The repository has not been published from this environment.
