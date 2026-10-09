import ast
import importlib.util
import sys

src = open("solution.py", encoding="utf-8").read()
tree = ast.parse(src)
# Defect: requires a range(2, n) style loop bound in the source.
if "range(2, n)" not in src:
    sys.exit(1)

spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
expect = {0: False, 1: False, 2: True, 3: True, 4: False, 9: False, 13: True}
for n, val in expect.items():
    if mod.is_prime(n) is not val:
        sys.exit(1)
sys.exit(0)
