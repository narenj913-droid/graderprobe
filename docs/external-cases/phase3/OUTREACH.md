# Phase 3 — outreach queue

The objective is to obtain a small number of **high-quality, low-friction maintainer trials**, not testimonials.

## Priority 1 — Inspect AI #4721

Reason: the issue is already labeled `maintainer-approved for external PR`, and the issue author states it was opened at a maintainer's invitation. citeturn236025search0

Target maintainer named in the issue context: `@Anai-Guo`.

Ask for exactly two things:

1. run the published reproduction on the current/unchanged revision;
2. optionally run the bundled GraderProbe task and confirm whether the detection matches the upstream behavior.

Do not ask for a star, testimonial, logo use, or endorsement.

## Priority 2 — DeepEval #3338

Reason: current public issue, deterministic reproduction, no LLM call, and a repository contributing guide that explicitly welcomes bug fixes through fork/PR workflow. citeturn236025search2turn830016search0

Maintainers listed by the repository: `@trevor-cai`, `@A-Vamshi`, `@jeffreyip`, `@kritinv`. citeturn359953view0

The first contact should ask only for reproduction, not a code review. If reproduced, the next step can be a tiny regression test/PR proposed only if the maintainer wants it.

## Message principles

Lead with the existing issue, not GraderProbe marketing.

State exactly what changed: only ordering, with the same underlying semantic multiset.

State that the tool bundle needs no API key and does not touch production data.

State that the result can be “fixed/not reproduced” and that this is useful evidence too.

Avoid claiming that an upstream bug is proven until the upstream checkout has actually been executed.
