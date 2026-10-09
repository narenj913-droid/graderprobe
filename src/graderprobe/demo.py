"""Offline scientific demonstration. Zero API calls. Fixed qualitative findings."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

from graderprobe.corpus import list_task_files, load_corpus
from graderprobe.reports.certificate import write_certificate
from graderprobe.reports.html import render_html
from graderprobe.reports.json_report import dump_json, write_json
from graderprobe.reports.markdown import render_markdown
from graderprobe.reports.terminal import render_terminal
from graderprobe.runner import RunConfig, run_task
from graderprobe.task import load_task
from graderprobe.types import FindingType, ProfileVerdict


def run_demo(
    *,
    out_dir: Path,
    only: str | None = None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log = progress or (lambda _m: None)
    files = list_task_files()
    if only:
        files = [p for p in files if p.parent.name == only or load_task(p).id == only]
        if not files:
            raise FileNotFoundError(f"corpus task not found: {only}")

    profiles_by_id: dict[str, Any] = {}

    def _run_one(path: Path):
        task = load_task(path)
        log(f"demo:{task.id}")
        # Demo-level parallelism is capped at two tasks, while each task uses a
        # single probe worker. This avoids nested thread/process amplification.
        profile = run_task(task, config=RunConfig(seed=0, max_workers=1), progress=None)
        dest = out_dir / task.id
        dest.mkdir(parents=True, exist_ok=True)
        json_path = write_json(profile, dest / "profile.json")
        (dest / "profile.md").write_text(render_markdown(profile), encoding="utf-8")
        (dest / "profile.html").write_text(render_html(profile), encoding="utf-8")
        write_certificate(task, profile, dest / "CERTIFICATE.json", result_path=json_path)
        return task.id, profile

    workers = min(2, len(files))
    with ThreadPoolExecutor(max_workers=max(1, workers), thread_name_prefix="graderprobe-demo") as pool:
        futures = [pool.submit(_run_one, path) for path in files]
        for future in as_completed(futures):
            task_id, profile = future.result()
            profiles_by_id[task_id] = profile

    profiles = [profiles_by_id[load_task(path).id] for path in files]

    summary = _summarize(profiles)
    dump_json(summary, out_dir / "summary.json")
    (out_dir / "summary.md").write_text(_summary_markdown(summary, profiles), encoding="utf-8")
    terminal = _summary_terminal(summary, profiles)
    (out_dir / "summary.txt").write_text(terminal, encoding="utf-8")
    summary["terminal"] = terminal
    summary["exit_code"] = 0
    return summary


def _summarize(profiles) -> dict[str, Any]:
    fa = fr = baseline_invalid = ok = warn = fail = inc = 0
    rows = []
    for profile in profiles:
        fa += profile.metrics.false_acceptance_count
        fr += profile.metrics.false_rejection_count
        if profile.verdict is ProfileVerdict.BASELINE_INVALID:
            baseline_invalid += 1
        elif profile.verdict is ProfileVerdict.BOUNDARY_OK:
            ok += 1
        elif profile.verdict is ProfileVerdict.BOUNDARY_WARNING:
            warn += 1
        elif profile.verdict is ProfileVerdict.INCONCLUSIVE:
            inc += 1
        else:
            fail += 1
        rows.append(
            {
                "task_id": profile.task_id,
                "title": profile.task_title,
                "verdict": profile.verdict.value,
                "baseline": profile.baseline.verdict.value,
                "baseline_ok": profile.baseline.ok,
                "false_acceptance": profile.metrics.false_acceptance_count,
                "false_rejection": profile.metrics.false_rejection_count,
                "invariance": {
                    "preserved": profile.metrics.invariance_preserved,
                    "executed": profile.metrics.invariance_executed,
                    "rate": profile.metrics.invariance_preservation_rate,
                },
                "sensitivity": {
                    "detected": profile.metrics.sensitivity_detected,
                    "executed": profile.metrics.sensitivity_executed,
                    "rate": profile.metrics.sensitivity_detection_rate,
                },
            }
        )
    n = len(profiles)
    return {
        "schema": "graderprobe.demo_summary.v1",
        "n_tasks": n,
        "honesty": (
            f"This demonstration uses n={n} synthetic tasks from a corpus "
            "containing intentionally defective evaluators. It does not "
            "establish general benchmark validity. No confidence interval "
            "is reported because n<30."
        ),
        "counts": {
            "boundary_ok": ok,
            "boundary_warning": warn,
            "boundary_fail": fail,
            "baseline_invalid": baseline_invalid,
            "inconclusive": inc,
            "false_acceptance_findings": fa,
            "false_rejection_findings": fr,
        },
        "tasks": rows,
    }


def _summary_terminal(summary: dict[str, Any], profiles) -> str:
    lines = [
        "GRADERPROBE OFFLINE DEMO",
        f"n={summary['n_tasks']} synthetic tasks",
        summary["honesty"],
        "",
    ]
    for profile in profiles:
        lines.append(render_terminal(profile).rstrip())
        lines.append("-" * 56)
    c = summary["counts"]
    lines += [
        "CORPUS TOTALS",
        f"  BOUNDARY_OK           {c['boundary_ok']}",
        f"  BOUNDARY_WARNING      {c['boundary_warning']}",
        f"  BOUNDARY_FAIL         {c['boundary_fail']}",
        f"  BASELINE_INVALID      {c['baseline_invalid']}",
        f"  INCONCLUSIVE          {c['inconclusive']}",
        f"  false acceptance      {c['false_acceptance_findings']}",
        f"  false rejection       {c['false_rejection_findings']}",
        "",
        "Passing Boundary Tests does not prove an evaluator is correct.",
        "",
    ]
    return "\n".join(lines)


def _summary_markdown(summary: dict[str, Any], profiles) -> str:
    lines = [
        "# GraderProbe offline demo",
        "",
        summary["honesty"],
        "",
        "| Task | Verdict | FA | FR | Inv | Sen |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in summary["tasks"]:
        inv = row["invariance"]
        sen = row["sensitivity"]
        lines.append(
            f"| `{row['task_id']}` | `{row['verdict']}` | {row['false_acceptance']} | "
            f"{row['false_rejection']} | {inv['preserved']}/{inv['executed']} | "
            f"{sen['detected']}/{sen['executed']} |"
        )
    lines += ["", "Passing Boundary Tests does not prove an evaluator is correct.", ""]
    return "\n".join(lines)
