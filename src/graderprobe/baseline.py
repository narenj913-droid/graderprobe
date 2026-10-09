"""Baseline safety checks. Invalid baselines never produce a boundary score."""

from __future__ import annotations

from dataclasses import dataclass, field

from graderprobe.execution import run_evaluator
from graderprobe.isolation import IsolatedWorkspace
from graderprobe.types import ExecutionResult, TaskSpec, Verdict, is_evaluative


@dataclass
class BaselineReport:
    ok: bool
    verdict: Verdict
    reason: str
    runs: list[ExecutionResult] = field(default_factory=list)
    known_invalid: ExecutionResult | None = None
    behavior_runs: list[ExecutionResult] = field(default_factory=list)
    behavior_ok: bool | None = None
    behavior_reason: str = ""
    harness_ok: bool = True
    output_stable: bool | None = None
    output_stability_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "verdict": self.verdict.value,
            "reason": self.reason,
            "runs": [run.to_dict() for run in self.runs],
            "known_invalid": None if self.known_invalid is None else self.known_invalid.to_dict(),
            "behavior_runs": [run.to_dict() for run in self.behavior_runs],
            "behavior_ok": self.behavior_ok,
            "behavior_reason": self.behavior_reason,
            "harness_ok": self.harness_ok,
            "output_stable": self.output_stable,
            "output_stability_reason": self.output_stability_reason,
        }


def validate_baseline(task: TaskSpec, *, inherit_secrets: bool = False, repeats_override: int | None = None) -> BaselineReport:
    source = _source(task)
    repeats = max(1, int(repeats_override if repeats_override is not None else task.baseline_repeats))
    runs: list[ExecutionResult] = []
    for attempt in range(1, repeats + 1):
        with IsolatedWorkspace(source, prefix=f"gp-base-{task.id}-") as workspace:
            _install_reference(workspace, task)
            result = run_evaluator(
                workspace, task.evaluator, attempt=attempt, inherit_secrets=inherit_secrets
            )
            runs.append(result)

    if not runs:
        return BaselineReport(
            ok=False,
            verdict=Verdict.BASELINE_INVALID,
            reason="no baseline runs executed",
            harness_ok=False,
        )

    verdicts = {run.verdict for run in runs}
    if len(verdicts) > 1:
        return BaselineReport(
            ok=False,
            verdict=Verdict.BASELINE_INVALID,
            reason=(
                "non-deterministic evaluator: baseline verdicts disagreed "
                f"({sorted(v.value for v in verdicts)})"
            ),
            runs=runs,
            output_stable=False,
            output_stability_reason="verdicts disagreed across baseline repeats",
        )

    primary = runs[0]
    output_stable = len({(run.exit_code, run.stdout_sha256, run.stderr_sha256) for run in runs}) <= 1
    output_reason = (
        "stdout/stderr digests and exit code stable across repeats"
        if output_stable else
        "verdict stable but execution output or exit code varied across repeats"
    )
    if primary.verdict in {Verdict.ERROR, Verdict.TIMEOUT}:
        return BaselineReport(
            ok=False,
            verdict=Verdict.BASELINE_INVALID,
            reason=(
                f"baseline evaluator {primary.verdict.value}: "
                f"{primary.error_message or 'see captured stderr'}"
            ),
            runs=runs,
            harness_ok=primary.verdict is not Verdict.TIMEOUT,
            output_stable=output_stable,
            output_stability_reason=output_reason,
        )

    expected = task.oracle.expected_baseline_verdict
    if primary.verdict != expected:
        return BaselineReport(
            ok=False,
            verdict=Verdict.BASELINE_INVALID,
            reason=(
                f"reference candidate produced {primary.verdict.value}, "
                f"expected {expected.value}"
            ),
            runs=runs,
        )

    behavior_runs: list[ExecutionResult] = []
    if task.behavior_validator is not None:
        with IsolatedWorkspace(source, prefix=f"gp-behavior-base-{task.id}-") as workspace:
            _install_reference(workspace, task)
            behavior_result = run_evaluator(
                workspace, task.behavior_validator, attempt=1, inherit_secrets=inherit_secrets
            )
            behavior_runs.append(behavior_result)
        if behavior_result.verdict is not Verdict.PASS:
            return BaselineReport(
                ok=False,
                verdict=Verdict.BASELINE_INVALID,
                reason=(
                    "behavior validator did not accept reference candidate: "
                    f"{behavior_result.verdict.value}"
                ),
                runs=runs,
                behavior_runs=behavior_runs,
                behavior_ok=False,
                behavior_reason="reference behavior validation failed",
                output_stable=output_stable,
                output_stability_reason=output_reason,
            )

    known_invalid_result = None
    if task.oracle.known_invalid:
        with IsolatedWorkspace(source, prefix=f"gp-invalid-{task.id}-") as workspace:
            try:
                payload = (source / task.oracle.known_invalid).read_text(encoding="utf-8")
            except OSError as exc:
                return BaselineReport(
                    ok=False,
                    verdict=Verdict.BASELINE_INVALID,
                    reason=f"known_invalid unreadable: {exc}",
                    runs=runs,
                    output_stable=output_stable,
                    output_stability_reason=output_reason,
                )
            workspace.write_text(task.candidate_file, payload)
            known_invalid_result = run_evaluator(
                workspace, task.evaluator, attempt=1, inherit_secrets=inherit_secrets
            )
            # IMPORTANT: a declared known-invalid fixture is a control for the
            # benchmark grader. A defective grader may legitimately accept it;
            # that is exactly the false-acceptance signal we are trying to find.
            # Therefore its mismatch is recorded, not treated as baseline failure.

    behavior_ok = None if task.behavior_validator is None else True
    behavior_reason = "" if task.behavior_validator is None else "reference behavior accepted"
    return BaselineReport(
        ok=True,
        verdict=primary.verdict,
        reason="baseline accepted",
        runs=runs,
        known_invalid=known_invalid_result,
        behavior_runs=behavior_runs,
        behavior_ok=behavior_ok,
        behavior_reason=behavior_reason,
        output_stable=output_stable,
        output_stability_reason=output_reason,
    )


def _install_reference(workspace: IsolatedWorkspace, task: TaskSpec) -> None:
    source = _source(task)
    ref = task.oracle.reference
    ref_path = source / ref
    if ref_path.is_file() and ref != task.candidate_file:
        workspace.write_text(task.candidate_file, ref_path.read_text(encoding="utf-8"))


def _source(task: TaskSpec):
    from pathlib import Path

    return Path(task.source_path)
