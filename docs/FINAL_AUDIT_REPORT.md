# Final publication audit — 2026-10-10

## Result

The source package has been reviewed and strengthened for public release. This is **not** a claim that the project has been publicly published, adopted by other maintainers, or accepted by OpenAI. The code ZIP intentionally has no `.git` directory; the contract lock must be generated from the real commit in the owner’s Git checkout.

## Hardening performed

- GitHub Action values are passed through environment variables, validated before use, and task/output paths are constrained to `GITHUB_WORKSPACE`.
- The automatic PR comment is restricted to same-repository pull requests; fork PRs are not given a write path.
- Third-party GitHub Actions are pinned to full immutable commit SHAs and Dependabot is configured for weekly Actions/Python dependency updates.
- Contract-lock/release assurance now fails closed when the required committed lock is missing rather than silently skipping the gate.
- Lock metadata uses a portable repository marker instead of leaking an absolute local path.
- Historical evidence artifacts are preserved and local-machine paths were sanitized where applicable; the Phase 5 SHA-256 manifest is retained.
- The public application draft’s character counts were corrected. Claims distinguish the exact-revision local DeepEval #3338 before/after experiment from all cases still awaiting independent upstream validation.
- Owner-specific and stale Antigravity handoff instructions were removed from the public project tree. Current and historic handoff prompts are preserved in the root `instructions/` folder of the delivery package.

## Tests verified in this audit environment

Each of the following was run independently and passed:

- `test_public_workflow_input_safety.py`: 8 passed.
- `test_public_reliability.py`: 3 passed (including the bounded-smoke gate regression).
- `test_stage1_hardening.py`: 10 passed.
- `test_stage2_behavior.py`: 6 passed.
- `test_findings.py`: 6 passed.
- `test_transforms.py`: 8 passed.
- `test_task_schema.py`: 4 passed.
- `test_stage3_ast.py`: 5 passed.
- `test_stage3_runner.py`: 2 passed.
- `test_stage4_runtime.py`: 5 passed.
- `test_stage5_reproducibility.py`: 7 passed.
- `test_stage6_ecosystem.py`: 9 passed.
- All 7 test cases in `test_stage7_assurance.py` passed when the slow report-schema round-trip case was run separately; one combined invocation timed out in this environment after its first 6 passing cases.
- `test_stage8_causal_lock.py`: 5 passed.
- `test_external_cases.py`: 2 passed.
- `test_phase3_trial_bundle.py`: 3 passed.
- `test_phase3_deepeval_3025.py` and `test_phase3_trial_bundle.py`: 5 tests passed under `unittest` after converting the previously pytest-style free functions, so the primary CI discovery command runs all of them.
- `test_phase5_deepeval_3339_validation.py`: 3 passed.
- `test_self_detect.py`: 4 passed.
- `test_adapters.py`: 3 passed.
- `test_cli_and_metrics.py`: 12 passed.
- `test_execution.py`: 4 passed.
- `scripts/public_reliability_gate.sh`: **PASS** after consolidating its smoke into the same subprocess-bounded test used by the unit suite. The smoke asserted `BOUNDARY_OK`, zero findings, a replay artifact, and zero API usage.
- The wheel built successfully: `graderprobe-0.8.0-py3-none-any.whl` (SHA-256 `cbec3419c65dc7205fd436fa1e7679b3eb7b41dcc4e94f5055cd0800ff137390`).
- Workflow/action YAML parsing passed for 7 YAML files, and `bash -n` passed for 4 shell scripts plus embedded workflow run blocks. Antigravity should repeat these checks after integration.

## Remaining verification limitation

The full `test_demo_corpus.py` run exceeded the time limit in this audit container. The observed command-line run of the specific `under-constrained-auth` demo task completed successfully, but that does not substitute for the entire corpus test. A combined full-suite pass is therefore **not claimed** for this exact final snapshot. The handoff prompt directs Antigravity to run the suite in the owner’s Windows environment and in GitHub Actions, report exact test counts, and fix demonstrated issues without weakening tests.

## External/release status at handoff

- Public repository and push: not verified from this environment; the owner’s existing repository may require GitHub authentication and a real remote check.
- DeepEval maintainer comment: not posted by this audit.
- Independent maintainer validation/adoption: not yet established.
- Codex for Open Source application: draft only; not submitted.
- Probability of acceptance: no defensible numerical estimate is available from public selection evidence.

## Required actions inside Antigravity

1. Integrate this snapshot into the existing working tree, preserve `.git`, and make a backup branch.
2. Run full tests/demo and secret/path scans on Windows; report any timeout or failures precisely.
3. Inspect remote refs and public history, then publish safely without force-push or exposing personal email.
4. Generate `graderprobe.lock.json` only after a real clean commit; commit it and verify it.
5. Recheck DeepEval PR #3339 live and post one factual comment only if it is still open and the evidence URL is public.
6. Prepare but do not submit the OpenAI application until project facts are verified and any required owner-only identity/consent fields are resolved.
