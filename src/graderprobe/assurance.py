"""Benchmark/evaluator release assurance.

This module turns GraderProbe from a task-level auditor into a change-aware
release gate.  It compares the same counterfactual probe set across a Git base
and head revision, classifies artifact drift, and produces an evidence-first
release decision.  It never treats a score delta as proof of a model change.
"""
from __future__ import annotations

import json
import posixpath
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path, PurePosixPath
from typing import Any

from graderprobe.baseline import BaselineReport
from graderprobe.hashes import hash_tree, merkle_like, sha256_json
from graderprobe.profile import BoundaryIntegrityProfile
from graderprobe.runner import RunConfig, run_task
from graderprobe.task import TaskError, load_task
from graderprobe.types import FindingType, ProfileVerdict, ProbeClass, ProbeSpec


@dataclass(frozen=True)
class ChangedFile:
    status: str
    path: str
    old_path: str | None = None
    category: str = "other"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "path": self.path,
            "old_path": self.old_path,
            "category": self.category,
        }


@dataclass(frozen=True)
class TaskReleaseComparison:
    task_id: str
    task_path: str
    base_available: bool
    base_verdict: str
    head_verdict: str
    comparability: str
    decision: str
    changed_categories: tuple[str, ...]
    common_probe_count: int
    new_head_findings: int
    new_high_findings: int
    false_acceptance_delta: int
    false_rejection_delta: int
    baseline_head_ok: bool
    baseline_base_ok: bool
    required_checks: tuple[str, ...] = ()
    executed_checks: tuple[str, ...] = ()
    check_gaps: tuple[str, ...] = ()
    drift_severity: str = "low"
    base_task_digest: str | None = None
    head_task_digest: str | None = None
    base_cohort_id: str | None = None
    head_cohort_id: str | None = None
    probe_set_delta: int = 0
    head_findings: tuple[dict[str, Any], ...] = ()
    notes: tuple[str, ...] = ()
    coverage_scope: str = "task_local"

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_path": self.task_path,
            "base_available": self.base_available,
            "base_verdict": self.base_verdict,
            "head_verdict": self.head_verdict,
            "comparability": self.comparability,
            "decision": self.decision,
            "coverage_scope": self.coverage_scope,
            "changed_categories": list(self.changed_categories),
            "common_probe_count": self.common_probe_count,
            "new_head_findings": self.new_head_findings,
            "new_high_findings": self.new_high_findings,
            "false_acceptance_delta": self.false_acceptance_delta,
            "false_rejection_delta": self.false_rejection_delta,
            "baseline_head_ok": self.baseline_head_ok,
            "baseline_base_ok": self.baseline_base_ok,
            "required_checks": list(self.required_checks),
            "executed_checks": list(self.executed_checks),
            "check_gaps": list(self.check_gaps),
            "drift_severity": self.drift_severity,
            "base_task_digest": self.base_task_digest,
            "head_task_digest": self.head_task_digest,
            "base_cohort_id": self.base_cohort_id,
            "head_cohort_id": self.head_cohort_id,
            "probe_set_delta": self.probe_set_delta,
            "head_findings": list(self.head_findings),
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ReleaseAssuranceReport:
    schema: str
    graderprobe_version: str
    repository: str
    base_ref: str
    head_ref: str
    base_commit: str | None
    head_commit: str | None
    changed_files: tuple[ChangedFile, ...]
    comparisons: tuple[TaskReleaseComparison, ...]
    decision: str
    release_fingerprint: str
    semantic_reviews: tuple[dict[str, Any], ...] = ()
    api_usage: dict[str, int] = field(default_factory=dict)
    deleted_task_paths: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "graderprobe_version": self.graderprobe_version,
            "repository": self.repository,
            "base_ref": self.base_ref,
            "head_ref": self.head_ref,
            "base_commit": self.base_commit,
            "head_commit": self.head_commit,
            "changed_files": [item.to_dict() for item in self.changed_files],
            "comparisons": [item.to_dict() for item in self.comparisons],
            "decision": self.decision,
            "release_fingerprint": self.release_fingerprint,
            "semantic_reviews": list(self.semantic_reviews),
            "api_usage": dict(self.api_usage or {}),
            "deleted_task_paths": list(self.deleted_task_paths),
            "notes": list(self.notes),
        }


def changed_file_manifest(repo: str | Path, *, base_ref: str = "HEAD~1", head_ref: str = "HEAD") -> list[ChangedFile]:
    root = Path(repo).resolve()
    proc = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-status", "--find-renames", f"{base_ref}...{head_ref}"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git diff failed")
    files: list[ChangedFile] = []
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        path = parts[-1]
        old_path = parts[1] if status.startswith("R") and len(parts) >= 3 else None
        files.append(ChangedFile(status=status, path=path, old_path=old_path, category=classify_change(path)))
    return files


def classify_change(path: str) -> str:
    p = PurePosixPath(path)
    name = p.name.lower()
    parts = {item.lower() for item in p.parts}
    if parts & {"docs", "evidence", "artifacts"}:
        return "other"
    if parts & {"tools", "scripts", ".github", "workflow"}:
        return "maintainer_workflow"
    if name in {"graderprobe.lock.json"} or name.endswith(".lock.json") or name.endswith(".lock"):
        return "maintainer_workflow"
    if name in {"task.yaml", "task.yml", "instruction.md"}:
        return "task_contract"
    if "solution" in parts or "reference" in parts or "gold" in parts:
        return "reference_solution"
    if "environment" in parts or "environments" in parts or name in {"dockerfile", "compose.yaml", "docker-compose.yaml"}:
        return "environment"
    if (
        "tests" in parts
        or "graders" in parts
        or "evaluators" in parts
        or "verifiers" in parts
        or "grader" in name
        or "verifier" in name
        or "evaluator" in name
    ):
        return "evaluator"
    if "probe" in name or "probes" in parts:
        return "probe_definition"
    return "other"


def _resolve_ref(repo: Path, ref: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", ref],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    return proc.stdout.strip() if proc.returncode == 0 else None


def release_assurance(
    repo: str | Path,
    *,
    task_root: str | Path,
    base_ref: str = "HEAD~1",
    head_ref: str = "HEAD",
    config: RunConfig | None = None,
    max_tasks: int | None = None,
) -> ReleaseAssuranceReport:
    root = Path(repo).resolve()
    task_root = Path(task_root).resolve()
    if not task_root.is_dir():
        raise ValueError(f"task root does not exist: {task_root}")
    config = config or RunConfig()
    manifest = changed_file_manifest(root, base_ref=base_ref, head_ref=head_ref)
    head_tasks = [t for t in _changed_task_files(root, manifest) if _path_is_within(t, task_root)]
    global_categories = sorted({
        item.category
        for item in manifest
        if item.category in {"evaluator", "environment", "task_contract", "reference_solution", "probe_definition"}
        and not _path_is_within(root / item.path, task_root)
        and not _path_is_within(root / item.path, root / "corpus")
    })
    global_fanout = bool(global_categories)
    all_head_tasks = sorted(task_root.rglob("task.yaml")) if global_fanout else head_tasks
    if global_fanout:
        # A shared evaluator/environment/probe change can affect every task even
        # when no task-local file changed. Silently returning NO_CHANGES would
        # be an unsafe false negative. Conservatively fan out to the current
        # task population; max_tasks may cap it and the report records the gap.
        head_tasks = all_head_tasks
    total_head_tasks = len(head_tasks)
    if max_tasks is not None:
        head_tasks = head_tasks[: max(0, int(max_tasks))]
    capped_global_fanout = global_fanout and len(head_tasks) < total_head_tasks
    deleted_task_paths = _deleted_task_paths(root, task_root, manifest)

    comparisons: list[TaskReleaseComparison] = []
    for head_task_path in head_tasks:
        try:
            head_task = load_task(head_task_path)
        except (TaskError, OSError) as exc:
            comparisons.append(
                TaskReleaseComparison(
                    task_id=str(head_task_path),
                    task_path=str(head_task_path),
                    base_available=False,
                    base_verdict="ERROR",
                    head_verdict="ERROR",
                    comparability="NON_COMPARABLE",
                    decision="BLOCK",
                    coverage_scope="global_fanout" if global_fanout else "task_local",
                    changed_categories=_categories_for_task(head_task_path, manifest, root),
                    common_probe_count=0,
                    new_head_findings=0,
                    new_high_findings=0,
                    false_acceptance_delta=0,
                    false_rejection_delta=0,
                    baseline_head_ok=False,
                    baseline_base_ok=False,
                    notes=(f"head task load failed: {exc}",),
                )
            )
            continue

        # New/changed head tasks must still be validated even when the base
        # revision has no corresponding task.  This prevents newly introduced
        # benchmark tasks from bypassing baseline/probe checks. Evaluator and
        # environment changes force at least two baseline repeats so the release
        # report can make a meaningful determinism statement.
        head_categories = _categories_for_task(head_task_path, manifest, root)
        if global_fanout:
            head_categories = sorted(set(head_categories) | set(global_categories))
        head_repeats = config.baseline_repeats_override
        if ("evaluator" in head_categories or "environment" in head_categories) and (head_repeats is None or int(head_repeats) < 2):
            head_repeats = 2
        head_config = replace(config, baseline_repeats_override=head_repeats)
        task_rel = head_task_path.parent.relative_to(root).as_posix()
        head_exec_task = _rebase_task_to_repo_snapshot(head_task, task_rel, root) if global_fanout else head_task
        head_profile = run_task(head_exec_task, config=head_config)
        base_root_ctx = _materialize_task_dir(root, base_ref, head_task_path.parent, full_repo=global_fanout)
        try:
            if base_root_ctx is None:
                comparisons.append(_head_only_comparison(head_task, head_task_path, head_profile, manifest, root, coverage_scope="global_fanout" if global_fanout else "task_local", additional_categories=global_categories if global_fanout else ()))
                continue
            base_dir = base_root_ctx / head_task_path.parent.relative_to(root)
            base_task_path = base_dir / "task.yaml"
            if not base_task_path.is_file():
                comparisons.append(_head_only_comparison(head_task, head_task_path, head_profile, manifest, root, coverage_scope="global_fanout" if global_fanout else "task_local", additional_categories=global_categories if global_fanout else ()))
                continue

            base_task = load_task(base_task_path)

            # Re-run the exact probe set emitted on head against the base task.
            # The base task's own declared probes are removed so the comparison is
            # about the same experiment rather than two unrelated probe selections.
            replay_specs = [_probe_to_dict(pair.probe) for pair in head_profile.pairs]
            if global_fanout:
                replay_task = _rebase_task_to_repo_snapshot(base_task, task_rel, base_root_ctx)
            else:
                replay_task = replace(base_task, invariance_probes=[], sensitivity_probes=[])
            base_cfg = replace(
                head_config,
                include_auto_probes=False,
                include_auto_sensitivity=False,
                include_model_probes=False,
                model_provider=None,
                replay_probes=replay_specs,
            )
            base_profile = run_task(replay_task, config=base_cfg)
            comparisons.append(
                _compare_profiles(
                    head_task=head_task,
                    head_task_path=head_task_path,
                    base_task=base_task,
                    base_task_path=base_task_path,
                    base_profile=base_profile,
                    head_profile=head_profile,
                    manifest=manifest,
                    root=root,
                    coverage_scope="global_fanout" if global_fanout else "task_local",
                    additional_categories=global_categories if global_fanout else (),
                )
            )
        finally:
            if base_root_ctx is not None:
                _cleanup_materialized(base_root_ctx)

    semantic_reviews: list[dict[str, Any]] = []
    provider = config.model_provider if config.include_model_probes else None
    if provider is not None and hasattr(provider, "review_release_change"):
        diff_text = _compact_diff(root, base_ref, head_ref, manifest)
        for comparison in comparisons:
            try:
                review = provider.review_release_change(
                    task_id=comparison.task_id,
                    diff_summary=diff_text,
                    head_report={
                        "verdict": comparison.head_verdict,
                        "metrics": {
                            "false_acceptance_delta": comparison.false_acceptance_delta,
                            "false_rejection_delta": comparison.false_rejection_delta,
                            "new_head_findings": comparison.new_head_findings,
                        },
                        "findings": list(comparison.head_findings),
                    },
                )
                semantic_reviews.append({"task_id": comparison.task_id, "review": review, "usage": getattr(provider, "last_usage", {})})
            except Exception as exc:  # noqa: BLE001
                semantic_reviews.append({"task_id": comparison.task_id, "review_error": str(exc)})

    decision = _overall_decision(comparisons)
    semantic_errors = [item for item in semantic_reviews if "review_error" in item]
    if semantic_errors and decision == "ALLOW":
        decision = "WARN"
    if deleted_task_paths:
        if decision in {"ALLOW", "NO_CHANGES"}:
            decision = "WARN"
    if capped_global_fanout:
        decision = "WARN" if decision == "ALLOW" else decision
    base_commit = _resolve_ref(root, base_ref)
    head_commit = _resolve_ref(root, head_ref)
    api_usage = getattr(config.model_provider, "usage_summary", {}) if config.include_model_probes else {}
    fingerprint = "sha256:" + sha256_json(
        {
            "base_ref": base_ref,
            "head_ref": head_ref,
            "base_commit": base_commit,
            "head_commit": head_commit,
            "decision": decision,
            "deleted_task_paths": deleted_task_paths,
            "comparisons": [item.to_dict() for item in comparisons],
        }
    )
    report_notes = [
        "Release assurance compares the same counterfactual probe set across revisions where possible.",
        "A release decision is evidence-based and does not prove benchmark correctness.",
        "Deleted benchmark tasks are reported because removal changes release comparability.",
    ]
    if global_fanout:
        report_notes.append("A shared high-risk artifact changed outside task directories; tasks were conservatively fan-out audited.")
    if semantic_errors:
        report_notes.append(f"{len(semantic_errors)} requested semantic review(s) failed; decision was not allowed to remain ALLOW.")
    return ReleaseAssuranceReport(
        schema="graderprobe.release_assurance.v1",
        graderprobe_version=_version(),
        repository=str(root),
        base_ref=base_ref,
        head_ref=head_ref,
        base_commit=base_commit,
        head_commit=head_commit,
        changed_files=tuple(manifest),
        comparisons=tuple(comparisons),
        decision=decision,
        release_fingerprint=fingerprint,
        semantic_reviews=tuple(semantic_reviews),
        api_usage=dict(api_usage),
        deleted_task_paths=tuple(deleted_task_paths),
        notes=tuple(report_notes),
    )


def _required_checks(categories: list[str]) -> tuple[str, ...]:
    required: set[str] = set()
    cats = set(categories)
    if "evaluator" in cats:
        required.update({"baseline", "invariance", "sensitivity", "determinism"})
    if "task_contract" in cats:
        required.update({"baseline", "invariance", "sensitivity"})
    if "reference_solution" in cats:
        required.update({"baseline", "sensitivity"})
    if "environment" in cats:
        required.update({"baseline", "determinism"})
    if "probe_definition" in cats:
        required.add("invariance")
        required.add("sensitivity")
    if not required:
        required.add("baseline")
    return tuple(sorted(required))


def _drift_severity(categories: list[str]) -> str:
    cats = set(categories)
    if "evaluator" in cats or "environment" in cats:
        return "high"
    if cats & {"task_contract", "reference_solution", "probe_definition"}:
        return "medium"
    return "low"


def _task_digest(task_path: Path) -> str | None:
    try:
        return merkle_like(hash_tree(task_path))
    except OSError:
        return None


def _cohort_id(task_digest: str | None, task) -> str | None:
    if not task_digest:
        return None
    evaluator = {
        "command": list(task.evaluator.command),
        "working_dir": task.evaluator.working_dir,
        "timeout_seconds": task.evaluator.timeout_seconds,
        "pass_exit_codes": list(task.evaluator.pass_exit_codes),
        "fail_exit_codes": list(task.evaluator.fail_exit_codes),
        "inconclusive_exit_codes": list(task.evaluator.inconclusive_exit_codes),
        "verdict_protocol": task.evaluator.verdict_protocol,
        "environment": dict(sorted(task.evaluator.environment.items())),
        "network": task.evaluator.network,
        "backend": task.evaluator.backend,
        "container_image": task.evaluator.container_image,
        "container_network": task.evaluator.container_network,
        "container_memory": task.evaluator.container_memory,
        "container_cpus": task.evaluator.container_cpus,
    }
    environment = {
        "behavior_validator": None if task.behavior_validator is None else list(task.behavior_validator.command),
        "provenance": task.provenance,
    }
    return "sha256:" + sha256_json({"task_tree_digest": task_digest, "evaluator": evaluator, "environment": environment})


def _compare_profiles(*, head_task, head_task_path, base_task, base_task_path, base_profile, head_profile, manifest, root, coverage_scope="task_local", additional_categories=()) -> TaskReleaseComparison:
    base_map = {pair.probe.id: pair for pair in base_profile.pairs}
    head_map = {pair.probe.id: pair for pair in head_profile.pairs}
    common = sorted(set(base_map) & set(head_map))

    def notable(profile: BoundaryIntegrityProfile) -> set[tuple[str, str]]:
        return {
            (f.probe_id, f.type.value)
            for f in profile.findings
            if f.type in {FindingType.FALSE_ACCEPTANCE, FindingType.FALSE_REJECTION}
        }

    base_notable = notable(base_profile)
    head_notable = notable(head_profile)
    new_notable = head_notable - base_notable
    new_high = {
        (f.probe_id, f.type.value)
        for f in head_profile.findings
        if f.type in {FindingType.FALSE_ACCEPTANCE, FindingType.FALSE_REJECTION}
        and f.severity.value == "high"
        and (f.probe_id, f.type.value) not in base_notable
    }
    fa_delta = head_profile.metrics.false_acceptance_count - base_profile.metrics.false_acceptance_count
    fr_delta = head_profile.metrics.false_rejection_count - base_profile.metrics.false_rejection_count

    categories_list = sorted(set(_categories_for_task(head_task_path, manifest, root)) | set(additional_categories))
    categories = tuple(categories_list)
    materially_changed = set(categories) & {"task_contract", "reference_solution", "environment", "evaluator", "probe_definition"}
    executed: set[str] = {"baseline"}
    if len(base_profile.baseline.runs) >= 2 and len(head_profile.baseline.runs) >= 2:
        executed.add("determinism")
    if any(pair.probe.probe_class is ProbeClass.INVARIANCE for pair in head_profile.pairs) and any(pair.probe.probe_class is ProbeClass.INVARIANCE for pair in base_profile.pairs):
        executed.add("invariance")
    if any(pair.probe.probe_class is ProbeClass.SENSITIVITY for pair in head_profile.pairs) and any(pair.probe.probe_class is ProbeClass.SENSITIVITY for pair in base_profile.pairs):
        executed.add("sensitivity")
    required = set(_required_checks(categories_list))
    check_gaps = tuple(sorted(required - executed))
    base_digest = _task_digest(base_task_path.parent)
    head_digest = _task_digest(head_task_path.parent)
    base_cohort = _cohort_id(base_digest, base_task)
    head_cohort = _cohort_id(head_digest, head_task)
    if not base_profile.baseline.ok or not head_profile.baseline.ok:
        comparability = "NON_COMPARABLE"
    elif not materially_changed:
        comparability = "DIRECT"
    else:
        comparability = "DIFFERENTIAL"

    notes: list[str] = []
    probe_set_delta = len(set(head_map) ^ set(base_map))
    if len(common) < len(head_map):
        notes.append(f"{len(head_map) - len(common)} head probes were not present in the base result set")
    if len(common) < len(base_map):
        notes.append(f"{len(base_map) - len(common)} base probes were not present in the head result set")
    if base_map and head_map and not common:
        notes.append("base and head share no probe IDs; differential evidence is unavailable")
    if not head_profile.baseline.output_stable:
        notes.append("head baseline output or exit code was not stable across repeats")
    if not base_profile.baseline.output_stable:
        notes.append("base baseline output or exit code was not stable across repeats")
    if head_profile.verdict is ProfileVerdict.BASELINE_INVALID:
        notes.append("head baseline invalid")
    if base_profile.verdict is ProfileVerdict.BASELINE_INVALID:
        notes.append("base baseline invalid")

    decision = "ALLOW"
    if head_profile.verdict is ProfileVerdict.BASELINE_INVALID:
        decision = "BLOCK"
    elif new_high:
        decision = "BLOCK"
    elif base_profile.verdict is ProfileVerdict.BOUNDARY_OK and head_profile.verdict is ProfileVerdict.BOUNDARY_FAIL:
        decision = "BLOCK"
    elif head_profile.verdict in {ProfileVerdict.BOUNDARY_WARNING, ProfileVerdict.INCONCLUSIVE}:
        decision = "WARN"
    elif fa_delta > 0 or fr_delta > 0:
        decision = "WARN"
    elif probe_set_delta > 0 and "probe_definition" in categories:
        decision = "WARN"
    elif base_map and head_map and not common:
        decision = "WARN"
    elif check_gaps:
        decision = "WARN"
    elif (not base_profile.baseline.output_stable or not head_profile.baseline.output_stable) and ("evaluator" in categories or "environment" in categories):
        decision = "WARN"

    head_findings = tuple(
        {
            "type": f.type.value,
            "severity": f.severity.value,
            "probe_id": f.probe_id,
            "summary": f.summary,
        }
        for f in head_profile.findings
        if f.type in {FindingType.FALSE_ACCEPTANCE, FindingType.FALSE_REJECTION, FindingType.INCONCLUSIVE, FindingType.EXECUTION_ERROR}
    )

    return TaskReleaseComparison(
        task_id=head_task.id,
        task_path=str(head_task_path),
        base_available=True,
        base_verdict=base_profile.verdict.value,
        head_verdict=head_profile.verdict.value,
        comparability=comparability,
        decision=decision,
        coverage_scope=coverage_scope,
        changed_categories=categories,
        common_probe_count=len(common),
        new_head_findings=len(new_notable),
        new_high_findings=len(new_high),
        false_acceptance_delta=fa_delta,
        false_rejection_delta=fr_delta,
        baseline_head_ok=head_profile.baseline.ok,
        baseline_base_ok=base_profile.baseline.ok,
        required_checks=tuple(sorted(required)),
        executed_checks=tuple(sorted(executed)),
        check_gaps=check_gaps,
        drift_severity=_drift_severity(categories_list),
        base_task_digest=base_digest,
        head_task_digest=head_digest,
        base_cohort_id=base_cohort,
        head_cohort_id=head_cohort,
        probe_set_delta=probe_set_delta,
        head_findings=head_findings,
        notes=tuple(notes),
    )


def _head_only_comparison(task, task_path: Path, head_profile: BoundaryIntegrityProfile, manifest: list[ChangedFile], root: Path, *, coverage_scope="task_local", additional_categories=()) -> TaskReleaseComparison:
    categories = tuple(sorted(set(_categories_for_task(task_path, manifest, root)) | set(additional_categories)))
    high = sum(1 for f in head_profile.findings if f.type in {FindingType.FALSE_ACCEPTANCE, FindingType.FALSE_REJECTION} and f.severity.value == "high")
    notables = tuple(
        {"type": f.type.value, "severity": f.severity.value, "probe_id": f.probe_id, "summary": f.summary}
        for f in head_profile.findings
        if f.type in {FindingType.FALSE_ACCEPTANCE, FindingType.FALSE_REJECTION, FindingType.INCONCLUSIVE, FindingType.EXECUTION_ERROR}
    )
    executed: set[str] = {"baseline"}
    if len(head_profile.baseline.runs) >= 2:
        executed.add("determinism")
    if any(pair.probe.probe_class is ProbeClass.INVARIANCE for pair in head_profile.pairs):
        executed.add("invariance")
    if any(pair.probe.probe_class is ProbeClass.SENSITIVITY for pair in head_profile.pairs):
        executed.add("sensitivity")
    required = set(_required_checks(list(categories)))
    check_gaps = tuple(sorted(required - executed))
    decision = "WARN"
    if head_profile.verdict is ProfileVerdict.BASELINE_INVALID or high:
        decision = "BLOCK"
    elif head_profile.verdict is ProfileVerdict.BOUNDARY_FAIL:
        decision = "BLOCK"
    digest = _task_digest(task_path.parent)
    return TaskReleaseComparison(
        task_id=task.id,
        task_path=str(task_path),
        base_available=False,
        base_verdict="NOT_AVAILABLE",
        head_verdict=head_profile.verdict.value,
        comparability="NON_COMPARABLE",
        decision=decision,
        coverage_scope=coverage_scope,
        changed_categories=categories,
        common_probe_count=0,
        new_head_findings=len(notables),
        new_high_findings=high,
        false_acceptance_delta=head_profile.metrics.false_acceptance_count,
        false_rejection_delta=head_profile.metrics.false_rejection_count,
        baseline_head_ok=head_profile.baseline.ok,
        baseline_base_ok=False,
        required_checks=tuple(sorted(required)),
        executed_checks=tuple(sorted(executed)),
        check_gaps=check_gaps,
        drift_severity=_drift_severity(list(categories)),
        head_task_digest=digest,
        head_cohort_id=_cohort_id(digest, task),
        probe_set_delta=len(head_profile.pairs),
        head_findings=notables,
        notes=("No base task was available; head task was audited but cross-revision comparability could not be established.",),
    )


def _no_base_comparison(task, task_path: Path, manifest: list[ChangedFile], root: Path) -> TaskReleaseComparison:
    return TaskReleaseComparison(
        task_id=task.id,
        task_path=str(task_path),
        base_available=False,
        base_verdict="NOT_AVAILABLE",
        head_verdict="NOT_RUN",
        comparability="NON_COMPARABLE",
        decision="WARN",
        changed_categories=tuple(sorted(set(_categories_for_task(task_path, manifest, root)))),
        common_probe_count=0,
        new_head_findings=0,
        new_high_findings=0,
        false_acceptance_delta=0,
        false_rejection_delta=0,
        baseline_head_ok=False,
        baseline_base_ok=False,
        required_checks=_required_checks(list(categories)),
        drift_severity=_drift_severity(list(categories)),
        head_task_digest=_task_digest(task_path.parent),
        head_cohort_id=_cohort_id(_task_digest(task_path.parent), task),
        notes=("base revision does not contain a readable task directory",),
    )



def _deleted_task_paths(root: Path, task_root: Path, manifest: list[ChangedFile]) -> list[str]:
    out: set[str] = set()
    task_root = task_root.resolve()
    root = root.resolve()
    for item in manifest:
        if not item.status.startswith("D"):
            continue
        p = (root / item.path).resolve()
        try:
            rel = p.relative_to(task_root)
        except ValueError:
            continue
        # A deleted task is represented by its directory. Any deleted file under
        # a task directory counts, but the report should not emit duplicate
        # entries for task.yaml plus the task's other files.
        if p.name in {"task.yaml", "task.yml"}:
            out.add(str(p.parent.relative_to(root)))
            continue
        parts = rel.parts
        if len(parts) >= 2:
            out.add(str((task_root / parts[0]).relative_to(root)))
    return sorted(out)


def _path_is_within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def _changed_task_files(root: Path, manifest: list[ChangedFile]) -> list[Path]:
    out: set[Path] = set()
    for item in manifest:
        p = (root / item.path).resolve()
        candidates = [p] if p.name in {"task.yaml", "task.yml"} else []
        current = p.parent if p.suffix else p
        for parent in (current, *current.parents):
            candidate = parent / "task.yaml"
            if candidate.is_file() and root in candidate.parents:
                candidates.append(candidate)
                break
            if parent == root:
                break
        out.update(candidates)
    return sorted(path for path in out if path.is_file())


def _categories_for_task(task_path: Path, manifest: list[ChangedFile], root: Path) -> list[str]:
    rel = task_path.parent.relative_to(root)
    out: list[str] = []
    for item in manifest:
        try:
            item_path = (root / item.path).resolve()
            if rel in item_path.parents or item_path.parent == task_path.parent:
                out.append(item.category)
        except OSError:
            continue
    return sorted(set(out or ["other"]))


def _materialize_task_dir(repo: Path, ref: str, task_dir: Path, *, full_repo: bool = False) -> Path | None:
    rel = "." if full_repo else task_dir.resolve().relative_to(repo.resolve()).as_posix()
    temp = Path(tempfile.mkdtemp(prefix="graderprobe-base-"))
    archive = temp / "tree.tar"
    with archive.open("wb") as archive_file:
        proc = subprocess.run(
            ["git", "-C", str(repo), "archive", "--format=tar", ref, "--", rel],
            stdout=archive_file,
            stderr=subprocess.PIPE,
            check=False,
            timeout=60,
        )
    if proc.returncode != 0:
        _cleanup_materialized(temp)
        return None
    try:
        with tarfile.open(archive, "r") as tf:
            root = temp / "tree"
            root.mkdir()
            base_resolved = root.resolve()
            for member in tf.getmembers():
                member_path = (root / member.name).resolve()
                if base_resolved != member_path and base_resolved not in member_path.parents:
                    raise ValueError("unsafe git archive member")
                if member.isdir():
                    member_path.mkdir(parents=True, exist_ok=True)
                    continue
                if not member.isreg():
                    raise ValueError(f"unsupported git archive member type: {member.name}")
                member_path.parent.mkdir(parents=True, exist_ok=True)
                source = tf.extractfile(member)
                if source is None:
                    raise ValueError(f"unable to read git archive member: {member.name}")
                with source, member_path.open("wb") as target:
                    import shutil
                    shutil.copyfileobj(source, target)
        return root
    except Exception:
        _cleanup_materialized(temp)
        raise


def _cleanup_materialized(path: Path) -> None:
    import shutil
    top = path if path.name.startswith("graderprobe-base-") else path.parent
    shutil.rmtree(top, ignore_errors=True)


def _prefix_rel(root_rel: str, value: str) -> str:
    if not value or value == ".":
        return root_rel
    return posixpath.normpath(posixpath.join(root_rel, value))


def _rebase_task_to_repo_snapshot(task, task_rel: str, snapshot_root: Path):
    """Rebase a task onto a repository snapshot so external task dependencies remain executable."""
    def prefix(value: str) -> str:
        return _prefix_rel(task_rel, value)

    def rebase_exec(spec):
        if spec is None:
            return None
        return replace(spec, working_dir=prefix(spec.working_dir))

    invariance = [
        replace(probe, target=prefix(probe.target or task.candidate_file))
        for probe in task.invariance_probes
    ]
    sensitivity = [
        replace(probe, target=prefix(probe.target or task.candidate_file))
        for probe in task.sensitivity_probes
    ]
    oracle = replace(
        task.oracle,
        reference=prefix(task.oracle.reference),
        known_invalid=None if task.oracle.known_invalid is None else prefix(task.oracle.known_invalid),
    )
    return replace(
        task,
        source_path=snapshot_root,
        candidate_file=prefix(task.candidate_file),
        oracle=oracle,
        evaluator=rebase_exec(task.evaluator),
        behavior_validator=rebase_exec(task.behavior_validator),
        invariance_probes=invariance,
        sensitivity_probes=sensitivity,
    )


def _probe_to_dict(probe: ProbeSpec) -> dict[str, Any]:
    return {
        "id": probe.id,
        "probe_class": probe.probe_class.value,
        "description": probe.description,
        "expected_relation": probe.expected_relation.value,
        "transform": {"kind": probe.transform.kind, "params": probe.transform.params},
        "method": probe.method.value,
        "target": probe.target,
        "notes": probe.notes,
    }


def _overall_decision(comparisons: list[TaskReleaseComparison]) -> str:
    if any(item.decision == "BLOCK" for item in comparisons):
        return "BLOCK"
    if any(item.decision == "WARN" for item in comparisons):
        return "WARN"
    if not comparisons:
        return "NO_CHANGES"
    return "ALLOW"


def _compact_diff(root: Path, base_ref: str, head_ref: str, manifest: list[ChangedFile]) -> str:
    paths = [item.path for item in manifest[:80]]
    if not paths:
        return "no changed files"
    proc = subprocess.run(
        ["git", "-C", str(root), "diff", "--unified=2", f"{base_ref}...{head_ref}", "--", *paths[:40]],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    text = proc.stdout if proc.returncode == 0 else "\n".join(paths)
    return text[:16000]


def render_release_markdown(report: ReleaseAssuranceReport) -> str:
    lines = [
        "# GraderProbe Release Assurance",
        "",
        f"**Decision:** `{report.decision}`",
        f"**Base:** `{report.base_ref}`",
        f"**Head:** `{report.head_ref}`",
        f"**Fingerprint:** `{report.release_fingerprint}`",
        "",
        "## Changed files",
        "",
        "| Status | File | Category |",
        "|---|---|---|",
    ]
    for item in report.changed_files:
        lines.append(f"| {item.status} | `{item.path}` | `{item.category}` |")
    lines += ["", "## Task comparisons", "", "| Task | Base | Head | Decision | Scope | Comparability | Drift | Common probes |", "|---|---|---|---|---|---|---|---:|"]
    for item in report.comparisons:
        lines.append(
            f"| `{item.task_id}` | `{item.base_verdict}` | `{item.head_verdict}` | `{item.decision}` | `{item.coverage_scope}` | `{item.comparability}` | `{item.drift_severity}` | {item.common_probe_count} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "BLOCK means the release-assurance evidence found a material regression or an invalid head baseline.",
        "WARN means additional maintainer review is warranted.",
        "ALLOW means no release-blocking regression was detected by this run; it is not a proof of benchmark correctness.",
        f"Deleted task paths: {len(report.deleted_task_paths)}.",
        f"Semantic API usage: {report.api_usage.get('calls', 0)} call(s), {report.api_usage.get('total_tokens', 0)} token(s).",
        "",
    ]
    return "\n".join(lines)


def write_release_report(report: ReleaseAssuranceReport, out_dir: str | Path) -> tuple[Path, Path]:
    payload = report.to_dict()
    try:
        import jsonschema
        schema_candidates = [
            Path(__file__).resolve().parent / "schemas" / "release_assurance.schema.json",
            Path(__file__).resolve().parents[2] / "schemas" / "release_assurance.schema.json",
        ]
        schema_path = next((candidate for candidate in schema_candidates if candidate.is_file()), None)
        if schema_path is not None:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.validate(payload, schema)
    except ImportError:
        pass
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "release-assurance.json"
    md_path = out / "release-assurance.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_release_markdown(report), encoding="utf-8")
    return json_path, md_path


def _version() -> str:
    from graderprobe import __version__
    return __version__
