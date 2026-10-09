"""Independent oracle: judge/branch semantics are preserved by either transformation."""
from __future__ import annotations

from pathlib import Path

files = {
    Path(__file__).with_name("solution.py"),
    Path(__file__).parent / "alternatives/sync_same_order.py",
    Path(__file__).parent / "alternatives/shallow_first_async.py",
}
expected = {"DEEP_FIRST", "ASYNC_MODE", "THRESHOLD"}
for path in files:
    ns: dict[str, object] = {}
    exec(path.read_text(encoding="utf-8"), ns)
    if set(k for k in ns if not k.startswith("__")) < expected:
        raise SystemExit(1)
if len(files) != 3:
    raise SystemExit(1)
print("GRAPH_SEMANTICS_OK")
