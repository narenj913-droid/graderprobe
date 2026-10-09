"""Execute DeepEval #3025 against the actual installed upstream package."""
from __future__ import annotations

import asyncio
import runpy
import sys
from pathlib import Path

try:
    import deepeval
    from deepeval.metrics import DAGMetric
    from deepeval.metrics.dag import TaskNode, BinaryJudgementNode, DeepAcyclicGraph
    from deepeval.models import DeepEvalBaseLLM
    from deepeval.test_case import LLMTestCase, SingleTurnParams
except Exception as exc:
    print(f"DEEP_EVAL_IMPORT_ERROR={type(exc).__name__}: {exc}", file=sys.stderr)
    raise SystemExit(10)

cfg = runpy.run_path(str(Path(__file__).with_name("solution.py")))
DEEP_FIRST = bool(cfg["DEEP_FIRST"])
ASYNC_MODE = bool(cfg["ASYNC_MODE"])
THRESHOLD = float(cfg["THRESHOLD"])
PARAMS = [SingleTurnParams.ACTUAL_OUTPUT]


class AlwaysYes(DeepEvalBaseLLM):
    """Deterministic judge: every reachable judgement returns True."""

    def load_model(self):
        return self

    def generate(self, prompt, schema=None, **kwargs):
        if schema.__name__ == "TaskNodeOutput":
            return schema(output=["Intro", "Body", "Conclusion"])
        return schema(verdict=True, reason="fixed")

    async def a_generate(self, prompt, schema=None, **kwargs):
        await asyncio.sleep(0)
        return self.generate(prompt, schema=schema, **kwargs)

    def get_model_name(self):
        return "always-yes"


def build(deep_first: bool) -> DeepAcyclicGraph:
    extract = TaskNode(
        instructions="Extract the headings",
        output_label="Headings",
        evaluation_params=PARAMS,
    )
    deep = BinaryJudgementNode(criteria="All three headings present?")
    inner = BinaryJudgementNode(criteria="Headings in the right order?")
    shallow = BinaryJudgementNode(criteria="Summary under 100 words?")

    if deep_first:
        extract.add_node(deep)
        extract.add_node(shallow)
    else:
        extract.add_node(shallow)
        extract.add_node(deep)

    deep.add_verdict(True, then=inner)
    deep.add_verdict(False, score=0)
    inner.add_verdict(True, score=10)
    inner.add_verdict(False, score=0)
    shallow.add_verdict(True, score=5)
    shallow.add_verdict(False, score=0)
    return DeepAcyclicGraph(root_nodes=[extract])


def run() -> float:
    metric = DAGMetric(
        name="Summary",
        dag=build(DEEP_FIRST),
        model=AlwaysYes(model="always-yes"),
        include_reason=False,
        async_mode=ASYNC_MODE,
    )
    case = LLMTestCase(input="Summarize.", actual_output="Intro\n Body\n Conclusion")
    metric.measure(case, _show_indicator=False)
    return float(metric.score)

score = run()
print(f"SCORE={score:.6f}")
print(f"THRESHOLD={THRESHOLD:.6f}")
print(f"DEEP_FIRST={str(DEEP_FIRST).lower()}")
print(f"ASYNC_MODE={str(ASYNC_MODE).lower()}")
print(f"VERDICT={'PASS' if score >= THRESHOLD else 'FAIL'}")
print(f"DEEPEVAL_VERSION={getattr(deepeval, '__version__', 'unknown')}")
raise SystemExit(0 if score >= THRESHOLD else 1)
