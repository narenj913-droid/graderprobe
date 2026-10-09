from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from graderprobe.adapters.swebench import SWEBenchStyleAdapter
from graderprobe.task import load_task


class AdapterTests(unittest.TestCase):
    def test_local_roundtrip(self) -> None:
        from graderprobe.corpus import corpus_dir

        task = load_task(corpus_dir() / "healthy-control" / "task.yaml")
        self.assertEqual(task.id, "healthy-control")

    def test_swebench_style(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "inst.yaml"
            path.write_text(
                "instance_id: foo-1\nproblem_statement: fix it\ntest_cmd: [python, -m, pytest]\n",
                encoding="utf-8",
            )
            task = SWEBenchStyleAdapter().load(path)
            self.assertEqual(task.id, "foo-1")
            self.assertEqual(task.evaluator.command[0], "python")

    def test_swebench_requires_id(self) -> None:
        with self.assertRaises(ValueError):
            SWEBenchStyleAdapter().from_mapping({"problem_statement": "x"})


if __name__ == "__main__":
    unittest.main()
