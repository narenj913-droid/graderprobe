#!/usr/bin/env python3
"""Run DeepEval #3025 without modifying the maintainer's checkout."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
CASE = HERE / "corpus/external-trials/deepeval-3025"
EVALUATOR = CASE / "evaluator.py"


def run_config(source: Path, repo: Path) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "evaluator.py").write_text(EVALUATOR.read_text(encoding="utf-8"), encoding="utf-8")
        (tmp / "solution.py").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        env = os.environ.copy()
        source_paths = [str(repo)]
        if (repo / "src").is_dir():
            source_paths.insert(0, str(repo / "src"))
        prior = env.get("PYTHONPATH")
        env["PYTHONPATH"] = os.pathsep.join(source_paths + ([prior] if prior else []))
        proc = subprocess.run(
            [sys.executable, "evaluator.py"],
            cwd=tmp,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return proc.returncode, proc.stdout.strip() + ("\n" + proc.stderr.strip() if proc.stderr else "")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--require-issue-revision", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    variants = {
        "baseline": CASE / "solution.py",
        "sync_counterfactual": CASE / "alternatives/sync_same_order.py",
        "order_counterfactual": CASE / "alternatives/shallow_first_async.py",
    }
    outputs = {name: run_config(path, repo) for name, path in variants.items()}

    try:
        head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    except Exception as exc:
        print(f"git_head_error={exc}", file=sys.stderr)
        return 2

    expected_revision = "c6d82ce"
    if args.require_issue_revision and not head.startswith(expected_revision):
        return 3

    result = {
        "project": "DeepEval",
        "issue": 3025,
        "reported_revision": expected_revision,
        "executed_repo": str(repo),
        "executed_git_head": head,
        "runs": {name: {"returncode": rc, "output": out} for name, (rc, out) in outputs.items()},
        "status": "reproduced"
        if outputs["baseline"][0] == 0
        and outputs["sync_counterfactual"][0] == 1
        and outputs["order_counterfactual"][0] == 1
        else "not_reproduced",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "reproduced" else 1


if __name__ == "__main__":
    raise SystemExit(main())
