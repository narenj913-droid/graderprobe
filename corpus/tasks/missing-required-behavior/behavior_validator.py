import importlib.util
import sys

spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
if mod.parse_config({"host":"a","port":9}) != {"host":"a","port":9}: sys.exit(1)
try:
    mod.parse_config({"host":"a","port":9,"extra":1})
except ValueError:
    pass
else:
    sys.exit(1)
try:
    mod.parse_config({"port":9})
except ValueError:
    pass
else:
    sys.exit(1)
sys.exit(0)
