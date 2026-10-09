from __future__ import annotations

import unittest
from pathlib import Path

from graderprobe.probes.engine import ProbeEngine
from graderprobe.probes.transforms import TransformError, apply_transform
from graderprobe.types import TransformSpec


class Stage3ASTTests(unittest.TestCase):
    SRC = """
def clamp(x):
    if x <= 10:
        return 10
    return x
"""

    def test_targeted_ast_comparison_flip_changes_only_one_comparison(self) -> None:
        out = apply_transform(
            self.SRC,
            TransformSpec(kind="ast_flip_comparison", params={"lineno": 3}),
            workspace=Path("."),
            target="solution.py",
        )
        self.assertIn("if x < 10:", out)
        self.assertIn("return 10", out)

    def test_targeted_ast_comparison_rewrite_preserves_form(self) -> None:
        out = apply_transform(
            self.SRC,
            TransformSpec(kind="ast_rewrite_comparison", params={"lineno": 3}),
            workspace=Path("."),
            target="solution.py",
        )
        self.assertIn("if 10 >= x:", out)

    def test_targeted_ast_constant_replacement(self) -> None:
        out = apply_transform(
            self.SRC,
            TransformSpec(kind="ast_replace_constant", params={"from": 10, "to": 11, "lineno": 3}),
            workspace=Path("."),
            target="solution.py",
        )
        self.assertIn("if x <= 11:", out)

    def test_ast_flip_requires_target(self) -> None:
        with self.assertRaises(TransformError):
            apply_transform(
                self.SRC,
                TransformSpec(kind="ast_flip_comparison", params={"lineno": 99}),
                workspace=Path("."),
                target="solution.py",
            )

    def test_auto_probes_are_targeted(self) -> None:
        engine = ProbeEngine(None)  # type: ignore[arg-type]
        invariance = engine.auto_invariance(self.SRC)
        sensitivity = engine.auto_sensitivity(self.SRC)
        self.assertTrue(any(p.transform.kind == "rename_identifiers" for p in invariance))
        self.assertTrue(any(p.transform.kind == "ast_flip_comparison" for p in sensitivity))
        self.assertTrue(any(p.transform.kind == "ast_replace_constant" for p in sensitivity))


if __name__ == "__main__":
    unittest.main()
