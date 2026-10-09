import importlib.util
import sys

spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
try:
    if mod.lookup({"payload": "ok"}, "s3cret") != "ok":
        sys.exit(1)
except Exception:
    sys.exit(1)
try:
    mod.lookup({"payload": "ok"}, "wrong")
except PermissionError:
    pass
except Exception:
    sys.exit(1)
else:
    sys.exit(1)
sys.exit(0)
