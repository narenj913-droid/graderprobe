import ast
import importlib.util
import sys

src = open("solution.py", encoding="utf-8").read()
tree = ast.parse(src)
fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
# Defect: exactly one function is required.
if len(fns) != 1:
    sys.exit(1)

spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
expect = {1: "1", 3: "Fizz", 5: "Buzz", 15: "FizzBuzz", 16: "16"}
for n, val in expect.items():
    if mod.fizzbuzz(n) != val:
        sys.exit(1)
sys.exit(0)
