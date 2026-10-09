from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from graderprobe.probes.transforms import TransformError, apply_transform
from graderprobe.types import TransformSpec


SRC = """
def add(a, b):
    return a + b
"""


class TransformTests(unittest.TestCase):
    def test_rename(self) -> None:
        out = apply_transform(
            SRC,
            TransformSpec(kind="rename_identifiers", params={"mapping": {"a": "x", "b": "y"}}),
            workspace=Path("."),
            target="solution.py",
        )
        self.assertIn("def add(x, y)", out)

    def test_expand_return(self) -> None:
        out = apply_transform(
            SRC,
            TransformSpec(kind="expand_return", params={"name": "tmp"}),
            workspace=Path("."),
            target="solution.py",
        )
        self.assertIn("tmp =", out)
        self.assertIn("return tmp", out)

    def test_flip_operator(self) -> None:
        src = "def f(n):\n    return n >= 18\n"
        out = apply_transform(
            src, TransformSpec(kind="flip_operator"), workspace=Path("."), target="s.py"
        )
        self.assertIn(">", out)
        self.assertNotIn(">=", out)

    def test_replace_file(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "alt.py"
            path.write_text("ok\n", encoding="utf-8")
            out = apply_transform(
                "old",
                TransformSpec(kind="replace_file", params={"source": "alt.py"}),
                workspace=Path(tmp),
                target="solution.py",
            )
            self.assertEqual(out, "ok\n")

    def test_unknown_kind(self) -> None:
        with self.assertRaises(TransformError):
            apply_transform("x", TransformSpec(kind="nope"), workspace=Path("."), target="s.py")

    def test_delete_matching(self) -> None:
        src = "a = 1\n# drop me\nb = 2\n"
        out = apply_transform(
            src,
            TransformSpec(kind="delete_matching", params={"pattern": "drop me"}),
            workspace=Path("."),
            target="s.py",
        )
        self.assertNotIn("drop me", out)
        self.assertIn("b = 2", out)

    def test_wrap_function(self) -> None:
        out = apply_transform(
            SRC,
            TransformSpec(kind="wrap_function", params={"function": "add", "helper": "add_impl"}),
            workspace=Path("."),
            target="s.py",
        )
        self.assertIn("def add_impl", out)
        self.assertIn("def add", out)

    def test_model_generated_still_needs_real_kind(self) -> None:
        with self.assertRaises(TransformError):
            apply_transform("x", TransformSpec(kind="llm_magic"), workspace=Path("."), target="s.py")


if __name__ == "__main__":
    unittest.main()
