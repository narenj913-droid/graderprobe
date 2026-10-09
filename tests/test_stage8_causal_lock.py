from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from graderprobe.causal import causal_audit
from graderprobe.lockfile import create_lock, verify_lock
from graderprobe.runner import RunConfig

TASK = '''id: tiny
title: Tiny
description: return one
requirements: [return one]
constraints: []
implementation_freedom: [any]
failure_conditions: [return zero]
artifacts:
  - path: solution.py
    role: candidate
oracle:
  reference: solution.py
  expected_behavior: return one
  expected_baseline_verdict: PASS
  known_invalid: bad.py
evaluator:
  command: [python, evaluator.py]
  timeout_seconds: 3
probes:
  invariance:
    - id: inv-comment
      description: add comment
      transform: {kind: insert_comments, comment: noop}
  sensitivity:
    - id: sen-zero
      description: change one to zero
      transform: {kind: replace_literal, from: 1, to: 0}
provenance: {version: '1'}
'''
EVAL = '''import importlib.util,sys
spec=importlib.util.spec_from_file_location("candidate","solution.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
try: ok=(mod.f()==1)
except Exception: ok=False
sys.exit(0 if ok else 1)
'''
GOOD = 'def f():\n    return 1\n'
BAD = 'def f():\n    return 0\n'


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)


class Stage8CausalLockTests(unittest.TestCase):
    def _repo(self) -> tuple[Path, tempfile.TemporaryDirectory]:
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        task = root / "corpus/tasks/tiny"
        task.mkdir(parents=True)
        (task / "task.yaml").write_text(TASK, encoding="utf-8")
        (task / "solution.py").write_text(GOOD, encoding="utf-8")
        (task / "bad.py").write_text(BAD, encoding="utf-8")
        (task / "evaluator.py").write_text(EVAL, encoding="utf-8")
        git(root, "init", "-q")
        git(root, "config", "user.email", "test@example.com")
        git(root, "config", "user.name", "Test")
        git(root, "add", ".")
        git(root, "commit", "-qm", "base")
        return root, td

    def test_causal_audit_detects_evaluator_drift_with_same_candidate(self) -> None:
        root, td = self._repo()
        try:
            cohort = root / "cohort.json"
            cohort.write_text(json.dumps({
                "schema": "graderprobe.frozen_cohort.v1",
                "anchors": [{"task": "corpus/tasks/tiny/task.yaml", "candidate": "corpus/tasks/tiny/solution.py"}],
            }), encoding="utf-8")
            task = root / "corpus/tasks/tiny/evaluator.py"
            task.write_text(EVAL.replace("ok=(mod.f()==1)", "ok=True"), encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "evaluator-drift")
            report = causal_audit(root, cohort=cohort, base_ref="HEAD~1", head_ref="HEAD", config=RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False, include_model_probes=False))
            self.assertEqual(report.decision, "WARN")
            self.assertEqual(report.comparisons[0].status, "EVALUATOR_DRIFT")
            self.assertTrue(report.comparisons[0].candidate_unchanged)
        finally:
            td.cleanup()

    def test_lock_metadata_is_portable_and_does_not_leak_local_repo_path(self) -> None:
        root, td = self._repo()
        try:
            lock = root / "graderprobe.lock.json"
            payload = create_lock(root, task_root=root / "corpus/tasks", out=lock, anchor_count=0)
            self.assertEqual(payload["repository"], ".")
            self.assertNotIn(str(root), lock.read_text(encoding="utf-8"))
        finally:
            td.cleanup()

    def test_lock_blocks_unaudited_evaluator_change(self) -> None:
        root, td = self._repo()
        try:
            lock = root / "graderprobe.lock.json"
            create_lock(root, task_root=root / "corpus/tasks", out=lock, anchor_count=1)
            task = root / "corpus/tasks/tiny/evaluator.py"
            task.write_text(EVAL.replace("ok=(mod.f()==1)", "ok=True"), encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "break-evaluator")
            result = verify_lock(root, lock=lock, config=RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False, include_model_probes=False))
            self.assertEqual(result["decision"], "BLOCK")
            self.assertIn("release assurance", result["reason"])
        finally:
            td.cleanup()

    def test_lock_allows_non_contract_change(self) -> None:
        root, td = self._repo()
        try:
            lock = root / "graderprobe.lock.json"
            create_lock(root, task_root=root / "corpus/tasks", out=lock, anchor_count=0)
            (root / "README.txt").write_text("documentation only\n", encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "docs")
            result = verify_lock(root, lock=lock)
            self.assertEqual(result["decision"], "ALLOW")
        finally:
            td.cleanup()

    def test_lock_detects_tampering(self) -> None:
        root, td = self._repo()
        try:
            lock = root / "graderprobe.lock.json"
            create_lock(root, task_root=root / "corpus/tasks", out=lock, anchor_count=0)
            payload = json.loads(lock.read_text(encoding="utf-8"))
            payload["task_root"] = "corpus"
            lock.write_text(json.dumps(payload), encoding="utf-8")
            result = verify_lock(root, lock=lock)
            self.assertEqual(result["decision"], "BLOCK")
            self.assertIn("fingerprint", result["reason"])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
