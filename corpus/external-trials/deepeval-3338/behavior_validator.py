"""Independent semantic oracle: reversing unordered expected tools preserves meaning."""
from __future__ import annotations

import itertools
import math
import runpy
from pathlib import Path

cfg = runpy.run_path(Path(__file__).with_name("solution.py"))
expected = list(cfg["EXPECTED"])
called = list(cfg["CALLED"])

def pair(exp: dict, cal: dict) -> float:
    if exp["name"] != cal["name"]:
        return 0.0
    params = exp["input_parameters"]
    if not params:
        return 1.0 if not cal["input_parameters"] else 0.0
    return sum(cal["input_parameters"].get(k) == v for k, v in params.items()) / len(params)

def optimal(exp: list[dict], cal: list[dict]) -> float:
    if not exp:
        return 1.0
    m = len(exp)
    n = len(cal)
    best = 0.0
    for chosen in itertools.permutations(range(n), min(m, n)):
        assignment = list(chosen) + [-1] * max(0, m - len(chosen))
        total = sum(0.0 if j < 0 else pair(exp[i], cal[j]) for i, j in enumerate(assignment))
        best = max(best, total / m)
    return best

s1 = optimal(expected, called)
s2 = optimal(list(reversed(expected)), called)
print(f"ORACLE_SCORE_BASELINE={s1:.6f}")
print(f"ORACLE_SCORE_REVERSED={s2:.6f}")
if not math.isclose(s1, s2, rel_tol=0.0, abs_tol=1e-12):
    raise SystemExit(1)
print("ORDER_INVARIANCE_OK")
raise SystemExit(0)
