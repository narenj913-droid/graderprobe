"""Small in-process execution memoization used by expensive counterfactual loops.

The cache is deliberately scoped to one run. It stores no source text and never
becomes a correctness oracle. Callers opt in and the cache key includes the full
execution contract plus the candidate/workspace digest.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from graderprobe import __version__
from graderprobe.hashes import sha256_json, sha256_text
from graderprobe.types import EvaluatorSpec, ExecutionResult


@dataclass(frozen=True)
class CacheKey:
    value: str


class ExecutionMemo:
    """Bounded in-memory memo for identical deterministic-looking executions."""

    def __init__(self, max_entries: int = 256) -> None:
        self.max_entries = max(1, int(max_entries))
        self._data: dict[str, ExecutionResult] = {}
        self._order: list[str] = []

    def get(self, key: CacheKey) -> ExecutionResult | None:
        return self._data.get(key.value)

    def put(self, key: CacheKey, result: ExecutionResult) -> None:
        if key.value not in self._data:
            self._order.append(key.value)
        self._data[key.value] = result
        while len(self._order) > self.max_entries:
            old = self._order.pop(0)
            self._data.pop(old, None)

    def get_or_compute(
        self, key: CacheKey, compute: Callable[[], ExecutionResult]
    ) -> tuple[ExecutionResult, bool]:
        cached = self.get(key)
        if cached is not None:
            return cached, True
        result = compute()
        self.put(key, result)
        return result, False


def make_execution_key(
    *,
    workspace_digest: str,
    spec: EvaluatorSpec,
    attempt: int,
    inherit_secrets: bool,
) -> CacheKey:
    payload = {
        "graderprobe_version": __version__,
        "workspace": workspace_digest,
        "command": spec.command,
        "working_dir": spec.working_dir,
        "timeout": spec.timeout_seconds,
        "pass_exit_codes": spec.pass_exit_codes,
        "fail_exit_codes": spec.fail_exit_codes,
        "inconclusive_exit_codes": spec.inconclusive_exit_codes,
        "verdict_protocol": spec.verdict_protocol,
        "environment": spec.environment,
        "network": spec.network,
        "backend": spec.backend,
        "container_image": spec.container_image,
        "container_network": spec.container_network,
        "container_memory": spec.container_memory,
        "container_cpus": spec.container_cpus,
        "attempt": attempt,
        "inherit_secrets": inherit_secrets,
    }
    return CacheKey(sha256_json(payload))


def candidate_text_digest(candidate_text: str) -> str:
    return sha256_text(candidate_text)
