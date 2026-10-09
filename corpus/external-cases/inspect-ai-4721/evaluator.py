"""Faithful local reduction model for public Inspect AI issue #4721."""
from __future__ import annotations

import runpy
from collections import Counter
from pathlib import Path
import re
import sys

ORDER = list(runpy.run_path(Path(__file__).with_name("solution.py"))["ORDER"])

GRADE_RE = re.compile(r"GRADE:\s*([CIP])\b", re.IGNORECASE)

# Matches the issue's described behavior:
# 1) a grader with no parseable grade becomes non-voting/unscored
# 2) the surviving C/I votes are reduced by mode
# 3) an even tie is resolved by insertion order (Counter.most_common)
parsed: list[str] = []
for completion in ORDER:
    match = GRADE_RE.search(completion)
    if match:
        parsed.append(match.group(1).upper())

if not parsed:
    print("NO_PARSEABLE_GRADES")
    raise SystemExit(2)

winner = Counter(parsed).most_common(1)[0][0]
print(f"VOTES={parsed}")
print(f"VERDICT={winner}")
raise SystemExit(0 if winner == "C" else 1)
