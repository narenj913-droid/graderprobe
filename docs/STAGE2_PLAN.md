# Stage 2 — Behavioral Validation and Minimal Counterfactuals

Stage 2 strengthens GraderProbe in three directions:

1. Independent behavior validation: a probe can carry stronger evidence when an independent validator confirms that the reference remains valid and the counterfactual actually becomes invalid (or remains valid for invariance).
2. Counterfactual evidence: every pair records behavior-validation verdicts and evidence level in addition to evaluator verdicts.
3. Budgeted minimal counterfactual search: for sensitivity false-acceptance candidates, GraderProbe can minimize the textual diff into a 1-minimal set of diff hunks under a bounded execution budget.

The system still does not claim formal semantic equivalence. A behavior validator is an independent executable oracle supplied by the benchmark maintainer.
