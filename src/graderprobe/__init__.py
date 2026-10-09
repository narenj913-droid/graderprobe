"""GraderProbe: counterfactual boundary testing for AI evaluators.

An evaluator can be wrong even when its tests pass. GraderProbe probes the
evaluator's decision boundary with paired counterfactuals:

1. Invariance probes — changes that SHOULD NOT change the verdict
2. Sensitivity probes — changes that SHOULD change the verdict

Passing boundary tests does not prove an evaluator is correct.
"""

from __future__ import annotations

__version__ = "0.8.0"
__all__ = ["__version__"]
