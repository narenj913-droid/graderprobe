"""Execute Inspect AI #4721 against the actual installed upstream package."""
from __future__ import annotations

import asyncio
import runpy
import sys
from pathlib import Path

try:
    from inspect_ai.model import ModelOutput, get_model
    from inspect_ai.scorer import Target, model_graded_qa
    from inspect_ai.solver import TaskState
except Exception as exc:
    print(f"INSPECT_AI_IMPORT_ERROR={type(exc).__name__}: {exc}", file=sys.stderr)
    raise SystemExit(10)

order = list(runpy.run_path(Path(__file__).with_name("solution.py"))["ORDER"])

def grader(content: str):
    return get_model(
        "mockllm/model",
        custom_outputs=[ModelOutput.from_content("mockllm/model", content)],
    )

async def run() -> object:
    scorer = model_graded_qa(model=[grader(c) for c in order])
    state = TaskState(
        model="mockllm/model",
        sample_id=1,
        epoch=1,
        input="q",
        messages=[],
    )
    return await scorer(state, Target(["the answer"]))

score = asyncio.run(run())
print(f"VERDICT={score.value}")
print(f"INSPECT_AI_VERSION={getattr(sys.modules.get('inspect_ai'), '__version__', 'unknown')}")
raise SystemExit(0 if score.value == "C" else 1)
