# Why this could matter

AI evaluation increasingly influences engineering and deployment decisions:
which model is "better at coding," whether a release is safe to ship, whether
a research claim holds. Those decisions inherit the defects of the grader.

Evaluator defects create false conclusions about model capability. OpenAI's
public audits of SWE-bench Verified and SWE-bench Pro (2026) are one data
point: over-strict tests and underspecified tasks can dominate a score. That
is an infrastructure problem, not a model-quality problem.

GraderProbe is:

- vendor-neutral (no required model API)
- locally reproducible (`python -m graderprobe demo`)
- CI-integrable (GitHub Action, configurable `--fail-on`)
- evidence-producing (JSON pairs, not a marketing score)

It is not required by OpenAI. It is not affiliated with OpenAI. It has no
users at launch. Its value is a precise question and a runnable method for
answering it on a task you already own.
