# Final publication checklist — 2026-10-10

This is the authoritative publication checklist for the current source snapshot. Historical phase reports are retained for traceability; they do not override this document.

## Source status

- Python package and project source are present. The source ZIP intentionally has no `.git` directory.
- Composite Action inputs are passed as environment values rather than injected into shell/JavaScript source. Task/output paths are checked against `GITHUB_WORKSPACE`.
- Third-party GitHub Actions are pinned to full commit SHAs; regression tests enforce this. Dependabot is configured for weekly GitHub Actions and pip updates.
- Automatic PR comments are restricted to same-repository PRs. Contract/release assurance fails if the lock is missing.
- Lock metadata uses `repository: "."` rather than an absolute path.
- Sanitized Phase 5 evidence and its SHA-256 manifest are retained. Other cases are labelled according to their actual validation status.
- Local-only Antigravity instructions are kept in the separate delivery bundle and are not part of the public source tree.

## Current verification record

See `docs/FINAL_AUDIT_REPORT.md` for per-module test results, wheel build details, the release-gate pass, and the known timeout on the complete demo-corpus test in this audit container. Do not claim an uninterrupted full-suite pass for this exact snapshot until Antigravity verifies it in Windows/CI.

## Required before public push

1. Preserve current `.git` and create a backup branch before copying this project snapshot into the existing working tree.
2. Inspect Git authors/emails. Do not publish the owner's personal email; preserve old refs locally and use GitHub's no-reply identity for new public commits where needed.
3. Run the full test suite, offline demo, YAML/shell checks, and secret/path scans in the real Windows checkout. Document exact pass/skip/fail counts.
4. Create a clean release commit. Do not include local ZIPs, environments, credentials or archived private reports.
5. Generate the real lock in that clean repository using `graderprobe lock . --task-root corpus/tasks --out graderprobe.lock.json --anchors 2`; commit the resulting lock and run `graderprobe verify-lock . --lock graderprobe.lock.json --workers 1 --execution-slots 1`. Never fabricate the lock in a source ZIP.
6. Inspect remote refs before push. If the remote is not empty, use a safe release branch and PR; never force-push or overwrite existing content.
7. Verify public access and the exact remote commit hash while logged out.
8. Recheck DeepEval PR #3339 live. Post one factual technical comment only if it remains open/relevant and the public evidence link works; otherwise record why not.
9. Refresh the application draft and official form/terms. Do not invent adoption, endorsement, download counts, maintainer role, identity, or selection odds. The application is not submitted until the form confirms it.

## Not established

No broad adoption, third-party maintainer validation, external CI usage, OpenAI endorsement, or 30%+ selection probability is established by the current evidence. API-credit benefits and the separate maximum grant are not guaranteed.
