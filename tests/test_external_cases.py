from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ExternalCaseReproductionTests(unittest.TestCase):
    def _run(self, task_rel: str) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "profile"
            env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "graderprobe",
                    "run",
                    task_rel,
                    "--out",
                    str(out),
                    "--workers",
                    "1",
                    "--execution-slots",
                    "1",
                    "--fail-on",
                    "high",
                ],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=20,
            )
            self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
            return json.loads((out / "profile.json").read_text(encoding="utf-8"))

    def test_deepeval_3338_is_detected_as_high_false_rejection(self) -> None:
        profile = self._run("corpus/external-cases/deepeval-3338/task.yaml")
        self.assertEqual(profile["verdict"], "BOUNDARY_FAIL")
        self.assertEqual(profile["metrics"]["false_rejection_count"], 1)
        self.assertEqual(profile["findings"][0]["severity"], "high")
        self.assertEqual(profile["findings"][0]["evidence"]["original_behavior_verdict"], "PASS")
        self.assertEqual(profile["findings"][0]["evidence"]["transformed_behavior_verdict"], "PASS")
        self.assertEqual(profile["baseline"]["runs"][0]["stdout"].splitlines()[1], "SCORE=0.666667")
        self.assertIn("SCORE=0.500000", profile["pairs"][0]["probe_execution"]["stdout"])

    def test_inspect_ai_4721_is_detected_as_high_false_rejection(self) -> None:
        profile = self._run("corpus/external-cases/inspect-ai-4721/task.yaml")
        self.assertEqual(profile["verdict"], "BOUNDARY_FAIL")
        self.assertEqual(profile["metrics"]["false_rejection_count"], 1)
        self.assertEqual(profile["findings"][0]["severity"], "high")
        self.assertEqual(profile["findings"][0]["evidence"]["original_behavior_verdict"], "PASS")
        self.assertEqual(profile["findings"][0]["evidence"]["transformed_behavior_verdict"], "PASS")


if __name__ == "__main__":
    unittest.main()
