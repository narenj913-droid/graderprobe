"""Task runner: baseline, counterfactual probes, evidence, and profiles."""

from __future__ import annotations

import os
import platform
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from graderprobe import __version__
from graderprobe.baseline import BaselineReport, validate_baseline
from graderprobe.cache import ExecutionMemo, make_execution_key
from graderprobe.hashes import hash_tree, merkle_like
from graderprobe.evidence import PairEvidence, build_pair
from graderprobe.execution import run_evaluator, set_execution_slots, execution_slots
from graderprobe.isolation import IsolatedWorkspace
from graderprobe.probes.engine import ProbeEngine, apply_probe
from graderprobe.probes.minimize import minimize_by_diff_hunks
from graderprobe.profile import BoundaryIntegrityProfile, assemble_profile
from graderprobe.task import load_task
from graderprobe.providers.base import NullProvider, ModelProvider, proposals_to_specs
from graderprobe.types import EvidenceLevel, ExecutionResult, TaskSpec, Verdict

ProgressFn = Callable[[str], None]


@dataclass
class RunConfig:
    include_auto_probes: bool = False
    include_auto_sensitivity: bool = False
    validate_behavior: bool = True
    validate_behavior_all: bool = False
    minimize_counterfactuals: bool = False
    max_minimization_runs: int = 12
    seed: int = 0
    inherit_secrets: bool = False
    max_workers: int = 2
    task_workers: int = 1
    validate_invariance_behavior: bool = True
    memoize_minimization: bool = True
    baseline_repeats_override: int | None = None
    execution_slots: int | None = None
    include_model_probes: bool = False
    model_provider: ModelProvider | None = None
    max_model_proposals: int = 3
    replay_probes: list[dict[str, Any]] | None = None


def run_task(
    task: TaskSpec | str | Path,
    *,
    config: RunConfig | None = None,
    progress: ProgressFn | None = None,
) -> BoundaryIntegrityProfile:
    config = config or RunConfig()
    if not isinstance(task, TaskSpec):
        task = load_task(task)
    log = progress or (lambda _msg: None)

    # The CLI/audit layer configures the process-wide execution governor before
    # starting worker threads. Do not mutate the global semaphore from worker
    # threads; replacing it while other workers hold slots can deadlock them.
    log(f"execution_slots:{execution_slots()}")
    log(f"baseline:{task.id}")
    baseline = validate_baseline(
        task,
        inherit_secrets=config.inherit_secrets,
        repeats_override=config.baseline_repeats_override,
    )
    env = _environment(task, config)
    if not baseline.ok:
        log(f"baseline_invalid:{task.id}:{baseline.reason}")
        return assemble_profile(task, baseline, [], environment=env, notes=[baseline.reason])

    baseline_result = baseline.runs[0]
    source = Path(task.source_path)
    reference_path = source / task.oracle.reference
    original = (
        reference_path.read_text(encoding="utf-8")
        if reference_path.is_file()
        else (source / task.candidate_file).read_text(encoding="utf-8")
    )

    probes = list(task.all_probes())
    if config.include_auto_probes:
        engine = ProbeEngine(task)
        probes.extend(engine.auto_invariance(original))
        if config.include_auto_sensitivity and task.behavior_validator is not None:
            probes.extend(engine.auto_sensitivity(original))
    if config.replay_probes:
        for item in config.replay_probes:
            try:
                from graderprobe.types import ProbeClass, ProbeMethod, ExpectedRelation, ProbeSpec, TransformSpec
                probes.append(ProbeSpec(
                    id=str(item["id"]),
                    probe_class=ProbeClass(str(item["probe_class"])),
                    description=str(item.get("description", "replayed model probe")),
                    expected_relation=ExpectedRelation(str(item["expected_relation"])),
                    transform=TransformSpec(kind=str(item["transform"]["kind"]), params=dict(item["transform"].get("params") or {})),
                    method=ProbeMethod(str(item.get("method", "MODEL_GENERATED"))),
                    target=str(item.get("target", task.candidate_file)),
                    notes=str(item.get("notes", "")),
                ))
            except (KeyError, TypeError, ValueError) as exc:
                log(f"replay_probe_ignored:{exc}")
    elif config.include_model_probes:
        provider = config.model_provider or NullProvider()
        proposals = provider.propose_probes(task, original)[: max(0, int(config.max_model_proposals))]
        probes.extend(proposals_to_specs(proposals, prefix="MODEL"))
        log(f"model_probes:{provider.name}:{len(proposals)}")
    probes = _deduplicate_probes(probes)

    if not probes:
        return assemble_profile(
            task,
            baseline,
            [],
            environment=env,
            notes=["Passing boundary tests does not prove an evaluator is correct.", "n_probes=0"],
        )

    # Each probe gets its own isolated workspace, so probes can execute in
    # parallel without mutating one another. We restore deterministic result
    # order before profile assembly.
    workers = max(1, min(int(config.max_workers), len(probes)))
    results: dict[int, PairEvidence] = {}
    if workers == 1:
        for index, probe in enumerate(probes, start=1):
            log(f"probe:{probe.id}")
            results[index] = _run_probe(
                task, source, probe, index, baseline, baseline_result, original, config
            )
    else:
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="graderprobe") as pool:
            future_map = {
                pool.submit(
                    _run_probe, task, source, probe, index, baseline, baseline_result, original, config
                ): (index, probe)
                for index, probe in enumerate(probes, start=1)
            }
            for future in as_completed(future_map):
                index, probe = future_map[future]
                log(f"probe_done:{probe.id}")
                try:
                    results[index] = future.result()
                except Exception as exc:  # noqa: BLE001
                    results[index] = _error_pair(task, probe, index, baseline, baseline_result, str(exc))

    pairs = [results[index] for index in sorted(results)]
    notes = [
        "Passing boundary tests does not prove an evaluator is correct.",
        f"n_probes={len(pairs)} for task {task.id}.",
        f"probe_workers={workers}.",
        f"execution_slots={execution_slots()}.",
        "baseline_output_stable=" + str(baseline.output_stable),
        "model_provider=" + ((config.model_provider.name if config.model_provider is not None else "null") if config.include_model_probes else "disabled"),
    ]
    return assemble_profile(task, baseline, pairs, environment=env, notes=notes)


def _run_probe(
    task: TaskSpec,
    source: Path,
    probe,
    index: int,
    baseline: BaselineReport,
    baseline_result: ExecutionResult,
    source_reference: str,
    config: RunConfig,
) -> PairEvidence:
    with IsolatedWorkspace(source, prefix=f"gp-{task.id}-{probe.id}-") as workspace:
        try:
            applied = apply_probe(workspace, task, probe)
        except Exception as exc:  # noqa: BLE001
            return _error_pair(task, probe, index, baseline, baseline_result, str(exc))

        if not applied.validation_ok:
            fake = ExecutionResult(
                verdict=Verdict.ERROR,
                exit_code=None,
                stdout="",
                stderr=applied.validation_error,
                duration_ms=0.0,
                timed_out=False,
                workspace=str(workspace.path),
                command=[],
                environment={},
                error_message=applied.validation_error,
            )
            return build_pair(
                index=index,
                probe=probe,
                original=applied.original,
                transformed=applied.transformed,
                baseline_verdict=baseline_result.verdict,
                baseline_execution=baseline_result,
                probe_execution=fake,
                original_behavior=baseline.behavior_runs[0] if baseline.behavior_runs else None,
                transformed_behavior=None,
                evidence_level=EvidenceLevel.UNVALIDATED,
            )

        result = run_evaluator(workspace, task.evaluator, attempt=1, inherit_secrets=config.inherit_secrets)
        transformed_behavior = None
        evidence_level = EvidenceLevel.UNVALIDATED

        behavior_needed = _needs_behavior_validation(probe, result, baseline_result, config, task)
        if behavior_needed:
            transformed_behavior = (
                run_evaluator(workspace, task.behavior_validator, attempt=1, inherit_secrets=config.inherit_secrets)
                if task.behavior_validator is not None else None
            )
            evidence_level = _behavior_evidence_level(
                baseline=baseline,
                transformed_behavior=transformed_behavior,
                probe=probe,
            )

        pair = build_pair(
            index=index,
            probe=probe,
            original=applied.original,
            transformed=applied.transformed,
            baseline_verdict=baseline_result.verdict,
            baseline_execution=baseline_result,
            probe_execution=result,
            original_behavior=baseline.behavior_runs[0] if baseline.behavior_runs else None,
            transformed_behavior=transformed_behavior,
            evidence_level=evidence_level,
        )

        if _can_minimize(pair, config):
            pair.minimal_counterfactual = _minimize_counterfactual(
                task=task,
                source=source,
                original=applied.original,
                transformed=applied.transformed,
                config=config,
            )
        return pair


def _needs_behavior_validation(probe, result: ExecutionResult, baseline_result: ExecutionResult, config: RunConfig, task: TaskSpec) -> bool:
    if not config.validate_behavior or task.behavior_validator is None:
        return False
    if config.validate_behavior_all:
        return True
    if probe.probe_class.value == "invariance" and config.validate_invariance_behavior:
        return result.verdict is not baseline_result.verdict
    if probe.probe_class.value == "sensitivity":
        return result.verdict is Verdict.PASS and baseline_result.verdict is Verdict.PASS
    return False


def _behavior_evidence_level(*, baseline: BaselineReport, transformed_behavior: ExecutionResult | None, probe) -> EvidenceLevel:
    if transformed_behavior is None:
        return EvidenceLevel.UNVALIDATED
    if transformed_behavior.verdict not in {Verdict.PASS, Verdict.FAIL}:
        return EvidenceLevel.UNVALIDATED
    if baseline.behavior_runs and baseline.behavior_runs[0].verdict is Verdict.PASS:
        return EvidenceLevel.SMOKE_VALIDATED
    return EvidenceLevel.UNVALIDATED


def _can_minimize(pair: PairEvidence, config: RunConfig) -> bool:
    return bool(
        config.minimize_counterfactuals
        and pair.probe.probe_class.value == "sensitivity"
        and pair.actual_verdict is Verdict.PASS
        and pair.baseline_verdict is Verdict.PASS
        and pair.transformed_behavior is not None
        and pair.transformed_behavior.verdict is Verdict.FAIL
    )


def _minimize_counterfactual(*, task: TaskSpec, source: Path, original: str, transformed: str, config: RunConfig) -> dict[str, Any] | None:
    memo = ExecutionMemo(max_entries=max(32, config.max_minimization_runs * 2)) if config.memoize_minimization else None

    def predicate(candidate_text: str) -> bool:
        with IsolatedWorkspace(source, prefix=f"gp-min-{task.id}-") as mini:
            mini.write_text(task.candidate_file, candidate_text)
            ev = _run_with_optional_memo(mini, task.evaluator, config, memo, attempt=1)
            if ev.verdict is not Verdict.PASS:
                return False
            if task.behavior_validator is None:
                return False
            bv = _run_with_optional_memo(mini, task.behavior_validator, config, memo, attempt=1)
            return bv.verdict is Verdict.FAIL

    result = minimize_by_diff_hunks(
        original,
        transformed,
        predicate,
        budget=max(1, config.max_minimization_runs),
    )
    return None if result is None else result.to_dict()


def _run_with_optional_memo(
    workspace: IsolatedWorkspace,
    spec,
    config: RunConfig,
    memo: ExecutionMemo | None,
    *,
    attempt: int,
):
    if memo is None:
        return run_evaluator(workspace, spec, attempt=attempt, inherit_secrets=config.inherit_secrets)
    digest = merkle_like(hash_tree(workspace.path))
    key = make_execution_key(
        workspace_digest=digest, spec=spec, attempt=attempt, inherit_secrets=config.inherit_secrets
    )
    result, hit = memo.get_or_compute(
        key, lambda: run_evaluator(workspace, spec, attempt=attempt, inherit_secrets=config.inherit_secrets)
    )
    from dataclasses import replace
    if not hit:
        return replace(result, cache_key=key.value)
    return replace(result, workspace=str(workspace.path), cache_hit=True, cache_key=key.value, duration_ms=0.0)


def _error_pair(task: TaskSpec, probe, index: int, baseline: BaselineReport, baseline_result: ExecutionResult, message: str) -> PairEvidence:
    fake = ExecutionResult(
        verdict=Verdict.ERROR,
        exit_code=None,
        stdout="",
        stderr=message,
        duration_ms=0.0,
        timed_out=False,
        workspace="",
        command=[],
        environment={},
        error_message=message,
    )
    return build_pair(
        index=index,
        probe=probe,
        original="",
        transformed="",
        baseline_verdict=baseline_result.verdict,
        baseline_execution=baseline_result,
        probe_execution=fake,
        original_behavior=baseline.behavior_runs[0] if baseline.behavior_runs else None,
        transformed_behavior=None,
        evidence_level=EvidenceLevel.UNVALIDATED,
    )


def _deduplicate_probes(probes: list) -> list:
    seen: set[tuple[str, str, str]] = set()
    out = []
    for probe in probes:
        key = (
            probe.probe_class.value,
            probe.transform.kind,
            repr(sorted(probe.transform.params.items(), key=lambda item: item[0])),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(probe)
    return out


def _environment(task: TaskSpec, config: RunConfig) -> dict[str, Any]:
    return {
        "graderprobe_version": __version__,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "seed": config.seed,
        "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_id": task.id,
        "network_policy": task.evaluator.network,
        "inherit_secrets": config.inherit_secrets,
        "max_workers": max(1, int(config.max_workers)),
        "pid": os.getpid(),
    }
