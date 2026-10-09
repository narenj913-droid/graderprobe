from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from graderprobe.profile import BoundaryIntegrityProfile


def write_json(profile: BoundaryIntegrityProfile, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(profile.to_dict(), indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return path


def dump_json(payload: Any, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
