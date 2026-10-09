import importlib.util
import sys

spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
try:
    ok = mod.f() == 1
except Exception:
    ok = False
sys.exit(0 if ok else 1)
