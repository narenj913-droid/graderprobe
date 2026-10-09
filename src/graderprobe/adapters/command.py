from __future__ import annotations

from graderprobe.adapters.base import EvaluatorAdapter
from graderprobe.execution import run_evaluator
from graderprobe.isolation import IsolatedWorkspace
from graderprobe.types import EvaluatorSpec, ExecutionResult


class CommandEvaluatorAdapter(EvaluatorAdapter):
    """Default adapter: run an evaluator command in an isolated workspace."""

    def evaluate(self, workspace: IsolatedWorkspace, spec: EvaluatorSpec) -> ExecutionResult:
        return run_evaluator(workspace, spec)
