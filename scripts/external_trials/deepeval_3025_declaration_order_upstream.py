#!/usr/bin/env python3
"""Run the declaration-order companion of DeepEval #3025 against an authorized checkout."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "corpus/external-trials/deepeval-3025-declaration-order"
EXPECTED_COMMIT = "c6d82ce"


def run(source: Path, repo: Path) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / "solution.py").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        (work / "evaluator.py").write_text((CASE / "evaluator.py").read_text(encoding="utf-8"), encoding="utf-8")
        env = os.environ.copy()
        paths = [str(repo)]
        if (repo / "src").is_dir():
            paths.insert(0, str(repo / "src"))
        if env.get("PYTHONPATH"):
            paths.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(paths)
        proc = subprocess.run([sys.executable, "evaluator.py"], cwd=work, env=env, capture_output=True, text=True, timeout=60)
        return proc.returncode, proc.stdout, proc.stderr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream-repo", type=Path, default=Path.cwd())
    ap.add_argument("--out", type=Path, default=ROOT / "artifacts/phase3/deepeval-3025-declaration-order.json")
    ap.add_argument("--require-issue-revision", action="store_true")
    args = ap.parse_args()
    repo = args.upstream_repo.resolve()
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception as exc:
        print(f"git_error={exc}", file=sys.stderr)
        return 2
    if args.require_issue_revision and not head.startswith(EXPECTED_COMMIT):
        return 3
    b = run(CASE / "solution.py", repo)
    t = run(CASE / "alternatives/deep_first_sync.py", repo)
    result = {
        "project": "DeepEval",
        "issue": "https://github.com/confident-ai/deepeval/issues/3025",
        "reported_revision": EXPECTED_COMMIT,
        "executed_repository": str(repo),
        "executed_revision": head,
        "baseline": {"returncode": b[0], "stdout": b[1], "stderr": b[2]},
        "transformed": {"returncode": t[0], "stdout": t[1], "stderr": t[2]},
        "status": "reproduced" if b[0] == 0 and t[0] == 1 else "not_reproduced_or_changed",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "reproduced" else 1


if __name__ == "__main__":
    raise SystemExit(main())
