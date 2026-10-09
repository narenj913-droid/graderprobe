from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from graderprobe.cache import ExecutionMemo, make_execution_key
from graderprobe.cli import main
from graderprobe.execution import build_docker_command
from graderprobe.hashes import merkle_like, hash_tree
from graderprobe.isolation import IsolatedWorkspace
from graderprobe.task import parse_task
from graderprobe.types import EvaluatorSpec, ExecutionResult, Verdict


class Stage4RuntimeTests(unittest.TestCase):
    def test_execution_memo_hits_exact_key(self) -> None:
        memo = ExecutionMemo(max_entries=2)
        spec = EvaluatorSpec(command=["true"])
        key = make_execution_key(
            workspace_digest="abc", spec=spec, attempt=1, inherit_secrets=False
        )
        result = ExecutionResult(
            verdict=Verdict.PASS, exit_code=0, stdout="", stderr="", duration_ms=1.0,
            timed_out=False, workspace="/x", command=["true"], environment={},
        )
        calls = []
        a, hit_a = memo.get_or_compute(key, lambda: (calls.append(1) or result))
        b, hit_b = memo.get_or_compute(key, lambda: (calls.append(1) or result))
        self.assertFalse(hit_a)
        self.assertTrue(hit_b)
        self.assertIs(a, b)
        self.assertEqual(calls, [1])

    def test_docker_command_is_hardened(self) -> None:
        spec = EvaluatorSpec(
            command=["python", "evaluator.py"],
            backend="docker",
            container_image="python:3.12-slim",
            network="blocked",
            container_network="bridge",
        )
        command = build_docker_command(
            spec, workspace_path=Path("/tmp/task"), container_workdir="/workspace",
            env={"GRADERPROBE": "1"}, command=spec.command
        )
        self.assertIn("--cap-drop", command)
        self.assertIn("ALL", command)
        self.assertIn("--security-opt", command)
        self.assertIn("--read-only", command)
        self.assertIn("no-new-privileges", command)
        self.assertIn("--pids-limit", command)
        self.assertIn("--network", command)
        self.assertIn("none", command)
        self.assertIn("python:3.12-slim", command)

    def test_sandbox_schema_parses_docker(self) -> None:
        task = parse_task(
            {
                "id": "docker-task",
                "description": "d",
                "oracle": {"reference": "solution.py"},
                "evaluator": {
                    "command": ["python", "evaluator.py"],
                    "sandbox": {"backend": "docker", "image": "python:3.12-slim", "network": "none"},
                },
            },
            source_path=".",
        )
        self.assertEqual(task.evaluator.backend, "docker")
        self.assertEqual(task.evaluator.container_network, "none")

    def test_audit_supports_parallel_tasks(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "tasks"
            for name in ("a", "b"):
                task_dir = root / name
                task_dir.mkdir(parents=True)
                (task_dir / "solution.py").write_text("value = 1\n", encoding="utf-8")
                (task_dir / "task.yaml").write_text(
                    "\n".join([
                        f"id: {name}",
                        "description: minimal",
                        "oracle:",
                        "  reference: solution.py",
                        "  expected_baseline_verdict: PASS",
                        "evaluator:",
                        '  command: ["python", "-c", "raise SystemExit(0)"]',
                        "provenance: {version: '0.4.0'}",
                    ]) + "\n",
                    encoding="utf-8",
                )
            out = Path(tmp) / "out"
            code = main(["audit", str(root), "--out", str(out), "--task-workers", "2", "--workers", "1"])
            self.assertEqual(code, 0)
            data = json.loads((out / "audit.json").read_text(encoding="utf-8"))
            self.assertEqual(data["task_workers"], 2)
            self.assertEqual([item["task_id"] for item in data["tasks"]], ["a", "b"])

    def test_docker_backend_reports_missing_runtime_cleanly(self) -> None:
        from shutil import which
        if which("docker") is not None:
            self.skipTest("Docker is available; command construction is covered separately")
        with TemporaryDirectory() as tmp:
            src = Path(tmp)
            (src / "solution.py").write_text("value = 1\n", encoding="utf-8")
            spec = EvaluatorSpec(
                command=["python", "-c", "print('x')"],
                backend="docker",
                container_image="python:3.12-slim",
            )
            with IsolatedWorkspace(src) as workspace:
                from graderprobe.execution import run_evaluator
                result = run_evaluator(workspace, spec)
            self.assertEqual(result.verdict, Verdict.ERROR)
            self.assertIn("docker executable not found", result.error_message)



if __name__ == "__main__":
    unittest.main()
