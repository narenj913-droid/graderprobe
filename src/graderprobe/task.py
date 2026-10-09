"""Load and validate native GraderProbe task documents."""

from __future__ import annotations

import json
from pathlib import Path, PureWindowsPath
from typing import Any

import yaml

from jsonschema import Draft202012Validator

from graderprobe.types import (
    ArtifactRef,
    EvaluatorSpec,
    ExpectedRelation,
    OracleSpec,
    ProbeClass,
    ProbeMethod,
    ProbeSpec,
    TaskSpec,
    TransformSpec,
    Verdict,
)


REQUIRED_TOP = ("id", "description", "oracle", "evaluator")
_SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "task.schema.json"


class TaskError(ValueError):
    """Raised when a task document is structurally invalid."""


def load_task(path: str | Path) -> TaskSpec:
    path = Path(path).resolve()
    if not path.is_file():
        raise TaskError(f"task file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TaskError("task document must be a mapping")
    return parse_task(raw, source_path=str(path.parent))


def parse_task(raw: dict[str, Any], *, source_path: str = "") -> TaskSpec:
    try:
        validator = Draft202012Validator(_load_task_schema())
        errors = sorted(validator.iter_errors(raw), key=lambda error: list(error.absolute_path))
    except OSError as exc:
        raise TaskError(f"task schema unavailable: {exc}") from exc
    if errors:
        details = "; ".join(_format_schema_error(error) for error in errors[:8])
        if len(errors) > 8:
            details += f"; and {len(errors) - 8} more"
        raise TaskError(f"task schema validation failed: {details}")

    missing = [key for key in REQUIRED_TOP if key not in raw]
    if missing:
        raise TaskError(f"task missing required keys: {missing}")

    oracle_raw = raw["oracle"] or {}
    evaluator_raw = raw["evaluator"] or {}
    interpretation = evaluator_raw.get("interpretation") or {}
    probes_raw = raw.get("probes") or {}

    command = evaluator_raw.get("command")
    if isinstance(command, str):
        command = ["sh", "-c", command]
    if not isinstance(command, list) or not command:
        raise TaskError("evaluator.command must be a non-empty list or string")

    expected_verdict = _verdict(
        oracle_raw.get("expected_baseline_verdict", "PASS"),
        field_name="oracle.expected_baseline_verdict",
    )

    task = TaskSpec(
        id=str(raw["id"]),
        title=str(raw.get("title") or raw["id"]),
        description=str(raw["description"]).strip(),
        requirements=_str_list(raw.get("requirements")),
        constraints=_str_list(raw.get("constraints")),
        implementation_freedom=_str_list(raw.get("implementation_freedom")),
        failure_conditions=_str_list(raw.get("failure_conditions")),
        artifacts=_artifacts(raw.get("artifacts")),
        oracle=OracleSpec(
            reference=str(oracle_raw.get("reference", "solution.py")),
            expected_behavior=str(oracle_raw.get("expected_behavior", "")),
            expected_baseline_verdict=expected_verdict,
            known_invalid=oracle_raw.get("known_invalid"),
            known_invalid_verdict=_verdict(
                oracle_raw.get("known_invalid_verdict", "FAIL"),
                field_name="oracle.known_invalid_verdict",
            ),
        ),
        evaluator=_parse_execution_spec(evaluator_raw, field_name="evaluator"),
        behavior_validator=(
            _parse_execution_spec(raw.get("behavior_validator"), field_name="behavior_validator")
            if raw.get("behavior_validator") is not None
            else None
        ),
        invariance_probes=_probes(probes_raw.get("invariance"), ProbeClass.INVARIANCE),
        sensitivity_probes=_probes(probes_raw.get("sensitivity"), ProbeClass.SENSITIVITY),
        provenance=dict(raw.get("provenance") or {}),
        failure_mode=str(raw.get("failure_mode", "")),
        source_path=source_path,
        baseline_repeats=max(1, int(raw.get("baseline_repeats", 1))),
        candidate_file=str(raw.get("candidate_file", "solution.py")),
        metadata=dict(raw.get("metadata") or {}),
    )
    _validate_task(task)
    return task


def _parse_execution_spec(raw: Any, *, field_name: str) -> EvaluatorSpec:
    if not isinstance(raw, dict):
        raise TaskError(f"{field_name} must be a mapping")
    interpretation = raw.get("interpretation") or {}
    command = raw.get("command")
    if isinstance(command, str):
        command = ["sh", "-c", command]
    if not isinstance(command, list) or not command:
        raise TaskError(f"{field_name}.command must be a non-empty list or string")
    sandbox = raw.get("sandbox") or {}
    if not isinstance(sandbox, dict):
        raise TaskError(f"{field_name}.sandbox must be a mapping")
    backend = str(sandbox.get("backend", "process"))
    if backend not in {"process", "docker"}:
        raise TaskError(f"{field_name}.sandbox.backend must be process or docker")
    container_network = str(sandbox.get("network", "none"))
    if container_network not in {"none", "bridge"}:
        raise TaskError(f"{field_name}.sandbox.network must be none or bridge")
    image = sandbox.get("image")
    if backend == "docker" and not image:
        raise TaskError(f"{field_name}.sandbox.image is required for docker backend")
    return EvaluatorSpec(
        command=[str(part) for part in command],
        timeout_seconds=float(raw.get("timeout_seconds", 8)),
        working_dir=str(raw.get("working_dir", ".")),
        pass_exit_codes=_int_tuple(interpretation.get("pass_exit_codes", [0])),
        fail_exit_codes=_int_tuple(interpretation.get("fail_exit_codes", [1])),
        inconclusive_exit_codes=_int_tuple(interpretation.get("inconclusive_exit_codes", [2])),
        verdict_protocol=str(interpretation.get("verdict_protocol", "exit_code")),
        environment={str(k): str(v) for k, v in (raw.get("environment") or {}).items()},
        network=str(raw.get("network", "unrestricted")),
        interpretation_notes=str(interpretation.get("notes", "")),
        backend=backend,
        container_image=None if image is None else str(image),
        container_network=container_network,
        container_memory=str(sandbox.get("memory", "512m")),
        container_cpus=str(sandbox.get("cpus", "1.0")),
    )

def _validate_task(task: TaskSpec) -> None:
    if not task.id.strip():
        raise TaskError("task.id must be non-empty")
    _validate_relative_path(task.candidate_file, "candidate_file")
    _validate_relative_path(task.oracle.reference, "oracle.reference")
    if task.oracle.known_invalid:
        _validate_relative_path(task.oracle.known_invalid, "oracle.known_invalid")
        if task.oracle.known_invalid_verdict not in {Verdict.PASS, Verdict.FAIL}:
            raise TaskError("oracle.known_invalid_verdict must be PASS or FAIL")
    _validate_relative_path(task.evaluator.working_dir, "evaluator.working_dir")
    if task.evaluator.verdict_protocol not in {"exit_code", "marker"}:
        raise TaskError(
            "evaluator.interpretation.verdict_protocol must be 'exit_code' or 'marker'"
        )
    overlap = set(task.evaluator.pass_exit_codes) & (
        set(task.evaluator.fail_exit_codes) | set(task.evaluator.inconclusive_exit_codes)
    )
    if overlap:
        raise TaskError(f"evaluator exit codes overlap: {sorted(overlap)}")
    seen: set[str] = set()
    for probe in task.all_probes():
        if probe.id in seen:
            raise TaskError(f"duplicate probe id: {probe.id}")
        seen.add(probe.id)
        _validate_relative_path(probe.target, f"probe.{probe.id}.target")
        if probe.method is ProbeMethod.MODEL_GENERATED:
            if not probe.description:
                raise TaskError(f"{probe.id}: MODEL_GENERATED probe needs a description")
        if probe.probe_class is ProbeClass.INVARIANCE:
            if probe.expected_relation is not ExpectedRelation.PRESERVE:
                raise TaskError(f"{probe.id}: invariance probes must preserve")
        if probe.probe_class is ProbeClass.SENSITIVITY:
            if probe.expected_relation is not ExpectedRelation.INVALIDATE:
                raise TaskError(f"{probe.id}: sensitivity probes must invalidate")


def _probes(raw: Any, probe_class: ProbeClass) -> list[ProbeSpec]:
    if not raw:
        return []
    if not isinstance(raw, list):
        raise TaskError(f"probes.{probe_class.value} must be a list")
    out: list[ProbeSpec] = []
    default_relation = (
        ExpectedRelation.PRESERVE
        if probe_class is ProbeClass.INVARIANCE
        else ExpectedRelation.INVALIDATE
    )
    for item in raw:
        if not isinstance(item, dict):
            raise TaskError("each probe must be a mapping")
        transform_raw = item.get("transform") or {}
        if not transform_raw.get("kind"):
            raise TaskError(f"probe {item.get('id')!r} missing transform.kind")
        method_raw = str(item.get("method", "deterministic"))
        try:
            method = ProbeMethod(method_raw) if method_raw != "deterministic" else ProbeMethod.DETERMINISTIC
        except ValueError as exc:
            raise TaskError(f"unknown probe method: {method_raw}") from exc
        relation_raw = item.get("expected_relation", default_relation.value)
        try:
            relation = ExpectedRelation(str(relation_raw))
        except ValueError as exc:
            raise TaskError(f"unknown expected_relation: {relation_raw}") from exc
        params = {k: v for k, v in transform_raw.items() if k != "kind"}
        out.append(
            ProbeSpec(
                id=str(item["id"]),
                probe_class=probe_class,
                description=str(item.get("description", "")),
                expected_relation=relation,
                transform=TransformSpec(kind=str(transform_raw["kind"]), params=params),
                method=method,
                target=str(item.get("target", "solution.py")),
                notes=str(item.get("notes", "")),
            )
        )
    return out


def _artifacts(raw: Any) -> list[ArtifactRef]:
    if not raw:
        return [ArtifactRef(path="solution.py")]
    out: list[ArtifactRef] = []
    for item in raw:
        if isinstance(item, str):
            out.append(ArtifactRef(path=item))
            continue
        out.append(
            ArtifactRef(
                path=str(item["path"]),
                role=str(item.get("role", "candidate")),
                language=str(item.get("language", "python")),
            )
        )
    return out


def _str_list(raw: Any) -> list[str]:
    if not raw:
        return []
    return [str(item) for item in raw]


def _int_tuple(raw: Any) -> tuple[int, ...]:
    return tuple(int(item) for item in raw)


def _validate_relative_path(value: str, field_name: str) -> None:
    if not value:
        raise TaskError(f"{field_name} must be non-empty")
    normalized = value.replace("\\", "/")
    if Path(value).is_absolute() or PureWindowsPath(value).is_absolute():
        raise TaskError(f"{field_name} must be relative: {value!r}")
    if any(part == ".." for part in normalized.split("/")):
        raise TaskError(f"{field_name} must not contain '..': {value!r}")


def _load_task_schema() -> dict[str, Any]:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _format_schema_error(error: Any) -> str:
    path = ".".join(str(part) for part in error.absolute_path) or "<root>"
    return f"{path}: {error.message}"


def _verdict(raw: Any, *, field_name: str) -> Verdict:
    try:
        return Verdict(str(raw))
    except ValueError as exc:
        raise TaskError(f"{field_name} has unknown verdict {raw!r}") from exc
