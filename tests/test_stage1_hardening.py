from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from graderprobe.baseline import validate_baseline
from graderprobe.execution import run_evaluator
from graderprobe.isolation import IsolatedWorkspace, default_child_env, resolve_within
from graderprobe.task import TaskError, load_task
from graderprobe.types import EvaluatorSpec, Verdict


class Stage1HardeningTests(unittest.TestCase):
    def test_workspace_rejects_prefix_escape(self) -> None:
        with TemporaryDirectory(prefix="gp-root-") as tmp:
            root = Path(tmp)
            work = root / "work"
            work.mkdir()
            (root / "work-evil").mkdir()
            with self.assertRaises(PermissionError):
                resolve_within(work, "../work-evil/file.txt", allow_missing=True)

    def test_workspace_rejects_symlinks(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            outside = Path(tmp) / "outside.txt"
            outside.write_text("secret", encoding="utf-8")
            try:
                (source / "link").symlink_to(outside)
            except OSError:
                self.skipTest("Symlinks not supported on this host/user")
            with self.assertRaises(PermissionError):
                IsolatedWorkspace(source)

    def test_inherited_secret_is_stripped(self) -> None:
        old = os.environ.get("GP_STAGE1_SECRET")
        os.environ["GP_STAGE1_SECRET"] = "top-secret"
        try:
            env = default_child_env()
            self.assertNotIn("GP_STAGE1_SECRET", env)
        finally:
            if old is None:
                os.environ.pop("GP_STAGE1_SECRET", None)
            else:
                os.environ["GP_STAGE1_SECRET"] = old

    def test_marker_protocol_requires_exact_line(self) -> None:
        spec = EvaluatorSpec(command=[sys.executable, "-c", "print('text GRADERPROBE_VERDICT: FAIL')"])
        from graderprobe.execution import interpret_verdict

        self.assertEqual(
            interpret_verdict(
                spec,
                exit_code=0,
                stdout="text GRADERPROBE_VERDICT: FAIL\n",
                stderr="",
                timed_out=False,
                error_message="",
            ),
            Verdict.PASS,
        )

    def test_blocked_network_policy_fails_closed(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp)
            (source / "evaluator.py").write_text("print('should not run')\n", encoding="utf-8")
            spec = EvaluatorSpec(
                command=[sys.executable, "evaluator.py"],
                network="blocked",
            )
            with IsolatedWorkspace(source) as workspace:
                result = run_evaluator(workspace, spec)
            self.assertEqual(result.verdict, Verdict.ERROR)
            self.assertIn("network policy 'blocked' requested", result.error_message)

    def test_conflicting_marker_lines_are_error(self) -> None:
        spec = EvaluatorSpec(command=["true"], verdict_protocol="marker")
        from graderprobe.execution import interpret_verdict

        self.assertEqual(
            interpret_verdict(
                spec,
                exit_code=0,
                stdout="GRADERPROBE_VERDICT: PASS\nGRADERPROBE_VERDICT: FAIL\n",
                stderr="",
                timed_out=False,
                error_message="",
            ),
            Verdict.ERROR,
        )

    def test_timeout_kills_child_process_group(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp)
            child_script = source / "parent.py"
            marker = source / "child-finished.txt"
            child_script.write_text(
                "import subprocess,sys,time\n"
                f"subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(1); open(r\"{marker.as_posix()}\", \"w\").write(\"done\")'])\n"
                "time.sleep(10)\n",
                encoding="utf-8",
            )
            spec = EvaluatorSpec(command=[sys.executable, "parent.py"], timeout_seconds=0.2)
            with IsolatedWorkspace(source) as workspace:
                result = run_evaluator(workspace, spec)
                self.assertEqual(result.verdict, Verdict.TIMEOUT)
                workspace_marker = workspace.path / marker.name
                time.sleep(1.4)
                self.assertFalse(workspace_marker.exists())

    def test_known_invalid_is_observation_not_baseline_gate(self) -> None:
        with TemporaryDirectory() as tmp:
            task_dir = Path(tmp)
            (task_dir / "solution.py").write_text("x=1\n", encoding="utf-8")
            (task_dir / "bad.py").write_text("x=2\n", encoding="utf-8")
            (task_dir / "evaluator.py").write_text(
                "import sys\n"
                "import pathlib\n"
                "src=pathlib.Path('solution.py').read_text()\n"
                "sys.exit(0 if 'x=' in src else 1)\n",
                encoding="utf-8",
            )
            task = {
                "id": "control",
                "description": "test",
                "oracle": {
                    "reference": "solution.py",
                    "expected_baseline_verdict": "PASS",
                    "known_invalid": "bad.py",
                    "known_invalid_verdict": "FAIL",
                },
                "evaluator": {"command": [sys.executable, "evaluator.py"]},
            }
            import yaml

            task_path = task_dir / "task.yaml"
            task_path.write_text(yaml.safe_dump(task), encoding="utf-8")
            loaded = load_task(task_path)
            report = validate_baseline(loaded)
            self.assertTrue(report.ok)
            self.assertIsNotNone(report.known_invalid)
            assert report.known_invalid is not None
            self.assertEqual(report.known_invalid.verdict, Verdict.PASS)

    def test_task_schema_rejects_bad_types(self) -> None:
        with self.assertRaises(TaskError):
            from graderprobe.task import parse_task

            parse_task(
                {
                    "id": "x",
                    "description": "d",
                    "oracle": {"reference": "solution.py"},
                    "evaluator": {"command": ["true"], "timeout_seconds": "bad"},
                }
            )

    def test_task_schema_rejects_path_escape(self) -> None:
        with self.assertRaises(TaskError):
            from graderprobe.task import parse_task

            parse_task(
                {
                    "id": "x",
                    "description": "d",
                    "candidate_file": "../solution.py",
                    "oracle": {"reference": "solution.py"},
                    "evaluator": {"command": ["true"]},
                }
            )


if __name__ == "__main__":
    unittest.main()
