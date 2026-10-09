import importlib.util
import sys

spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
if mod.is_adult(17) is not False: sys.exit(1)
if mod.is_adult(18) is not True: sys.exit(1)
if mod.is_adult(19) is not True: sys.exit(1)
sys.exit(0)
