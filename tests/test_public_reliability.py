from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class PublicReliabilityTests(unittest.TestCase):
    def test_cli_healthy_control_smoke_is_offline_and_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "graderprobe",
                    "run",
                    "corpus/tasks/healthy-control/task.yaml",
                    "--out",
                    str(out),
                    "--fail-on",
                    "high",
                    "--workers",
                    "1",
                    "--execution-slots",
                    "1",
                ],
                capture_output=True,
                text=True,
                timeout=20,
                env={**__import__("os").environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"), "OPENAI_API_KEY": ""},
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            profile = json.loads((out / "profile.json").read_text(encoding="utf-8"))
            self.assertEqual(profile["verdict"], "BOUNDARY_OK")
            self.assertFalse(profile.get("api_usage"))
            self.assertTrue((out / "replay.json").is_file())

    def test_public_gate_reuses_bounded_cli_smoke_test(self) -> None:
        script = Path("scripts/public_reliability_gate.sh").read_text(encoding="utf-8")
        smoke_test = Path("tests/test_public_reliability.py").read_text(encoding="utf-8")
        self.assertIn("python -m unittest -q tests.test_public_reliability", script)
        self.assertIn("timeout=20", smoke_test)

    def test_contract_lock_is_required_and_missing_lock_fails_explicitly(self) -> None:
        workflow = Path(".github/workflows/contract-lock.yml").read_text(encoding="utf-8")
        self.assertIn("Require committed evaluation contract lock", workflow)
        self.assertIn("if [ ! -f graderprobe.lock.json ]", workflow)
        self.assertIn("graderprobe.lock.json is required", workflow)
        self.assertNotIn("hashFiles('graderprobe.lock.json') != ''", workflow)


if __name__ == "__main__":
    unittest.main()
