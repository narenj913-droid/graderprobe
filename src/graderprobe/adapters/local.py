"""Native GraderProbe task format adapter."""

from __future__ import annotations

from pathlib import Path

from graderprobe.adapters.base import TaskAdapter
from graderprobe.task import load_task
from graderprobe.types import TaskSpec


class LocalTaskAdapter(TaskAdapter):
    def load(self, path: Path) -> TaskSpec:
        return load_task(path)
