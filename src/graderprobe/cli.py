"""Command-line interface.

  graderprobe validate <task>
  graderprobe probe <task>
  graderprobe run <task>
  graderprobe report <result>
  graderprobe demo
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from graderprobe import __version__
from graderprobe.reports.certificate import write_certificate
from graderprobe.reports.html import render_html
from graderprobe.reports.json_report import write_json
from graderprobe.reports.markdown import render_markdown
from graderprobe.reports.terminal import render_terminal
from graderprobe.runner import RunConfig, run_task
from graderprobe.execution import set_execution_slots
from graderprobe.replay import replay_bundle, write_replay_manifest
from graderprobe.task import TaskError, load_task
from graderprobe.types import ProfileVerdict, Severity
from graderprobe.providers.openai import OpenAIProvider
from graderprobe.reports.sarif import write_sarif, profiles_to_sarif
from graderprobe.reports.release_sarif import write_release_sarif
from graderprobe.git import changed_task_files, GitError
from graderprobe.assurance import release_assurance, write_release_report
from graderprobe.causal import causal_audit, write_causal_report
from graderprobe.lockfile import create_lock, verify_lock
from graderprobe.integrations.harbor import inspect_harbor_task, write_manifest as write_harbor_manifest


EXIT_OK = 0
EXIT_WARNING = 2
EXIT_FAIL = 3
EXIT_BASELINE = 4
EXIT_USAGE = 64


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return EXIT_USAGE
    try:
        return int(args.handler(args))
    except TaskError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except (ValueError, RuntimeError, GitError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="graderprobe",
        description=(
            "An evaluator can be wrong even when its tests pass. "
            "GraderProbe probes the evaluator's decision boundary by checking "
            "changes that should NOT change the verdict and changes that SHOULD."
        ),
    )
    parser.add_argument("--version", action="version", version=f"graderprobe {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_val = sub.add_parser("validate", help="validate a task document and baseline")
    p_val.add_argument("task")
    p_val.set_defaults(handler=cmd_validate)

    p_probe = sub.add_parser("probe", help="list declared (and optional auto) probes")
    p_probe.add_argument("task")
    p_probe.add_argument("--auto", action="store_true")
    p_probe.add_argument("--auto-sensitive", action="store_true")
    p_probe.set_defaults(handler=cmd_probe)

    p_run = sub.add_parser("run", help="run boundary probes and write evidence")
    p_run.add_argument("task")
    p_run.add_argument("--out", default="graderprobe-out")
    p_run.add_argument("--fail-on", default="high", choices=["none", "high", "medium", "any"])
    p_run.add_argument("--auto", action="store_true")
    p_run.add_argument("--auto-sensitive", action="store_true")
    p_run.add_argument("--no-validate-behavior", action="store_false", dest="validate_behavior", default=True)
    p_run.add_argument("--validate-behavior-all", action="store_true")
    p_run.add_argument("--minimize", action="store_true")
    p_run.add_argument("--minimize-budget", type=int, default=12)
    p_run.add_argument("--workers", type=int, default=2, help="parallel probe workers (default: 2)")
    p_run.add_argument("--execution-slots", type=int, default=2, help="global evaluator process slots (default: 2)")
    p_run.add_argument("--repeat-baseline", type=int, default=None, help="override baseline repeats")
    p_run.add_argument("--semantic", action="store_true", help="add up to 3 optional OpenAI semantic probe proposals")
    p_run.add_argument("--model", default=None, help="OpenAI model for --semantic (or GRADERPROBE_OPENAI_MODEL)")
    p_run.add_argument("--model-max-output-tokens", type=int, default=1200)
    p_run.add_argument("--sarif-out", default=None, help="write SARIF 2.1.0 output")
    p_run.set_defaults(handler=cmd_run)

    p_replay = sub.add_parser("replay", help="re-run a recorded bundle and compare outcome fingerprint")
    p_replay.add_argument("bundle")
    p_replay.add_argument("--allow-source-drift", action="store_true")
    p_replay.add_argument("--out", default=None)
    p_replay.set_defaults(handler=cmd_replay)

    p_report = sub.add_parser("report", help="render a stored JSON profile")
    p_report.add_argument("result")
    p_report.add_argument("--format", default="terminal", choices=["terminal", "markdown", "html"])
    p_report.set_defaults(handler=cmd_report)

    p_audit = sub.add_parser("audit", help="audit one task or every task.yaml under a directory")
    p_audit.add_argument("path")
    p_audit.add_argument("--out", default="graderprobe-out/audit")
    p_audit.add_argument("--auto", action="store_true")
    p_audit.add_argument("--auto-sensitive", action="store_true")
    p_audit.add_argument("--no-validate-behavior", action="store_false", dest="validate_behavior", default=True)
    p_audit.add_argument("--validate-behavior-all", action="store_true")
    p_audit.add_argument("--minimize", action="store_true")
    p_audit.add_argument("--minimize-budget", type=int, default=12)
    p_audit.add_argument("--workers", type=int, default=2, help="parallel probe workers within each task (default: 2)")
    p_audit.add_argument("--task-workers", type=int, default=2, help="parallel tasks in audit (default: 2)")
    p_audit.add_argument("--execution-slots", type=int, default=4, help="global evaluator process slots (default: 4)")
    p_audit.add_argument("--repeat-baseline", type=int, default=None, help="override baseline repeats")
    p_audit.add_argument("--changed-only", action="store_true", help="audit only tasks affected by Git changes")
    p_audit.add_argument("--base-ref", default="HEAD~1", help="Git base ref for --changed-only")
    p_audit.add_argument("--semantic", action="store_true", help="add up to 3 optional OpenAI semantic probe proposals per task")
    p_audit.add_argument("--model", default=None)
    p_audit.add_argument("--model-max-output-tokens", type=int, default=1200)
    p_audit.add_argument("--sarif-out", default=None, help="write combined SARIF 2.1.0 output")
    p_audit.set_defaults(handler=cmd_audit)

    p_sarif = sub.add_parser("sarif", help="convert a stored profile JSON to SARIF 2.1.0")
    p_sarif.add_argument("result")
    p_sarif.add_argument("--out", default="graderprobe-out/results.sarif")
    p_sarif.set_defaults(handler=cmd_sarif)

    p_release = sub.add_parser("release-audit", help="compare changed evaluation tasks across Git revisions")
    p_release.add_argument("path", help="repository path")
    p_release.add_argument("--task-root", default="corpus/tasks", help="directory containing task.yaml files")
    p_release.add_argument("--base-ref", default="HEAD~1")
    p_release.add_argument("--head-ref", default="HEAD")
    p_release.add_argument("--out", default="graderprobe-out/release")
    p_release.add_argument("--auto", action="store_true")
    p_release.add_argument("--auto-sensitive", action="store_true")
    p_release.add_argument("--no-validate-behavior", action="store_false", dest="validate_behavior", default=True)
    p_release.add_argument("--minimize", action="store_true")
    p_release.add_argument("--minimize-budget", type=int, default=8)
    p_release.add_argument("--workers", type=int, default=1)
    p_release.add_argument("--execution-slots", type=int, default=1)
    p_release.add_argument("--repeat-baseline", type=int, default=None)
    p_release.add_argument("--semantic", action="store_true", help="add bounded OpenAI semantic review to changed tasks")
    p_release.add_argument("--model", default=None)
    p_release.add_argument("--model-max-output-tokens", type=int, default=1000)
    p_release.add_argument("--max-tasks", type=int, default=None)
    p_release.add_argument("--sarif-out", default=None, help="write release-assurance SARIF 2.1.0 output")
    p_release.add_argument("--causal-cohort", default=None, help="also run frozen-candidate causal attribution")
    p_release.set_defaults(handler=cmd_release_audit)

    p_causal = sub.add_parser("causal-audit", help="compare frozen candidates across evaluator revisions")
    p_causal.add_argument("path", help="repository path")
    p_causal.add_argument("--cohort", required=True, help="JSON frozen cohort manifest")
    p_causal.add_argument("--base-ref", default="HEAD~1")
    p_causal.add_argument("--head-ref", default="HEAD")
    p_causal.add_argument("--out", default="graderprobe-out/causal")
    p_causal.add_argument("--workers", type=int, default=1)
    p_causal.add_argument("--execution-slots", type=int, default=1)
    p_causal.set_defaults(handler=cmd_causal_audit)

    p_lock = sub.add_parser("lock", help="create a persistent evaluation-contract lockfile")
    p_lock.add_argument("path", help="repository path")
    p_lock.add_argument("--task-root", default="corpus/tasks")
    p_lock.add_argument("--out", default="graderprobe.lock.json")
    p_lock.add_argument("--anchors", type=int, default=2, help="number of deterministic behavioral anchors to execute (default: 2)")
    p_lock.set_defaults(handler=cmd_lock)

    p_verify_lock = sub.add_parser("verify-lock", help="verify a contract lock and changed evaluation behavior")
    p_verify_lock.add_argument("path", help="repository path")
    p_verify_lock.add_argument("--lock", default="graderprobe.lock.json")
    p_verify_lock.add_argument("--workers", type=int, default=1)
    p_verify_lock.add_argument("--execution-slots", type=int, default=1)
    p_verify_lock.set_defaults(handler=cmd_verify_lock)

    p_harbor = sub.add_parser("harbor-inspect", help="inspect a Harbor task package without pretending to run Harbor")
    p_harbor.add_argument("path")
    p_harbor.add_argument("--out", default=None)
    p_harbor.set_defaults(handler=cmd_harbor_inspect)

    p_demo = sub.add_parser("demo", help="run the offline demonstration corpus (no API calls)")
    p_demo.add_argument("--out", default="graderprobe-out/demo")
    p_demo.add_argument("--task", default=None)
    p_demo.set_defaults(handler=cmd_demo)
    return parser


def cmd_validate(args: argparse.Namespace) -> int:
    from graderprobe.baseline import validate_baseline

    task = load_task(args.task)
    report = validate_baseline(task)
    print(f"task {task.id}: {'OK' if report.ok else 'BASELINE_INVALID'}")
    print(report.reason)
    print(f"baseline verdict: {report.verdict.value}")
    return EXIT_OK if report.ok else EXIT_BASELINE


def cmd_probe(args: argparse.Namespace) -> int:
    task = load_task(args.task)
    probes = task.all_probes()
    if args.auto:
        from graderprobe.probes.engine import ProbeEngine

        source = Path(task.source_path) / task.candidate_file
        text = source.read_text(encoding="utf-8") if source.is_file() else ""
        engine = ProbeEngine(task)
        probes = probes + engine.auto_invariance(text)
        if args.auto_sensitive and task.behavior_validator is not None:
            probes = probes + engine.auto_sensitivity(text)
    if not probes:
        print("no probes declared")
        return EXIT_OK
    for probe in probes:
        print(
            f"{probe.id:16} {probe.probe_class.value:12} "
            f"{probe.method.value:16} {probe.transform.kind:20} {probe.description}"
        )
    return EXIT_OK


def cmd_run(args: argparse.Namespace) -> int:
    task = load_task(args.task)
    set_execution_slots(max(1, int(args.execution_slots)))
    provider = OpenAIProvider(model=args.model, max_output_tokens=args.model_max_output_tokens) if args.semantic else None
    config = RunConfig(
        include_auto_probes=args.auto,
        include_auto_sensitivity=args.auto_sensitive,
        validate_behavior=args.validate_behavior,
        validate_behavior_all=args.validate_behavior_all,
        minimize_counterfactuals=args.minimize,
        max_minimization_runs=max(1, args.minimize_budget),
        max_workers=max(1, args.workers),
        baseline_repeats_override=args.repeat_baseline,
        execution_slots=max(1, int(args.execution_slots)),
        include_model_probes=args.semantic,
        model_provider=provider,
        max_model_proposals=3,
    )
    profile = run_task(task, config=config, progress=_progress)
    profile_path = _write_outputs(task, profile, Path(args.out))
    write_replay_manifest(task, profile, profile_path, config, Path(args.out) / "replay.json", task_file=Path(args.task).resolve())
    if args.sarif_out:
        write_sarif(profile_path, args.sarif_out)
    print(render_terminal(profile))
    return _exit_for(profile, args.fail_on)


def cmd_report(args: argparse.Namespace) -> int:
    raw = json.loads(Path(args.result).read_text(encoding="utf-8"))
    if args.format == "markdown":
        sys.stdout.write(f"# {raw.get('task_id')}\n\nVerdict: `{raw.get('verdict')}`\n")
    elif args.format == "html":
        sys.stdout.write(
            f"<html><body><h1>{raw.get('task_id')}</h1><p>{raw.get('verdict')}</p></body></html>"
        )
    else:
        print("BOUNDARY INTEGRITY PROFILE")
        print(f"Task: {raw.get('task_id')}")
        print(f"Verdict: {raw.get('verdict')}")
        for finding in raw.get("findings") or []:
            if finding.get("type") in {"false_acceptance", "false_rejection", "baseline_invalid"}:
                print(f"{finding.get('probe_id')} {str(finding.get('severity', '')).upper()}")
                print(f"  {finding.get('summary')}")
    return EXIT_OK


def cmd_audit(args: argparse.Namespace) -> int:
    target = Path(args.path).resolve()
    if args.changed_only:
        try:
            tasks = changed_task_files(target if target.is_dir() else target.parent, base_ref=args.base_ref)
        except GitError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_USAGE
    else:
        tasks = [target] if target.is_file() else sorted(target.rglob("task.yaml"))
    if not tasks:
        print("no affected task.yaml files found" if args.changed_only else "no task.yaml files found", file=sys.stderr)
        return EXIT_USAGE
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    set_execution_slots(max(1, int(args.execution_slots)))

    provider = OpenAIProvider(model=args.model, max_output_tokens=args.model_max_output_tokens) if args.semantic else None

    def run_one(task_path: Path) -> dict:
        try:
            task = load_task(task_path)
            profile = run_task(
                task,
                config=RunConfig(
                    include_auto_probes=args.auto,
                    include_auto_sensitivity=args.auto_sensitive,
                    validate_behavior=args.validate_behavior,
                    minimize_counterfactuals=args.minimize,
                    max_minimization_runs=max(1, args.minimize_budget),
                    max_workers=max(1, args.workers),
                    task_workers=max(1, args.task_workers),
                    baseline_repeats_override=args.repeat_baseline,
                    execution_slots=max(1, int(args.execution_slots)),
                    include_model_probes=args.semantic,
                    model_provider=provider,
                    max_model_proposals=3,
                ),
                progress=_progress,
            )
            task_out = out / task.id
            profile_path = _write_outputs(task, profile, task_out)
            write_replay_manifest(task, profile, profile_path, config=RunConfig(
                include_auto_probes=args.auto,
                include_auto_sensitivity=args.auto_sensitive,
                validate_behavior=args.validate_behavior,
                validate_behavior_all=args.validate_behavior_all,
                minimize_counterfactuals=args.minimize,
                max_minimization_runs=max(1, args.minimize_budget),
                max_workers=max(1, args.workers),
                baseline_repeats_override=args.repeat_baseline,
                execution_slots=max(1, int(args.execution_slots)),
            ), path=task_out / "replay.json", task_file=task_path.resolve())
            return {
                "task_id": task.id,
                "verdict": profile.verdict.value,
                "findings": len(profile.findings),
                "false_acceptance_count": profile.metrics.false_acceptance_count,
                "false_rejection_count": profile.metrics.false_rejection_count,
                "inconclusive_count": profile.metrics.inconclusive_count,
                "error": None,
            }
        except (TaskError, OSError) as exc:
            return {"task_id": str(task_path), "verdict": "ERROR", "error": str(exc)}

    task_workers = max(1, min(int(args.task_workers), len(tasks)))
    profile_payloads: dict[int, dict] = {}
    results_by_index: dict[int, dict] = {}
    if task_workers == 1:
        for i, task_path in enumerate(tasks):
            results_by_index[i] = run_one(task_path)
    else:
        with ThreadPoolExecutor(max_workers=task_workers, thread_name_prefix="graderprobe-task") as pool:
            futures = {pool.submit(run_one, task_path): i for i, task_path in enumerate(tasks)}
            for future in as_completed(futures):
                results_by_index[futures[future]] = future.result()

    results = [results_by_index[i] for i in sorted(results_by_index)]
    exit_code = EXIT_OK
    for item in results:
        verdict = item.get("verdict")
        if verdict in {"BOUNDARY_FAIL", "BOUNDARY_WARNING"}:
            if verdict == "BOUNDARY_FAIL":
                exit_code = max(exit_code, EXIT_FAIL)
            else:
                exit_code = max(exit_code, EXIT_WARNING)
        elif verdict in {"BASELINE_INVALID", "ERROR"}:
            exit_code = max(exit_code, EXIT_BASELINE if verdict == "BASELINE_INVALID" else EXIT_USAGE)
    audit_payload = {"tasks": results, "task_workers": task_workers, "changed_only": bool(args.changed_only), "base_ref": args.base_ref if args.changed_only else None}
    (out / "audit.json").write_text(json.dumps(audit_payload, indent=2) + "\n", encoding="utf-8")
    if args.sarif_out:
        profiles = []
        for item in results:
            candidate = out / str(item.get("task_id")) / "profile.json"
            if candidate.is_file():
                try:
                    profiles.append(json.loads(candidate.read_text(encoding="utf-8")))
                except json.JSONDecodeError:
                    pass
        Path(args.sarif_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.sarif_out).write_text(json.dumps(profiles_to_sarif(profiles), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit_payload, indent=2))
    return exit_code


def cmd_release_audit(args: argparse.Namespace) -> int:
    repo = Path(args.path).resolve()
    task_root = (repo / args.task_root).resolve() if not Path(args.task_root).is_absolute() else Path(args.task_root).resolve()
    set_execution_slots(max(1, int(args.execution_slots)))
    provider = OpenAIProvider(model=args.model, max_output_tokens=args.model_max_output_tokens) if args.semantic else None
    config = RunConfig(
        include_auto_probes=args.auto,
        include_auto_sensitivity=args.auto_sensitive,
        validate_behavior=args.validate_behavior,
        minimize_counterfactuals=args.minimize,
        max_minimization_runs=max(1, args.minimize_budget),
        max_workers=max(1, args.workers),
        baseline_repeats_override=args.repeat_baseline,
        execution_slots=max(1, int(args.execution_slots)),
        include_model_probes=args.semantic,
        model_provider=provider,
        max_model_proposals=3,
    )
    report = release_assurance(
        repo,
        task_root=task_root,
        base_ref=args.base_ref,
        head_ref=args.head_ref,
        config=config,
        max_tasks=args.max_tasks,
    )
    paths = write_release_report(report, args.out)
    if args.causal_cohort:
        causal_report = causal_audit(
            repo,
            cohort=args.causal_cohort,
            base_ref=args.base_ref,
            head_ref=args.head_ref,
            config=RunConfig(max_workers=1, execution_slots=1, include_auto_probes=False, include_model_probes=False),
        )
        causal_paths = write_causal_report(causal_report, Path(args.out) / "causal")
        print(causal_paths[1].read_text(encoding="utf-8"))
        if causal_report.decision == "WARN" and report.decision == "ALLOW":
            report = __import__("dataclasses").replace(report, decision="WARN", notes=tuple(report.notes) + ("Frozen-candidate causal attribution reported evaluator-stack drift or non-comparability.",))
            paths = write_release_report(report, args.out)
    if args.sarif_out:
        write_release_sarif(report, args.sarif_out)
    print(paths[1].read_text(encoding="utf-8"))
    if report.decision == "BLOCK":
        return EXIT_FAIL
    if report.decision == "WARN":
        return EXIT_WARNING
    return EXIT_OK


def cmd_causal_audit(args: argparse.Namespace) -> int:
    report = causal_audit(
        args.path,
        cohort=args.cohort,
        base_ref=args.base_ref,
        head_ref=args.head_ref,
        config=RunConfig(max_workers=max(1, args.workers), execution_slots=max(1, args.execution_slots), include_auto_probes=False, include_model_probes=False),
    )
    paths = write_causal_report(report, args.out)
    print(paths[1].read_text(encoding="utf-8"))
    return EXIT_WARNING if report.decision == "WARN" else EXIT_OK


def cmd_lock(args: argparse.Namespace) -> int:
    payload = create_lock(args.path, task_root=Path(args.path) / args.task_root, out=args.out, anchor_count=max(0, args.anchors))
    print(json.dumps({"lock": str(Path(args.out).resolve()), "fingerprint": payload["lock_fingerprint"], "tasks": len(payload["task_inventory"]), "anchors": len(payload["anchors"])}, indent=2))
    return EXIT_OK


def cmd_verify_lock(args: argparse.Namespace) -> int:
    result = verify_lock(args.path, lock=args.lock, config=RunConfig(max_workers=max(1, args.workers), execution_slots=max(1, args.execution_slots), include_auto_probes=False, include_model_probes=False))
    print(json.dumps(result, indent=2, default=str))
    decision = result.get("decision")
    if decision == "BLOCK":
        return EXIT_FAIL
    if decision == "WARN":
        return EXIT_WARNING
    return EXIT_OK


def cmd_sarif(args: argparse.Namespace) -> int:
    write_sarif(args.result, args.out)
    print(args.out)
    return EXIT_OK


def cmd_harbor_inspect(args: argparse.Namespace) -> int:
    manifest = inspect_harbor_task(args.path)
    if args.out:
        write_harbor_manifest(args.path, args.out)
    print(json.dumps(manifest.to_dict(), indent=2))
    return EXIT_WARNING if manifest.warnings else EXIT_OK


def cmd_demo(args: argparse.Namespace) -> int:
    from graderprobe.demo import run_demo

    summary = run_demo(out_dir=Path(args.out), only=args.task, progress=_progress)
    print(summary["terminal"])
    return int(summary["exit_code"])


def cmd_replay(args: argparse.Namespace) -> int:
    result = replay_bundle(args.bundle, out_dir=args.out, allow_source_drift=args.allow_source_drift)
    print(json.dumps({
        "task_id": result["task_id"],
        "verdict": result["verdict"],
        "matched": result["matched"],
        "expected_fingerprint": result["expected_fingerprint"],
        "actual_fingerprint": result["actual_fingerprint"],
        "source_tree_digest": result["source_tree_digest"],
    }, indent=2))
    return EXIT_OK if result["matched"] else EXIT_FAIL


def _write_outputs(task, profile, out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    json_path = write_json(profile, out / "profile.json")
    (out / "profile.md").write_text(render_markdown(profile), encoding="utf-8")
    (out / "profile.html").write_text(render_html(profile), encoding="utf-8")
    write_certificate(task, profile, out / "CERTIFICATE.json", result_path=json_path)
    return json_path


def _exit_for(profile, fail_on: str) -> int:
    if profile.verdict is ProfileVerdict.BASELINE_INVALID:
        return EXIT_BASELINE
    if fail_on == "none":
        return EXIT_OK
    notables = [
        item
        for item in profile.findings
        if item.type.value in {"false_acceptance", "false_rejection"}
    ]
    if not notables:
        return EXIT_OK
    if fail_on == "any":
        return EXIT_FAIL
    if fail_on == "high" and any(item.severity is Severity.HIGH for item in notables):
        return EXIT_FAIL
    if fail_on == "medium" and any(
        item.severity in {Severity.HIGH, Severity.MEDIUM} for item in notables
    ):
        return EXIT_FAIL
    return EXIT_WARNING


def _progress(message: str) -> None:
    print(f"# {message}", file=sys.stderr)
