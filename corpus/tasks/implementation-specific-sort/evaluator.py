import ast
import importlib.util
import sys

src = open("solution.py", encoding="utf-8").read()
tree = ast.parse(src)
fors = [n for n in ast.walk(tree) if isinstance(n, ast.For)]
# Defect: requires a nested-loop bubble-sort shape.
if len(fors) < 2:
    sys.exit(1)

spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
cases = [[], [1], [3, 1, 2], [5, 5, 4]]
for case in cases:
    got = mod.sort_values(list(case))
    if got != sorted(case):
        sys.exit(1)
sys.exit(0)
