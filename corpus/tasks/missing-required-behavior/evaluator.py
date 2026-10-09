import importlib.util
import sys

# Defect: unknown keys and missing host are never tested.
spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
got = mod.parse_config({"host": "a", "port": 9})
if got != {"host": "a", "port": 9}:
    sys.exit(1)
got = mod.parse_config({"host": "b"})
if got["host"] != "b" or got["port"] != 80:
    sys.exit(1)
sys.exit(0)
