# Changelog

## Unreleased — publication hardening
- Pass GitHub Action and workflow inputs through environment variables and validate paths, enums, and booleans before executing evaluator tasks.
- Pin third-party GitHub Actions to reviewed immutable commit SHAs and add Dependabot update PRs for GitHub Actions and Python packages.
- Require a real, committed evaluation-contract lock in contract/release assurance workflows instead of silently skipping verification.
- Keep generated contract-lock metadata portable; do not include the maintainer machine's absolute repository path.
- Guard automatic PR comments so the action does not attempt writes against fork PRs with read-only tokens.
- Preserve sanitized local before/after evidence while explicitly separating local reproduction from upstream maintainer validation and adoption.

## 0.8.0 — Evaluation-contract lock and frozen-candidate attribution
- Add persistent `graderprobe.lock.json` evaluation-contract snapshots.
- Add `graderprobe lock` and `graderprobe verify-lock` maintainer commands.
- Add frozen-candidate causal attribution and cohort schema.
- Add evaluator-drift vs candidate-drift classification.
- Add contract-lock and causal-attribution GitHub workflow integration.
- Add Stage 8 release-readiness, program-fit, and grant-readiness documentation.

## 0.7.1 — Release assurance hardening
- Let optional Codex CLI maintainer review use the installed CLI default unless `GRADERPROBE_CODEX_MODEL` is explicitly set; this avoids assuming a model ID is available to every maintainer.
- Add explicit executed-check and check-gap reporting.
- Audit newly added tasks head-only instead of skipping them.
- Add release SARIF metadata and GitHub PR summary integration.
- Add release report schema validation and safe Git-archive extraction.
- Add an optional Codex CLI maintainer-review script and API-credit usage plan.
- Harden local evaluator capture with file-backed stdout/stderr to avoid pipe stalls and preserve hard wall-clock timeouts.

## 0.7.0 — Change assurance
- Add Git-aware release assurance, cross-revision probe replay, release fingerprints, and optional semantic change review.
- Validate newly added tasks head-only instead of silently skipping them.
- Add release SARIF 2.1.0 export and GitHub Code Scanning upload workflow.
- Record deleted-task changes, probe-set deltas, head findings, and API usage in release artifacts.
- Harden base-tree extraction to avoid unsafe tar member types and deprecation warnings.


## 0.6.1

- Removed placeholder repository URLs from SARIF metadata.
- Bumped patch version after release hardening review.
- Updated release self-review and stale version-sensitive tests.

## 0.6.0

- Added changed-task Git auditing for maintainer workflows.
- Added SARIF 2.1.0 export for GitHub code-scanning integrations.
- Added optional bounded OpenAI Responses API semantic probe provider using Structured Outputs.
- Preserved model-generated probe specifications in replay manifests.
- Added Harbor task-package inspection and a license-clean fixture.
- Added maintainer-oriented API usage documentation and semantic audit workflow.

## 0.5.0

- Added process-wide execution concurrency governor.
- Replaced POSIX `preexec_fn` resource limits with an executable limit trampoline.
- Added safe accelerated workspace copy path with symlink pre-scan.
- Added output/contract execution digests and replay bundles.
- Added baseline output-drift diagnostics and `graderprobe replay`.

## 0.4.0

- Added optional Docker-backed evaluator execution with documented isolation controls.
- Added bounded task-level parallelism to `graderprobe audit`.
- Added scoped memoization for expensive minimization loops.
- Hardened hashing so symlinks are not dereferenced.
- Hardened the SWE-bench-style adapter against missing evaluator commands.

## 0.3.0

- Added targeted AST-aware comparison and literal probes.
- Added automatic AST-aware sensitivity/invariance candidates.
- Added parallel probe execution with deterministic result ordering.
- Added hierarchical, cached counterfactual minimization.

## 0.2.0

- Added optional independent behavior validation and evidence levels.
- Added deterministic auto sensitivity probes with validation gating.
- Added budgeted diff-hunk counterfactual minimization.
- Added recursive audit CLI.

## 0.1.1

- Hardened workspace path containment and symlink handling.
- Treated known-invalid fixtures as observable controls rather than baseline gates.
- Added explicit evaluator verdict protocols.
- Terminated POSIX evaluator process groups on timeout.
- Enforced task JSON-schema validation at load time.
- Propagated explicit secret-inheritance configuration.

## 0.1.0 — 2026-10-04

Initial project snapshot.
