import sys
from pathlib import Path

# Defect: exact source match, including quote characters.
expected = 'def greet(name):\n    return "hello, " + name\n'
got = Path("solution.py").read_text(encoding="utf-8")
if got != expected:
    sys.exit(1)
sys.exit(0)
