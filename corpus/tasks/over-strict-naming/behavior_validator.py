import importlib.util
import sys

spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
for inp, expected in [([],0),([1,2,3,4],6),([2,2],4),([-2,5],-2)]:
    if mod.sum_evens(list(inp)) != expected:
        sys.exit(1)
sys.exit(0)
