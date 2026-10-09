from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from graderprobe.cli import main
from graderprobe.hashes import merkle_like, sha256_text
from graderprobe.metrics import compute_metrics, wilson_interval
from graderprobe.providers.base import NullProvider, proposals_to_specs
from graderprobe.types import (
    FindingType,
    ProbeClass,
    ProbeSpec,
    TransformSpec,
    ExpectedRelation,
)
from graderprobe.findings import Finding
from graderprobe.types import Severity


class MetricsTests(unittest.TestCase):
    def test_rates_none_when_empty(self) -> None:
        metrics = compute_metrics([], probe_classes={})
        self.assertIsNone(metrics.invariance_preservation_rate)
        self.assertEqual(metrics.false_acceptance_count, 0)

    def test_wilson_refuses_small_n(self) -> None:
        self.assertIsNone(wilson_interval(7, 14))

    def test_wilson_large_n(self) -> None:
        interval = wilson_interval(80, 100)
        self.assertIsNotNone(interval)
        assert interval is not None
        low, high = interval
        self.assertLess(low, 0.8)
        self.assertGreater(high, 0.8)

    def test_error_rate(self) -> None:
        probe = ProbeSpec(
            id="X",
            probe_class=ProbeClass.INVARIANCE,
            description="d",
            expected_relation=ExpectedRelation.PRESERVE,
            transform=TransformSpec(kind="insert_comments"),
        )
        findings = [
            Finding(
                id="1",
                type=FindingType.EXECUTION_ERROR,
                severity=Severity.MEDIUM,
                probe_id="X",
                summary="e",
                evidence={"baseline": "PASS"},
            )
        ]
        metrics = compute_metrics(findings, probe_classes={"X": ProbeClass.INVARIANCE})
        self.assertEqual(metrics.probe_execution_error_rate, 1.0)


class HashTests(unittest.TestCase):
    def test_stable(self) -> None:
        self.assertEqual(sha256_text("a"), sha256_text("a"))
        self.assertEqual(merkle_like({"a": "1"}), merkle_like({"a": "1"}))
        self.assertNotEqual(merkle_like({"a": "1"}), merkle_like({"a": "2"}))


class ProviderTests(unittest.TestCase):
    def test_null_provider(self) -> None:
        from graderprobe.task import parse_task

        task = parse_task(
            {
                "id": "x",
                "description": "d",
                "oracle": {"reference": "solution.py"},
                "evaluator": {"command": ["true"]},
            }
        )
        self.assertEqual(NullProvider().propose_probes(task, "src"), [])
        self.assertEqual(proposals_to_specs([]), [])


class CliTests(unittest.TestCase):
    def test_help(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            main(["--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_validate_healthy(self) -> None:
        from graderprobe.corpus import corpus_dir

        code = main(["validate", str(corpus_dir() / "healthy-control" / "task.yaml")])
        self.assertEqual(code, 0)

    def test_validate_broken(self) -> None:
        from graderprobe.corpus import corpus_dir

        code = main(["validate", str(corpus_dir() / "broken-environment" / "task.yaml")])
        self.assertEqual(code, 4)

    def test_probe_lists(self) -> None:
        from graderprobe.corpus import corpus_dir

        code = main(["probe", str(corpus_dir() / "healthy-control" / "task.yaml"), "--auto"])
        self.assertEqual(code, 0)

    def test_run_writes_evidence(self) -> None:
        from graderprobe.corpus import corpus_dir

        with TemporaryDirectory() as tmp:
            code = main(
                [
                    "run",
                    str(corpus_dir() / "healthy-control" / "task.yaml"),
                    "--out",
                    tmp,
                    "--fail-on",
                    "none",
                ]
            )
            self.assertEqual(code, 0)
            profile = Path(tmp) / "profile.json"
            cert = Path(tmp) / "CERTIFICATE.json"
            self.assertTrue(profile.is_file())
            self.assertTrue(cert.is_file())
            raw = json.loads(profile.read_text(encoding="utf-8"))
            self.assertEqual(raw["verdict"], "BOUNDARY_OK")
            cert_raw = json.loads(cert.read_text(encoding="utf-8"))
            self.assertIn("hashes", cert_raw)
            self.assertIn("disclaimer", cert_raw)

    def test_report(self) -> None:
        from graderprobe.corpus import corpus_dir

        with TemporaryDirectory() as tmp:
            main(
                [
                    "run",
                    str(corpus_dir() / "healthy-control" / "task.yaml"),
                    "--out",
                    tmp,
                    "--fail-on",
                    "none",
                ]
            )
            self.assertEqual(main(["report", str(Path(tmp) / "profile.json")]), 0)


if __name__ == "__main__":
    unittest.main()
