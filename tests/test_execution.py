from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from graderprobe.execution import interpret_verdict, run_evaluator
from graderprobe.isolation import IsolatedWorkspace
from graderprobe.types import EvaluatorSpec, Verdict


class ExecutionTests(unittest.TestCase):
    def test_timeout_is_not_fail(self) -> None:
        with TemporaryDirectory() as tmp:
            src = Path(tmp)
            (src / "spin.py").write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
            spec = EvaluatorSpec(command=["python", "spin.py"], timeout_seconds=0.4)
            with IsolatedWorkspace(src) as workspace:
                result = run_evaluator(workspace, spec)
            self.assertEqual(result.verdict, Verdict.TIMEOUT)
            self.assertTrue(result.timed_out)

    def test_unknown_exit_is_error_not_fail(self) -> None:
        spec = EvaluatorSpec(
            command=["python", "-c", "raise SystemExit(9)"],
            pass_exit_codes=(0,),
            fail_exit_codes=(1,),
        )
        verdict = interpret_verdict(
            spec, exit_code=9, stdout="", stderr="", timed_out=False, error_message=""
        )
        self.assertEqual(verdict, Verdict.ERROR)

    def test_marker_overrides_exit(self) -> None:
        spec = EvaluatorSpec(command=["true"], verdict_protocol="marker")
        verdict = interpret_verdict(
            spec,
            exit_code=0,
            stdout="GRADERPROBE_VERDICT: INCONCLUSIVE\n",
            stderr="",
            timed_out=False,
            error_message="",
        )
        self.assertEqual(verdict, Verdict.INCONCLUSIVE)

    def test_pass_fail(self) -> None:
        spec = EvaluatorSpec(command=["true"])
        self.assertEqual(
            interpret_verdict(
                spec, exit_code=0, stdout="", stderr="", timed_out=False, error_message=""
            ),
            Verdict.PASS,
        )
        self.assertEqual(
            interpret_verdict(
                spec, exit_code=1, stdout="", stderr="", timed_out=False, error_message=""
            ),
            Verdict.FAIL,
        )


if __name__ == "__main__":
    unittest.main()
