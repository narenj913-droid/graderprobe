#!/usr/bin/env python3
"""Run DeepEval issue #3338 directly against an installed upstream package."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "corpus" / "external-trials" / "deepeval-3338" / "task.yaml"
EXPECTED_COMMIT = "d65c8da"

def git_head(cwd: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None

def git_repo(cwd: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None

def run_direct_solution(cwd: Path, solution_source: Path) -> dict:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tdpath = Path(td)
        (tdpath / "solution.py").write_text(solution_source.read_text(encoding="utf-8"), encoding="utf-8")
        evaluator = TASK.parent / "evaluator.py"
        (tdpath / "evaluator.py").write_text(evaluator.read_text(encoding="utf-8"), encoding="utf-8")
        proc = subprocess.run([sys.executable, str(tdpath / "evaluator.py")], cwd=cwd, env={**os.environ, "DEEPEVAL_DISABLE_DOTENV": "1", "PYTHONPATH": os.pathsep.join([*( [str(cwd / "src")] if (cwd / "src").is_dir() else []), str(cwd), *([os.environ["PYTHONPATH"]] if os.environ.get("PYTHONPATH") else [])])}, capture_output=True, text=True, timeout=30)
        return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream-repo", type=Path, default=Path.cwd())
    ap.add_argument("--out", type=Path, default=ROOT / "artifacts" / "phase3" / "deepeval-3338-upstream-trial.json")
    ap.add_argument("--require-issue-revision", action="store_true")
    args = ap.parse_args()
    repo = args.upstream_repo.resolve()
    head = git_head(repo)
    repo_root = git_repo(repo)
    baseline = run_direct_solution(repo, TASK.parent / "solution.py")
    transformed = run_direct_solution(repo, TASK.parent / "alternatives" / "reversed_expected.py")
    result = {
        "project": "DeepEval",
        "issue": "https://github.com/confident-ai/deepeval/issues/3338",
        "reported_revision": EXPECTED_COMMIT,
        "executed_repository": str(repo_root or repo),
        "executed_revision": head,
        "baseline": baseline,
        "transformed": transformed,
        "expected_public_pair": [0.5, 0.6667],
        "status": "reproduced" if baseline["returncode"] == 0 and transformed["returncode"] == 1 else "not_reproduced_or_changed",
    }
    if baseline["returncode"] == 10 or transformed["returncode"] == 10:
        result["status"] = "dependency_or_import_error"
        rc = 2
    elif args.require_issue_revision and not (head == EXPECTED_COMMIT or (head and head.startswith(EXPECTED_COMMIT))):
        result["status"] = "wrong_revision"
        rc = 3
    else:
        rc = 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return rc

if __name__ == "__main__":
    raise SystemExit(main())
