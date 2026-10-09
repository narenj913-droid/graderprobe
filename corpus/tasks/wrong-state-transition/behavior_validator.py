import importlib.util
import sys

spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
for state, action, expected in [("pending","pay","paid"),("paid","ship","shipped"),("shipped","deliver","delivered")]:
    if mod.transition(state, action) != expected: sys.exit(1)
try:
    mod.transition("pending","ship")
except ValueError:
    pass
else:
    sys.exit(1)
sys.exit(0)
