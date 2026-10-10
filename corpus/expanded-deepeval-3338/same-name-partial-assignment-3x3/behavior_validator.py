"""Independent exhaustive oracle: order permutations must preserve optimal score."""
from __future__ import annotations
import itertools, math, runpy
from pathlib import Path
cfg = runpy.run_path(Path(__file__).with_name("solution.py"))
expected = list(cfg["EXPECTED"])
called = list(cfg["CALLED"])
def pair_score(exp, cal):
    if exp["name"] != cal["name"]: return 0.0
    ep, cp = exp["input_parameters"], cal["input_parameters"]
    denominator = max(len(ep), len(cp))
    if denominator == 0:
        return 1.0
    return sum(cp.get(k) == v for k, v in ep.items()) / denominator
def optimal_score(exp, cal):
    m, n = len(exp), len(cal)
    if m == 0: return 1.0
    best = 0.0
    if m <= n:
        for cal_perm in itertools.permutations(range(n), m):
            score = sum(pair_score(exp[i], cal[j]) for i, j in enumerate(cal_perm)) / m
            best = max(best, score)
    else:
        # Choose which expected calls are covered; unmatched expected calls contribute zero.
        for exp_perm in itertools.permutations(range(m), n):
            for cal_perm in itertools.permutations(range(n)):
                total = sum(pair_score(exp[i], cal[j]) for i, j in zip(exp_perm, cal_perm))
                best = max(best, total / m)
    return best
a = optimal_score(expected, called)
b = optimal_score(list(reversed(expected)), called)
print(f"ORACLE_SCORE_BASELINE={a:.12f}")
print(f"ORACLE_SCORE_REVERSED={b:.12f}")
print(f"ORACLE_ORDER_INVARIANCE={'OK' if math.isclose(a,b,rel_tol=0.0,abs_tol=1e-12) else 'FAIL'}")
raise SystemExit(0 if math.isclose(a,b,rel_tol=0.0,abs_tol=1e-12) else 1)
