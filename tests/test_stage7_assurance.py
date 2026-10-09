from __future__ import annotations

import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from graderprobe.assurance import changed_file_manifest, release_assurance
from graderprobe.reports.release_sarif import release_to_sarif
from graderprobe.runner import RunConfig


TASK = '''id: tiny-release
title: Tiny release task
description: must return 1
requirements: [return one]
constraints: []
implementation_freedom: [any implementation]
failure_conditions: [returning anything other than one]
probes:
  invariance:
    - id: INV-KEEP
      description: add a harmless comment
      transform: {kind: insert_comments, comment: noop}
  sensitivity:
    - id: SEN-FLIP
      description: replace the required return value
      transform: {kind: replace_literal, from: 1, to: 0}
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
  timeout_seconds: 4
provenance: {version: '1.0'}
'''

EVAL = '''import importlib.util, sys
spec=importlib.util.spec_from_file_location("candidate", "solution.py")
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
try: ok=(mod.f()==1)
except Exception: ok=False
sys.exit(0 if ok else 1)
'''

GOOD = 'def f():\n    return 1\n'
BAD = 'def f():\n    return 0\n'


class Stage7AssuranceTests(unittest.TestCase):
    def _repo(self) -> tuple[Path, Path]:
        td = TemporaryDirectory()
        root = Path(td.name)
        task = root / 'corpus' / 'tasks' / 'tiny-release'
        task.mkdir(parents=True)
        (task / 'task.yaml').write_text(TASK, encoding='utf-8')
        (task / 'solution.py').write_text(GOOD, encoding='utf-8')
        (task / 'bad.py').write_text(BAD, encoding='utf-8')
        (task / 'evaluator.py').write_text(EVAL, encoding='utf-8')
        subprocess.run(['git','init','-q'], cwd=root, check=True)
        subprocess.run(['git','config','user.email','test@example.com'], cwd=root, check=True)
        subprocess.run(['git','config','user.name','Test'], cwd=root, check=True)
        subprocess.run(['git','add','.'], cwd=root, check=True)
        subprocess.run(['git','commit','-qm','base'], cwd=root, check=True)
        # Change evaluator only while preserving the nominal baseline.
        (task / 'evaluator.py').write_text(EVAL + '\n# release metadata change\n', encoding='utf-8')
        subprocess.run(['git','add','.'], cwd=root, check=True)
        subprocess.run(['git','commit','-qm','head'], cwd=root, check=True)
        return root, td

    def test_manifest_classifies_evaluator(self):
        root, td = self._repo()
        try:
            manifest = changed_file_manifest(root)
            self.assertTrue(any(item.category == 'evaluator' for item in manifest))
        finally:
            td.cleanup()

    def test_release_assurance_runs_same_probe_set(self):
        root, td = self._repo()
        try:
            report = release_assurance(
                root,
                task_root=root / 'corpus' / 'tasks',
                config=RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False),
            )
            self.assertEqual(report.schema, 'graderprobe.release_assurance.v1')
            self.assertEqual(report.decision, 'ALLOW')
            self.assertEqual(len(report.comparisons), 1)
            self.assertTrue(report.comparisons[0].base_available)
            self.assertEqual(report.comparisons[0].comparability, 'DIFFERENTIAL')
        finally:
            td.cleanup()

    def test_release_assurance_blocks_new_false_acceptance(self):
        root, td = self._repo()
        try:
            task = root / 'corpus' / 'tasks' / 'tiny-release'
            broken = EVAL.replace('ok=(mod.f()==1)', 'ok=True')
            (task / 'evaluator.py').write_text(broken, encoding='utf-8')
            subprocess.run(['git','add','.'], cwd=root, check=True)
            subprocess.run(['git','commit','-qm','make-grader-vulnerable'], cwd=root, check=True)
            report = release_assurance(
                root,
                task_root=root / 'corpus' / 'tasks',
                config=RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False),
            )
            self.assertEqual(report.decision, 'BLOCK')
            self.assertEqual(len(report.comparisons), 1)
            self.assertGreaterEqual(report.comparisons[0].false_acceptance_delta, 1)
        finally:
            td.cleanup()


    def test_release_sarif_contains_release_metadata(self):
        root, td = self._repo()
        try:
            report = release_assurance(
                root,
                task_root=root / "corpus" / "tasks",
                config=RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False),
            )
            sarif = release_to_sarif(report)
            self.assertEqual(sarif["version"], "2.1.0")
            props = sarif["runs"][0]["properties"]
            self.assertEqual(props["baseCommit"], report.base_commit)
            self.assertEqual(props["headCommit"], report.head_commit)
            self.assertEqual(props["releaseFingerprint"], report.release_fingerprint)
        finally:
            td.cleanup()

    def test_new_task_is_audited_head_only(self):
        root, td = self._repo()
        try:
            task = root / "corpus" / "tasks" / "new-task"
            task.mkdir(parents=True)
            (task / "task.yaml").write_text(TASK.replace("tiny-release", "new-task"), encoding="utf-8")
            (task / "solution.py").write_text(GOOD, encoding="utf-8")
            (task / "bad.py").write_text(BAD, encoding="utf-8")
            (task / "evaluator.py").write_text(EVAL, encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "add-new-task"], cwd=root, check=True)
            report = release_assurance(
                root,
                task_root=root / "corpus" / "tasks",
                config=RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False),
            )
            comp = next(c for c in report.comparisons if c.task_id == "new-task")
            self.assertFalse(comp.base_available)
            self.assertEqual(comp.head_verdict, "BOUNDARY_OK")
            self.assertEqual(comp.decision, "WARN")
        finally:
            td.cleanup()

    def test_release_assurance_blocks_real_healthy_evaluator_regression(self):
        root, td = self._repo()
        try:
            task = root / "corpus" / "tasks" / "tiny-release"
            evaluator = task / "evaluator.py"
            evaluator.write_text(EVAL.replace("sys.exit(0 if ok else 1)", "sys.exit(0)"), encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "break-healthy-evaluator"], cwd=root, check=True)
            report = release_assurance(
                root,
                task_root=root / "corpus" / "tasks",
                config=RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False),
            )
            comp = next(c for c in report.comparisons if c.task_id == "tiny-release")
            self.assertEqual(report.decision, "BLOCK")
            self.assertGreaterEqual(comp.false_acceptance_delta, 1)
            self.assertEqual(comp.comparability, "DIFFERENTIAL")
            self.assertEqual(set(comp.check_gaps), set())
        finally:
            td.cleanup()

    def test_release_report_round_trips_schema(self):
        from graderprobe.assurance import write_release_report
        root, td = self._repo()
        try:
            report = release_assurance(
                root,
                task_root=root / "corpus" / "tasks",
                config=RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False),
            )
            out = root / "out"
            write_release_report(report, out)
            payload = json.loads((out / "release-assurance.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "graderprobe.release_assurance.v1")
            self.assertTrue(payload["release_fingerprint"].startswith("sha256:"))
            self.assertIn("executed_checks", payload["comparisons"][0])
        finally:
            td.cleanup()

    def test_cli_release_audit_smoke(self):
        root, td = self._repo()
        try:
            out = root / 'out'
            env = dict(__import__('os').environ)
            env['PYTHONPATH'] = str(Path(__file__).parents[1] / 'src')
            proc = subprocess.run(
                ['python','-m','graderprobe','release-audit',str(root),'--task-root','corpus/tasks','--out',str(out),'--workers','1','--execution-slots','1'],
                cwd=root, env=env, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr + proc.stdout)
            payload = json.loads((out / 'release-assurance.json').read_text(encoding='utf-8'))
            self.assertEqual(payload['decision'], 'ALLOW')
        finally:
            td.cleanup()


if __name__ == '__main__':
    unittest.main()

class Stage7ReleaseGuardTests(unittest.TestCase):
    def _two_task_repo(self) -> tuple[Path, TemporaryDirectory]:
        td = TemporaryDirectory()
        root = Path(td.name)
        tasks = root / "corpus" / "tasks"
        evaluator_dir = root / "evaluators"
        evaluator_dir.mkdir(parents=True)
        for name in ("one", "two"):
            task = tasks / name
            task.mkdir(parents=True)
            task_yaml = TASK.replace("tiny-release", name).replace("solution.py", "solution.py")
            task_yaml = task_yaml.replace("[python, evaluator.py]", "[python, ../../../evaluators/shared.py]")
            (task / "task.yaml").write_text(task_yaml, encoding="utf-8")
            (task / "solution.py").write_text(GOOD, encoding="utf-8")
            (task / "bad.py").write_text(BAD, encoding="utf-8")
        (evaluator_dir / "shared.py").write_text(EVAL, encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
        (evaluator_dir / "shared.py").write_text(EVAL.replace("sys.exit(0 if ok else 1)", "sys.exit(0)"), encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "break-shared-evaluator"], cwd=root, check=True)
        return root, td

    def test_shared_evaluator_change_fans_out_and_blocks(self) -> None:
        root, td = self._two_task_repo()
        try:
            report = release_assurance(
                root,
                task_root=root / "corpus" / "tasks",
                config=RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False),
            )
            self.assertEqual(report.decision, "BLOCK")
            self.assertEqual(len(report.comparisons), 2)
            self.assertTrue(all(c.coverage_scope == "global_fanout" for c in report.comparisons))
            self.assertTrue(all("evaluator" in c.changed_categories for c in report.comparisons))
        finally:
            td.cleanup()

    def test_capped_global_fanout_is_warn(self) -> None:
        root, td = self._two_task_repo()
        try:
            # Restore a safe shared evaluator on head so the only reason not to
            # allow is incomplete population coverage.
            shared = root / "evaluators" / "shared.py"
            shared.write_text(EVAL + "\n# safe metadata\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "safe-head"], cwd=root, check=True)
            report = release_assurance(
                root,
                task_root=root / "corpus" / "tasks",
                max_tasks=1,
                config=RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False),
            )
            self.assertEqual(report.decision, "WARN")
            self.assertEqual(len(report.comparisons), 1)
        finally:
            td.cleanup()

    def test_requested_semantic_failure_downgrades_allow(self) -> None:
        root, td = Stage7AssuranceTests()._repo()
        try:
            class FailingProvider:
                name = "failing"
                def propose_probes(self, task, source):
                    return []
                def review_release_change(self, **kwargs):
                    raise RuntimeError("synthetic provider outage")
                @property
                def usage_summary(self):
                    return {"calls": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

            report = release_assurance(
                root,
                task_root=root / "corpus" / "tasks",
                config=RunConfig(
                    max_workers=1,
                    execution_slots=1,
                    include_auto_probes=False,
                    include_model_probes=True,
                    model_provider=FailingProvider(),
                ),
            )
            self.assertEqual(report.decision, "WARN")
            self.assertTrue(any("review_error" in item for item in report.semantic_reviews))
        finally:
            td.cleanup()

    def test_deleted_task_is_reported(self) -> None:
        root, td = Stage7AssuranceTests()._repo()
        try:
            task = root / "corpus" / "tasks" / "tiny-release"
            for child in task.iterdir():
                child.unlink()
            task.rmdir()
            subprocess.run(["git", "add", "-A"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "delete-task"], cwd=root, check=True)
            report = release_assurance(
                root,
                task_root=root / "corpus" / "tasks",
                config=RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False),
            )
            self.assertEqual(report.decision, "WARN")
            self.assertTrue(report.deleted_task_paths)
        finally:
            td.cleanup()
