"""Run the real DeepEval ToolCorrectnessMetric in a deterministic offline lane."""
from __future__ import annotations
import os, runpy, sys
from pathlib import Path
# These values are dummy/offline only; the metric lane must not call a model API.
os.environ["OPENAI_API_KEY"] = "graderprobe-offline-dummy-no-calls"
os.environ["DEEPEVAL_DISABLE_DOTENV"] = "1"
os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"
try:
    import deepeval
    from deepeval.metrics import ToolCorrectnessMetric
    from deepeval.test_case import LLMTestCase, ToolCall, ToolCallParams
except Exception as exc:
    print(f"DEEP_EVAL_IMPORT_ERROR={type(exc).__name__}: {exc}", file=sys.stderr)
    raise SystemExit(10)
cfg = runpy.run_path(Path(__file__).with_name("solution.py"))
expected = [ToolCall(name=x["name"], input_parameters=x["input_parameters"]) for x in cfg["EXPECTED"]]
called = [ToolCall(name=x["name"], input_parameters=x["input_parameters"]) for x in cfg["CALLED"]]
threshold = float(cfg["THRESHOLD"])
metric = ToolCorrectnessMetric(threshold=threshold, async_mode=False, evaluation_params=[ToolCallParams.INPUT_PARAMETERS], should_consider_ordering=bool(cfg["SHOULD_CONSIDER_ORDERING"]), should_exact_match=bool(cfg["SHOULD_EXACT_MATCH"]))
case = LLMTestCase(input="Offline evaluator-contract test", actual_output="Offline output", tools_called=called, expected_tools=expected)
metric.measure(case, _show_indicator=False)
score = float(metric.score)
passed = score >= threshold
print(f"DEEPEVAL_VERSION={getattr(deepeval, '__version__', 'unknown')}")
print(f"SCORE={score:.12f}")
print(f"THRESHOLD={threshold:.12f}")
print(f"VERDICT={'PASS' if passed else 'FAIL'}")
raise SystemExit(0 if passed else 1)
