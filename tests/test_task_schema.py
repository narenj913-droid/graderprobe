from __future__ import annotations

import unittest
from pathlib import Path

from graderprobe.corpus import list_task_files, load_corpus
from graderprobe.task import TaskError, load_task, parse_task


class TaskSchemaTests(unittest.TestCase):
    def test_missing_keys(self) -> None:
        with self.assertRaises(TaskError):
            parse_task({"id": "x"})

    def test_invariance_must_preserve(self) -> None:
        with self.assertRaises(TaskError):
            parse_task(
                {
                    "id": "x",
                    "description": "d",
                    "oracle": {"reference": "solution.py"},
                    "evaluator": {"command": ["true"]},
                    "probes": {
                        "invariance": [
                            {
                                "id": "INV-01",
                                "expected_relation": "invalidate",
                                "transform": {"kind": "insert_comments"},
                            }
                        ]
                    },
                }
            )

    def test_duplicate_probe_ids(self) -> None:
        with self.assertRaises(TaskError):
            parse_task(
                {
                    "id": "x",
                    "description": "d",
                    "oracle": {"reference": "solution.py"},
                    "evaluator": {"command": ["true"]},
                    "probes": {
                        "invariance": [
                            {"id": "INV-01", "transform": {"kind": "insert_comments"}},
                            {"id": "INV-01", "transform": {"kind": "insert_comments"}},
                        ]
                    },
                }
            )

    def test_corpus_loads(self) -> None:
        files = list_task_files()
        self.assertGreaterEqual(len(files), 12)
        tasks = load_corpus()
        ids = {task.id for task in tasks}
        self.assertIn("healthy-control", ids)
        self.assertIn("over-strict-naming", ids)
        for path in files:
            task = load_task(path)
            self.assertTrue(task.id)
            self.assertTrue((Path(task.source_path) / "evaluator.py").is_file())
            self.assertTrue((Path(task.source_path) / task.candidate_file).is_file())


if __name__ == "__main__":
    unittest.main()
