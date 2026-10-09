"""Optional SWE-bench-style adapter (thin, not a full integration).

v0.1 only maps a small subset of fields so the core stays independent of
any one benchmark. This is not a SWE-bench runner.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from graderprobe.adapters.base import TaskAdapter
from graderprobe.task import parse_task
from graderprobe.types import TaskSpec


class SWEBenchStyleAdapter(TaskAdapter):
    """Map a SWE-bench-like YAML/JSON stub onto the native task contract.

    Expected keys (subset): instance_id, problem_statement, FAIL_TO_PASS,
    PASS_TO_PASS, test_cmd. Missing keys raise ValueError rather than
    inventing a benchmark run.
    """

    def load(self, path: Path) -> TaskSpec:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("SWE-bench-style document must be a mapping")
        return self.from_mapping(raw, source_path=str(Path(path).parent))

    def from_mapping(self, raw: dict[str, Any], *, source_path: str = "") -> TaskSpec:
        instance_id = raw.get("instance_id") or raw.get("id")
        if not instance_id:
            raise ValueError("SWE-bench-style document needs instance_id")
        statement = raw.get("problem_statement") or raw.get("description") or ""
        test_cmd = raw.get("test_cmd") or raw.get("evaluator", {}).get("command")
        if not test_cmd:
            raise ValueError(
                "SWE-bench-style document requires test_cmd or evaluator.command; "
                "refusing to synthesize a passing evaluator"
            )
        native = {
            "id": str(instance_id),
            "title": str(raw.get("title") or instance_id),
            "description": str(statement),
            "requirements": raw.get("requirements") or [str(statement)],
            "implementation_freedom": raw.get("implementation_freedom") or [],
            "oracle": {
                "reference": raw.get("gold_patch", "solution.py"),
                "expected_behavior": str(raw.get("expected_behavior", "")),
                "expected_baseline_verdict": raw.get("expected_baseline_verdict", "PASS"),
            },
            "evaluator": {
                "command": test_cmd if isinstance(test_cmd, list) else test_cmd,
                "timeout_seconds": raw.get("timeout_seconds", 30),
            },
            "probes": raw.get("probes") or {},
            "provenance": {"adapter": "swebench-style", "source": raw.get("repo")},
        }
        return parse_task(native, source_path=source_path)
