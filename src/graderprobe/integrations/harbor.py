"""Read-only inspection of Harbor task packages.

Harbor is an external evaluation harness. This module deliberately avoids
claiming to be a Harbor runner; it validates the public task-package contract
and emits a portable bridge manifest.
"""
from __future__ import annotations

import json
try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:
        tomllib = None  # type: ignore
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HarborTaskManifest:
    path: str
    task_id: str
    task_name: str | None
    schema_version: str | None
    version: str | None
    verifier_path: str | None
    solution_path: str | None
    instruction_path: str | None
    environment_dockerfile: str | None
    verifier_timeout_sec: float | None
    agent_timeout_sec: float | None
    environment_network_mode: str | None
    verifier_network_mode: str | None
    has_task_toml: bool
    has_instruction: bool
    has_verifier: bool
    has_solution: bool
    has_environment: bool
    step_count: int
    warnings: tuple[str, ...]
    suggested_verifier_command: tuple[str, ...] | None = None
    suggested_solution_command: tuple[str, ...] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def inspect_harbor_task(path: str | Path) -> HarborTaskManifest:
    root = Path(path).resolve()
    toml_path = root / "task.toml"
    warnings: list[str] = []
    if not toml_path.is_file():
        raise ValueError(f"Harbor task.toml not found: {toml_path}")
    if tomllib is None:
        raise RuntimeError("Parsing TOML on Python < 3.11 requires tomli; please install tomli or run under Python 3.11+")
    raw = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    task_cfg = raw.get("task") or {}
    metadata = raw.get("metadata") or {}
    task_name = task_cfg.get("name")
    task_id = str(task_name or metadata.get("task_id") or root.name)
    schema_version = raw.get("schema_version")
    version = task_cfg.get("version") or raw.get("version")

    instruction = root / "instruction.md"
    verifier = root / "tests" / "test.sh"
    if not verifier.is_file() and (root / "tests" / "run_script.sh").is_file():
        verifier = root / "tests" / "run_script.sh"
    solution = root / "solution" / "solve.sh"
    dockerfile = root / "environment" / "Dockerfile"

    verifier_cfg = raw.get("verifier") or {}
    agent_cfg = raw.get("agent") or {}
    environment_cfg = raw.get("environment") or {}
    verifier_env = verifier_cfg.get("environment") or {}
    environment_network = environment_cfg.get("network_mode")
    verifier_network = verifier_env.get("network_mode") or verifier_cfg.get("network_mode")

    steps = raw.get("steps") or []
    step_count = len(steps) if isinstance(steps, list) else 0

    if not instruction.is_file():
        warnings.append("instruction.md not found")
    if not verifier.is_file():
        warnings.append("verifier script not found under tests/")
    if not solution.is_file():
        warnings.append("solution/solve.sh not found (optional in Harbor)")
    if not dockerfile.is_file() and not environment_cfg.get("docker_image"):
        warnings.append("no environment/Dockerfile or environment.docker_image found")
    if step_count:
        warnings.append(f"multi-step task detected: {step_count} step(s); execution bridge is not enabled in v0.6")

    return HarborTaskManifest(
        path=str(root),
        task_id=task_id,
        task_name=None if task_name is None else str(task_name),
        schema_version=None if schema_version is None else str(schema_version),
        version=None if version is None else str(version),
        verifier_path=verifier.relative_to(root).as_posix() if verifier.is_file() else None,
        solution_path=solution.relative_to(root).as_posix() if solution.is_file() else None,
        instruction_path=instruction.relative_to(root).as_posix() if instruction.is_file() else None,
        environment_dockerfile=dockerfile.relative_to(root).as_posix() if dockerfile.is_file() else None,
        verifier_timeout_sec=_float_or_none(verifier_cfg.get("timeout_sec") or verifier_cfg.get("execution_sec")),
        agent_timeout_sec=_float_or_none(agent_cfg.get("timeout_sec") or agent_cfg.get("execution_sec")),
        environment_network_mode=None if environment_network is None else str(environment_network),
        verifier_network_mode=None if verifier_network is None else str(verifier_network),
        has_task_toml=True,
        has_instruction=instruction.is_file(),
        has_verifier=verifier.is_file(),
        has_solution=solution.is_file(),
        has_environment=(dockerfile.is_file() or bool(environment_cfg.get("docker_image"))),
        step_count=step_count,
        warnings=tuple(warnings),
        suggested_verifier_command=("bash", verifier.relative_to(root).as_posix()) if verifier.is_file() else None,
        suggested_solution_command=("bash", solution.relative_to(root).as_posix()) if solution.is_file() else None,
    )


def write_manifest(path: str | Path, out: str | Path) -> Path:
    manifest = inspect_harbor_task(path)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest.to_dict(), indent=2) + "\n", encoding="utf-8")
    return out


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
