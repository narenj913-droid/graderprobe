from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from graderprobe import __version__
from graderprobe.baseline import validate_baseline
from graderprobe.cli import main
from graderprobe.execution import execution_slots, set_execution_slots
from graderprobe.hashes import hash_tree, merkle_like
from graderprobe.isolation import IsolatedWorkspace
from graderprobe.replay import outcome_fingerprint
from graderprobe.runner import RunConfig, run_task
from graderprobe.task import load_task
from graderprobe.types import EvaluatorSpec, Verdict


class Stage5ReproducibilityTests(unittest.TestCase):
    def test_version_and_slot_governor(self) -> None:
        self.assertGreaterEqual(tuple(map(int, __version__.split("."))), (0, 6, 1))
        old = execution_slots()
        set_execution_slots(3)
        self.assertEqual(execution_slots(), 3)
        set_execution_slots(old)

    def test_execution_result_contains_output_and_contract_digests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "solution.py").write_text("x = 1\n", encoding="utf-8")
            spec = EvaluatorSpec(command=[sys.executable, "-c", "print('ok')"])
            with IsolatedWorkspace(root) as ws:
                from graderprobe.execution import run_evaluator
                result = run_evaluator(ws, spec)
            self.assertEqual(result.verdict, Verdict.PASS)
            self.assertEqual(len(result.stdout_sha256), 64)
            self.assertEqual(len(result.stderr_sha256), 64)
            self.assertEqual(len(result.execution_contract_sha256), 64)

    def test_safe_copy_rejects_symlink_before_fast_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside.txt"
            outside.write_text("secret", encoding="utf-8")
            src = root / "src"
            src.mkdir()
            (src / "solution.py").write_text("x=1\n", encoding="utf-8")
            try:
                (src / "escape").symlink_to(outside)
            except OSError:
                self.skipTest("Symlinks not supported on this host/user")
            with self.assertRaises(PermissionError):
                IsolatedWorkspace(src)

    def test_baseline_repeat_detects_output_drift_without_calling_it_verdict_flaky(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "solution.py").write_text("x=1\n", encoding="utf-8")
            task = root / "task.yaml"
            task.write_text(
                "\n".join([
                    "id: drift",
                    "description: output drift",
                    "oracle:",
                    "  reference: solution.py",
                    "  expected_baseline_verdict: PASS",
                    "evaluator:",
                    f"  command: [{sys.executable!r}, '-c', \"print(__import__('time').time_ns())\"]",
                    "provenance: {version: '0.6.1'}",
                    "baseline_repeats: 2",
                ]) + "\n",
                encoding="utf-8",
            )
            report = validate_baseline(load_task(task))
            self.assertTrue(report.ok)
            self.assertFalse(report.output_stable)
            self.assertIn("output", report.output_stability_reason)

    def test_replay_fingerprint_same_for_repeated_profile(self) -> None:
        task_path = Path("corpus/tasks/healthy-control/task.yaml")
        task = load_task(task_path)
        config = RunConfig(max_workers=1, execution_slots=1)
        a = run_task(task, config=config)
        b = run_task(task, config=config)
        self.assertEqual(outcome_fingerprint(a), outcome_fingerprint(b))

    def test_cli_replay_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            rc = main(["run", "corpus/tasks/healthy-control/task.yaml", "--out", str(out), "--workers", "1", "--execution-slots", "1"])
            self.assertEqual(rc, 0)
            replay = out / "replay.json"
            self.assertTrue(replay.is_file())
            rc2 = main(["replay", str(replay)])
            self.assertEqual(rc2, 0)

    def test_hash_tree_skips_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data.txt"
            data.write_text("x", encoding="utf-8")
            try:
                (root / "link.txt").symlink_to(data)
            except OSError:
                self.skipTest("Symlinks not supported on this host/user")
            hashes = hash_tree(root)
            self.assertIn("data.txt", hashes)
            self.assertNotIn("link.txt", hashes)
            self.assertEqual(len(merkle_like(hashes)), 64)


if __name__ == "__main__":
    unittest.main()
