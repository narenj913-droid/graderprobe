"""Execute DeepEval #3338 against the actual installed upstream package."""
from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

# ToolCorrectnessMetric instantiates OpenAIModel during __init__ even for deterministic
# parameter matching. Provide an offline dummy key so local execution succeeds without API calls.
os.environ.setdefault("OPENAI_API_KEY", "dummy-local-key-no-calls")
os.environ.setdefault("DEEPEVAL_DISABLE_DOTENV", "1")
os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")

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

metric = ToolCorrectnessMetric(
    async_mode=False,
    evaluation_params=[ToolCallParams.INPUT_PARAMETERS],
)
case = LLMTestCase(input="x", actual_output="x", tools_called=called, expected_tools=expected)
metric.measure(case, _show_indicator=False)
score = float(metric.score)
print(f"SCORE={score:.6f}")
print(f"THRESHOLD={threshold:.6f}")
print(f"VERDICT={'PASS' if score >= threshold else 'FAIL'}")
print(f"DEEPEVAL_VERSION={getattr(deepeval, '__version__', 'unknown')}")
raise SystemExit(0 if score >= threshold else 1)
