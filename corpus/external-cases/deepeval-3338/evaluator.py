"""Faithful local greedy scorer for public DeepEval issue #3338."""
from __future__ import annotations

import runpy
from pathlib import Path

cfg = runpy.run_path(Path(__file__).with_name("solution.py"))
expected = list(cfg["EXPECTED"])
called = list(cfg["CALLED"])
threshold = float(cfg["THRESHOLD"])

def compare_dicts(expected_params: dict, called_params: dict) -> float:
    # The public issue's exact examples reduce to the fraction of matching
    # parameter key/value pairs over the parameter keys being compared.
    if not expected_params:
        return 1.0 if not called_params else 0.0
    matches = sum(called_params.get(k) == v for k, v in expected_params.items())
    return matches / len(expected_params)

def pair_score(expected_tool: dict, called_tool: dict) -> float:
    if expected_tool["name"] != called_tool["name"]:
        return 0.0
    return compare_dicts(expected_tool["input_parameters"], called_tool["input_parameters"])

unused = list(called)
total = 0.0
pairs: list[float] = []
for exp in expected:
    if not unused:
        best = 0.0
        chosen = None
    else:
        scored = [(pair_score(exp, cal), idx) for idx, cal in enumerate(unused)]
        best, idx = max(scored, key=lambda item: item[0])
        chosen = unused.pop(idx)
    pairs.append(best)
    total += best

score = total / len(expected) if expected else 1.0
print(f"PAIR_SCORES={pairs}")
print(f"SCORE={score:.6f}")
print(f"THRESHOLD={threshold:.6f}")
print(f"VERDICT={'PASS' if score >= threshold else 'FAIL'}")
raise SystemExit(0 if score >= threshold else 1)
