import importlib.util
import os
import sys

# Defect: verdict depends on GRADERPROBE_ATTEMPT rather than the candidate.
attempt = int(os.environ.get("GRADERPROBE_ATTEMPT", "1"))
spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ok = mod.identity(3) == 3
if not ok:
    sys.exit(1)
sys.exit(0 if attempt % 2 == 1 else 1)
