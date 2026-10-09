"""Generic evaluator and candidate adapter interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from graderprobe.isolation import IsolatedWorkspace
from graderprobe.types import EvaluatorSpec, ExecutionResult, TaskSpec


class EvaluatorAdapter(ABC):
    """Adapter around an evaluator that can score a candidate workspace."""

    @abstractmethod
    def evaluate(self, workspace: IsolatedWorkspace, spec: EvaluatorSpec) -> ExecutionResult:
        raise NotImplementedError


class CandidateAdapter(ABC):
    """Adapter that materializes a candidate into a workspace."""

    @abstractmethod
    def materialize(self, workspace: IsolatedWorkspace, source: Path, relative: str) -> None:
        raise NotImplementedError


class TaskAdapter(ABC):
    """Loads a task from an external benchmark format into TaskSpec."""

    @abstractmethod
    def load(self, path: Path) -> TaskSpec:
        raise NotImplementedError
