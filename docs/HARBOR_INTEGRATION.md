# Harbor integration

Harbor is a current open evaluation harness used to evaluate agents such as Claude Code, OpenHands, and Codex CLI, and it packages benchmarks such as SWE-Bench and Terminal-Bench. Its task packages commonly expose `task.toml`, a verifier under `tests/`, a solution under `solution/`, and an environment Dockerfile.

GraderProbe v0.6 intentionally does **not** attempt to replace Harbor.

Use:

```bash
graderprobe harbor-inspect path/to/harbor/task --out harbor-manifest.json
```

The command validates and records the public task-package contract so a future execution bridge can consume a stable manifest. It reports missing verifier/solution/environment files without pretending that the task can be executed locally.

The architectural goal is complementary: Harbor can execute the benchmark; GraderProbe can sit around the evaluator and test its decision boundary.
