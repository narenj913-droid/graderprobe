"""Shared enumerations and dataclasses for GraderProbe."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    INCONCLUSIVE = "INCONCLUSIVE"
    BASELINE_INVALID = "BASELINE_INVALID"


class ProbeClass(str, Enum):
    INVARIANCE = "invariance"
    SENSITIVITY = "sensitivity"


class ExpectedRelation(str, Enum):
    PRESERVE = "preserve"
    INVALIDATE = "invalidate"


class FindingType(str, Enum):
    FALSE_ACCEPTANCE = "false_acceptance"
    FALSE_REJECTION = "false_rejection"
    INCONCLUSIVE = "inconclusive"
    EXECUTION_ERROR = "execution_error"
    BASELINE_INVALID = "baseline_invalid"
    RELATION_HELD = "relation_held"


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EvidenceLevel(str, Enum):
    UNVALIDATED = "UNVALIDATED"
    SMOKE_VALIDATED = "SMOKE_VALIDATED"
    REFERENCE_VALIDATED = "REFERENCE_VALIDATED"


class ProbeMethod(str, Enum):
    DETERMINISTIC = "deterministic"
    MODEL_GENERATED = "MODEL_GENERATED"


class ExecutionBackend(str, Enum):
    PROCESS = "process"
    DOCKER = "docker"


class ProfileVerdict(str, Enum):
    BOUNDARY_OK = "BOUNDARY_OK"
    BOUNDARY_WARNING = "BOUNDARY_WARNING"
    BOUNDARY_FAIL = "BOUNDARY_FAIL"
    BASELINE_INVALID = "BASELINE_INVALID"
    INCONCLUSIVE = "INCONCLUSIVE"


TERMINAL_FAIL_VERDICTS = frozenset({Verdict.FAIL})
NON_EVALUATIVE = frozenset(
    {Verdict.ERROR, Verdict.TIMEOUT, Verdict.INCONCLUSIVE, Verdict.BASELINE_INVALID}
)


def is_evaluative(verdict: Verdict) -> bool:
    return verdict in {Verdict.PASS, Verdict.FAIL}


@dataclass(frozen=True)
class ArtifactRef:
    path: str
    role: str = "candidate"
    language: str = "python"


@dataclass
class EvaluatorSpec:
    command: list[str]
    timeout_seconds: float = 8.0
    working_dir: str = "."
    pass_exit_codes: tuple[int, ...] = (0,)
    fail_exit_codes: tuple[int, ...] = (1,)
    inconclusive_exit_codes: tuple[int, ...] = (2,)
    verdict_protocol: str = "exit_code"
    environment: dict[str, str] = field(default_factory=dict)
    network: str = "unrestricted"
    interpretation_notes: str = ""
    backend: str = "process"
    container_image: str | None = None
    container_network: str = "none"
    container_memory: str = "512m"
    container_cpus: str = "1.0"


@dataclass
class TransformSpec:
    kind: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProbeSpec:
    id: str
    probe_class: ProbeClass
    description: str
    expected_relation: ExpectedRelation
    transform: TransformSpec
    method: ProbeMethod = ProbeMethod.DETERMINISTIC
    target: str = "solution.py"
    notes: str = ""


@dataclass
class OracleSpec:
    reference: str
    expected_behavior: str
    expected_baseline_verdict: Verdict = Verdict.PASS
    known_invalid: str | None = None
    known_invalid_verdict: Verdict = Verdict.FAIL


@dataclass
class TaskSpec:
    id: str
    title: str
    description: str
    requirements: list[str]
    constraints: list[str]
    implementation_freedom: list[str]
    failure_conditions: list[str]
    artifacts: list[ArtifactRef]
    oracle: OracleSpec
    evaluator: EvaluatorSpec
    invariance_probes: list[ProbeSpec]
    sensitivity_probes: list[ProbeSpec]
    provenance: dict[str, Any]
    behavior_validator: EvaluatorSpec | None = None
    failure_mode: str = ""
    source_path: str = ""
    baseline_repeats: int = 1
    candidate_file: str = "solution.py"
    metadata: dict[str, Any] = field(default_factory=dict)

    def all_probes(self) -> list[ProbeSpec]:
        return list(self.invariance_probes) + list(self.sensitivity_probes)


@dataclass
class ExecutionResult:
    verdict: Verdict
    exit_code: int | None
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool
    workspace: str
    command: list[str]
    environment: Mapping[str, str]
    error_message: str = ""
    attempt: int = 1
    cache_hit: bool = False
    cache_key: str = ""
    stdout_sha256: str = ""
    stderr_sha256: str = ""
    execution_contract_sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "exit_code": self.exit_code,
            "stdout": _clip(self.stdout),
            "stderr": _clip(self.stderr),
            "duration_ms": round(self.duration_ms, 3),
            "timed_out": self.timed_out,
            "workspace": self.workspace,
            "command": self.command,
            "error_message": self.error_message,
            "attempt": self.attempt,
            "cache_hit": self.cache_hit,
            "cache_key": self.cache_key,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
            "execution_contract_sha256": self.execution_contract_sha256,
        }


def _clip(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[truncated {len(text) - limit} chars]"
