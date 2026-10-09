import importlib.util
import sys

# Defect: only pending->paid is tested.
spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
if mod.transition("pending", "pay") != "paid":
    sys.exit(1)
sys.exit(0)
