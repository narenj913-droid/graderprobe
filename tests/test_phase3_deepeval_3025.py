from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "corpus/external-trials/deepeval-3025"
ORDER_CASE = ROOT / "corpus/external-trials/deepeval-3025-declaration-order"


def _load(path: Path) -> dict[str, object]:
    ns: dict[str, object] = {}
    exec(path.read_text(encoding="utf-8"), ns)
    return {k: ns[k] for k in ("DEEP_FIRST", "ASYNC_MODE", "THRESHOLD")}


class DeepEval3025CounterfactualTests(unittest.TestCase):
    def test_counterfactuals_change_only_the_stated_axis(self) -> None:
        base = _load(CASE / "solution.py")
        sync = _load(CASE / "alternatives/sync_same_order.py")
        order = _load(CASE / "alternatives/shallow_first_async.py")
        self.assertEqual(base["THRESHOLD"], sync["THRESHOLD"])
        self.assertEqual(base["THRESHOLD"], order["THRESHOLD"])
        self.assertEqual(base["DEEP_FIRST"], sync["DEEP_FIRST"])
        self.assertNotEqual(base["ASYNC_MODE"], sync["ASYNC_MODE"])
        self.assertEqual(base["ASYNC_MODE"], order["ASYNC_MODE"])
        self.assertNotEqual(base["DEEP_FIRST"], order["DEEP_FIRST"])

    def test_declaration_order_companion_has_order_only_delta(self) -> None:
        base = _load(ORDER_CASE / "solution.py")
        mut = _load(ORDER_CASE / "alternatives/deep_first_sync.py")
        self.assertFalse(base["ASYNC_MODE"])
        self.assertFalse(mut["ASYNC_MODE"])
        self.assertEqual(base["THRESHOLD"], mut["THRESHOLD"])
        self.assertNotEqual(base["DEEP_FIRST"], mut["DEEP_FIRST"])


if __name__ == "__main__":
    unittest.main()
