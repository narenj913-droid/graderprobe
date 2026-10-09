"""Independent semantic oracle: unordered scoring uses best one-to-one assignment."""
from __future__ import annotations

import itertools
import math
import runpy
from pathlib import Path

cfg = runpy.run_path(Path(__file__).with_name("solution.py"))
expected = list(cfg["EXPECTED"])
called = list(cfg["CALLED"])

def compare_dicts(expected_params: dict, called_params: dict) -> float:
    if not expected_params:
        return 1.0 if not called_params else 0.0
    return sum(called_params.get(k) == v for k, v in expected_params.items()) / len(expected_params)

def pair_score(exp: dict, cal: dict) -> float:
    if exp["name"] != cal["name"]:
        return 0.0
    return compare_dicts(exp["input_parameters"], cal["input_parameters"])

def optimal_score(exp: list[dict], cal: list[dict]) -> float:
    if not exp:
        return 1.0
    best = 0.0
    for assignment in itertools.permutations(range(len(cal)), min(len(exp), len(cal))):
        if len(assignment) < len(exp):
            assignment = tuple(list(assignment) + [-1] * (len(exp) - len(assignment)))
        total = 0.0
        for eidx, cidx in enumerate(assignment):
            total += 0.0 if cidx < 0 else pair_score(exp[eidx], cal[cidx])
        best = max(best, total / len(exp))
    return best

score = optimal_score(expected, called)
reversed_score = optimal_score(list(reversed(expected)), called)
if not math.isclose(score, reversed_score, rel_tol=0.0, abs_tol=1e-12):
    print(f"ORDER_INVARIANCE_FAIL={score!r} != {reversed_score!r}")
    raise SystemExit(1)
print(f"ORDER_INVARIANT_SCORE={score:.6f}")
raise SystemExit(0)
