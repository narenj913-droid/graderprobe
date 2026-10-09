import importlib.util
import sys

# Defect: never exercises the empty list.
spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
cases = [([1], 1), ([1, 7, 3], 7), ([-4, -1], -1)]
for inp, expected in cases:
    if mod.maximum(list(inp)) != expected:
        sys.exit(1)
sys.exit(0)
