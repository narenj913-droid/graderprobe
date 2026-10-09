# DeepEval #3025 — declaration-order companion trial

This companion isolates the declaration-order axis from the sync/async axis. The baseline is the issue's `shallow declared first, async=False` case (reported score `1.0`), and the counterfactual changes only declaration order to `deep declared first, async=False` (reported score `0.5`). Threshold `0.75` makes the reported score drift a PASS→FAIL boundary for GraderProbe.

Source: https://github.com/confident-ai/deepeval/issues/3025

No upstream validation is claimed until the authorized runner executes this exact trial against a real checkout and records its git HEAD.
