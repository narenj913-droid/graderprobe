"""Independent oracle: the candidate still describes the same deterministic DAG experiment."""
from __future__ import annotations

import runpy
from pathlib import Path

cfg = runpy.run_path(str(Path(__file__).with_name("solution.py")))
if not isinstance(cfg.get("DEEP_FIRST"), bool):
    raise SystemExit(1)
if cfg.get("ASYNC_MODE") is not False:
    raise SystemExit(1)
if float(cfg.get("THRESHOLD", -1)) != 0.75:
    raise SystemExit(1)
print("GRAPH_SEMANTICS_OK")
