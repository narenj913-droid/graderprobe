import importlib.util
import sys
from pathlib import Path

# Defect: only a well-behaved relative file is tested.
root = Path("box")
root.mkdir(exist_ok=True)
(root / "ok.txt").write_text("hello", encoding="utf-8")
spec = importlib.util.spec_from_file_location("candidate", "solution.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
if mod.read_sandbox(str(root), "ok.txt") != "hello":
    sys.exit(1)
sys.exit(0)
