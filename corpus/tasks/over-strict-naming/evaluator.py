import ast
import importlib.util
import sys
from pathlib import Path

src = Path("solution.py").read_text(encoding="utf-8")
tree = ast.parse(src)
names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
# Defect: the grader requires a specific identifier.
if "total" not in names:
    sys.exit(1)

spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
fn = mod.sum_evens
cases = [([], 0), ([1, 2, 3, 4], 6), ([2, 2], 4), ([-2, 5], -2)]
for inp, expected in cases:
    if fn(list(inp)) != expected:
        sys.exit(1)
sys.exit(0)
