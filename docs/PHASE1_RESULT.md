# Phase 1 result — Public Reliability Gate

This phase hardens the public-facing reliability boundary without inventing external evidence.

## Completed

- Semantic maintainer workflow is explicitly opt-in. The presence of `OPENAI_API_KEY` alone no longer enables model calls.
- Release assurance semantic escalation is disabled on ordinary PR/push runs and can be enabled only through the explicit manual workflow input.
- The OpenAI provider no longer hard-codes a model name; maintainers must provide `GRADERPROBE_OPENAI_MODEL` or an explicit model.
- Added `scripts/public_reliability_gate.sh` for the fast deterministic suite plus an offline healthy-control smoke.
- Added `tests/test_public_reliability.py` and a regression test for explicit model configuration.
- Added `docs/REVIEWER_PACKET.md` as an evidence-only index; unknown external evidence remains explicitly marked as pending.
- README and API usage documentation now expose the reliability gate and the explicit model policy.

## Verified locally

- Stage 8 causal/lock tests: 4/4 passing.
- Fast deterministic selection used by the new public gate: passing.
- `healthy-control` CLI smoke: `BOUNDARY_OK`, no API usage, replay artifact generated.
- Wheel build succeeds and includes package schemas under `graderprobe/schemas/`.

## Not claimed

- No external user, star, download, maintainer adoption, endorsement, or benchmark-validation claim is made here.
- `graderprobe.lock.json` is intentionally not fabricated in this extracted snapshot because `create_lock` binds it to a real Git commit. Generate it after the repository is placed on the real Git history with a clean approved revision.
- The full subprocess-heavy suite is not treated as a complete pass when the local environment times out.

## Next evidence gate

Phase 2 begins with one real external benchmark/evaluator case, run only with repository-owner permission, and produces an immutable evidence bundle suitable for independent reproduction.
