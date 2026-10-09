#!/usr/bin/env python3
"""Run Inspect AI issue #4721 directly against an installed upstream package."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "corpus" / "external-trials" / "inspect-ai-4721"
EXPECTED_COMMIT = "1ea01a9"

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

def run_with_solution(cwd: Path, solution: Path) -> dict:
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / "solution.py").write_text(solution.read_text(encoding="utf-8"), encoding="utf-8")
        evaluator = TASK / "evaluator.py"
        (work / "evaluator.py").write_text(evaluator.read_text(encoding="utf-8"), encoding="utf-8")
        env = {**os.environ, "INSPECT_DISABLE_DOTENV": "1"}
        source_paths = [str(cwd)]
        if (cwd / "src").is_dir():
            source_paths.insert(0, str(cwd / "src"))
        if env.get("PYTHONPATH"):
            source_paths.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(source_paths)
        proc = subprocess.run(
            [sys.executable, str(work / "evaluator.py")],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}

def extract_verdict(stdout: str) -> str | None:
    m = re.search(r"(?m)^VERDICT=(.+)$", stdout)
    return m.group(1).strip() if m else None

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream-repo", type=Path, default=Path.cwd())
    ap.add_argument("--out", type=Path, default=ROOT / "artifacts" / "phase3" / "inspect-ai-4721-upstream-trial.json")
    ap.add_argument("--require-issue-revision", action="store_true")
    args = ap.parse_args()
    repo = args.upstream_repo.resolve()
    head = git_head(repo)
    repo_root = git_repo(repo)
    baseline = run_with_solution(repo, TASK / "solution.py")
    transformed = run_with_solution(repo, TASK / "alternatives" / "reversed_order.py")
    bver = extract_verdict(baseline["stdout"])
    tver = extract_verdict(transformed["stdout"])
    result = {
        "project": "Inspect AI",
        "issue": "https://github.com/UKGovernmentBEIS/inspect_ai/issues/4721",
        "reported_revision": EXPECTED_COMMIT,
        "executed_repository": str(repo_root or repo),
        "executed_revision": head,
        "baseline": baseline,
        "transformed": transformed,
        "observed_verdicts": [bver, tver],
        "expected_public_verdicts": ["C", "I"],
        "status": "reproduced" if bver == "C" and tver == "I" else "not_reproduced_or_changed",
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
