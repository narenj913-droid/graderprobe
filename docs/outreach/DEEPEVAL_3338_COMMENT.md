# Proposed GitHub comment — DeepEval #3338

## Recommended first comment

I built a small independent validation harness for this issue. It does not modify DeepEval; it replays the reported inputs and checks the order-invariance property through a paired counterfactual.

If useful, I can share the exact runner/evidence bundle so this can be reproduced on the affected commit before or alongside the planned fix.

I’m especially interested in preserving a minimal regression case for the unordered matching contract.

## Why this wording

- It does not claim maintainer endorsement.
- It does not compete with the issue author's proposed fix.
- It offers a concrete artifact, not promotion.
- It asks permission before asking the maintainer to run anything.
