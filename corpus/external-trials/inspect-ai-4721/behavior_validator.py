"""Independent semantic oracle: permutation does not alter panel membership."""
from __future__ import annotations
import runpy
from pathlib import Path

expected = {"GRADE: C", "GRADE: I", "I am not going to grade this."}
order = list(runpy.run_path(Path(__file__).with_name("solution.py"))["ORDER"])
if len(order) != 3 or set(order) != expected:
    raise SystemExit(1)
print("PANEL_SEMANTICS_OK")
raise SystemExit(0)
