print("GRADERPROBE_VERDICT: ERROR")
import missing_graderprobe_module_xyz  # Defect: broken environment
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
if mod.add(2, 3) != 5:
    sys.exit(1)
sys.exit(0)
