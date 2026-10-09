from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from graderprobe.cli import main
from graderprobe.git import changed_task_files
from graderprobe.integrations.harbor import inspect_harbor_task
from graderprobe.providers.openai import OpenAIProvider
from graderprobe.reports.sarif import profile_to_sarif, profiles_to_sarif
from graderprobe.task import load_task


class Stage6EcosystemTests(unittest.TestCase):
    def test_sarif_is_2_1_0_and_actionable(self) -> None:
        task = load_task(Path("corpus/tasks/under-constrained-auth/task.yaml"))
        from graderprobe.runner import RunConfig, run_task
        profile = run_task(task, config=RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False))
        sarif = profile_to_sarif(profile.to_dict())
        self.assertEqual(sarif["version"], "2.1.0")
        self.assertEqual(sarif["runs"][0]["tool"]["driver"]["name"], "GraderProbe")
        self.assertEqual(len(sarif["runs"][0]["results"]), 2)
        self.assertEqual(sarif["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"], "solution.py")

    def test_combined_sarif(self) -> None:
        one = {"task_id": "a", "verdict": "BOUNDARY_FAIL", "findings": [{"type": "false_acceptance", "severity": "high", "probe_id": "x", "summary": "bad", "evidence": {"target": "solution.py"}}]}
        two = {"task_id": "b", "verdict": "BOUNDARY_WARNING", "findings": [{"type": "false_rejection", "severity": "medium", "probe_id": "y", "summary": "strict", "evidence": {"target": "main.py"}}]}
        sarif = profiles_to_sarif([one, two])
        self.assertEqual(len(sarif["runs"][0]["results"]), 2)
        self.assertEqual(len(sarif["runs"][0]["tool"]["driver"]["rules"]), 2)

    def test_harbor_inspector_current_schema(self) -> None:
        fixture = Path("examples/harbor-task")
        m = inspect_harbor_task(fixture)
        self.assertEqual(m.task_id, "graderprobe/demo-harbor")
        self.assertEqual(m.task_name, "graderprobe/demo-harbor")
        self.assertEqual(m.schema_version, "1.4")
        self.assertTrue(m.has_instruction)
        self.assertTrue(m.has_verifier)
        self.assertTrue(m.has_solution)
        self.assertTrue(m.has_environment)
        self.assertEqual(m.environment_network_mode, "no-network")
        self.assertEqual(m.suggested_verifier_command, ("bash", "tests/test.sh"))

    def test_changed_task_files_finds_nearest_task(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            taskdir = root / "tasks" / "one"
            taskdir.mkdir(parents=True)
            (taskdir / "task.yaml").write_text(
                "id: one\ndescription: x\nrequirements: []\nconstraints: []\nfailure_conditions: []\nimplementation_freedom: []\noracle: {reference: solution.py}\nevaluator: {command: [true]}\n",
                encoding="utf-8",
            )
            (taskdir / "solution.py").write_text("x=1\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=root, check=True)
            (taskdir / "solution.py").write_text("x=2\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "change"], cwd=root, check=True)
            changed = changed_task_files(root, base_ref="HEAD~1")
            self.assertEqual(changed, [(taskdir / "task.yaml").resolve()])

    def test_harbor_cli(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "manifest.json"
            self.assertEqual(main(["harbor-inspect", "examples/harbor-task", "--out", str(out)]), 0)
            raw = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(raw["task_name"], "graderprobe/demo-harbor")


class OpenAIProviderTests(unittest.TestCase):
    def test_provider_rejects_missing_key(self) -> None:
        old = os.environ.pop("OPENAI_API_KEY", None)
        try:
            with self.assertRaises(ValueError):
                OpenAIProvider()
        finally:
            if old is not None:
                os.environ["OPENAI_API_KEY"] = old

    def test_provider_requires_explicit_model(self) -> None:
        old_key = os.environ.get("OPENAI_API_KEY")
        old_model = os.environ.pop("GRADERPROBE_OPENAI_MODEL", None)
        try:
            os.environ["OPENAI_API_KEY"] = "test-key"
            with self.assertRaises(ValueError):
                OpenAIProvider()
        finally:
            if old_key is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = old_key
            if old_model is not None:
                os.environ["GRADERPROBE_OPENAI_MODEL"] = old_model

    def test_parse_structured_response_without_network(self) -> None:
        body = json.dumps({
            "output_text": json.dumps({
                "proposals": [{
                    "description": "flip one boundary comparison",
                    "kind": "ast_flip_comparison",
                    "params": {"lineno": 3},
                    "rationale": "targets a stated boundary",
                }]
            })
        }).encode()

        class Resp:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return body

        provider = OpenAIProvider(api_key="test-key", model="test-model")
        task = load_task(Path("corpus/tasks/healthy-control/task.yaml"))
        with patch.object(urllib.request, "urlopen", return_value=Resp()) as mocked:
            proposals = provider.propose_probes(task, "def f(x):\n return x\n")
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].transform.kind, "ast_flip_comparison")
        mocked.assert_called_once()


if __name__ == "__main__":
    unittest.main()

class ReplayModelProbeTests(unittest.TestCase):
    def test_replay_manifest_preserves_model_probe_spec(self) -> None:
        from graderprobe.providers.base import Proposal
        from graderprobe.runner import RunConfig, run_task
        from graderprobe.replay import build_replay_manifest
        task = load_task(Path("corpus/tasks/healthy-control/task.yaml"))

        class FakeProvider:
            name = "fake"
            def propose_probes(self, task, source):
                return [Proposal(
                    description="flip first comparison",
                    transform=__import__("graderprobe.types", fromlist=["TransformSpec"]).TransformSpec(
                        kind="ast_flip_comparison", params={"lineno": 2}
                    ),
                    rationale="test replay preservation",
                )]

        config = RunConfig(
            max_workers=1,
            execution_slots=1,
            include_model_probes=True,
            model_provider=FakeProvider(),
        )
        profile = run_task(task, config=config)
        manifest = build_replay_manifest(task, profile, Path("/tmp/profile.json"), config)
        self.assertEqual(len(manifest["model_probes"]), 1)
        self.assertEqual(manifest["model_probes"][0]["transform"]["kind"], "ast_flip_comparison")
        self.assertFalse(manifest["config"]["include_model_probes"] is False)
