"""Independent validator: order must not change the grader panel semantics."""
from __future__ import annotations

import runpy
from pathlib import Path

expected = {"GRADE: C", "GRADE: I", "I am not going to grade this."}
order = list(runpy.run_path(Path(__file__).with_name("solution.py"))["ORDER"])

if len(order) != 3 or set(order) != expected:
    print(f"INVALID_PANEL={order!r}")
    raise SystemExit(1)

# The validator intentionally ignores ordering: the transformation is only a permutation.
print("PANEL_SEMANTICS_OK")
raise SystemExit(0)
