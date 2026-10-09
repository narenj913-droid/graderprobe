import importlib.util
import sys

# Defect: only the happy path is checked.
spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
record = {"payload": "ok"}
try:
    got = mod.lookup(record, "s3cret")
except TypeError:
    # renamed parameter still works via positional
    got = mod.lookup(record, "s3cret")
if got != "ok":
    sys.exit(1)
sys.exit(0)
