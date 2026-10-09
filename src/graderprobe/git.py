"""Small, read-only Git helpers for changed-task maintainer workflows."""
from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def changed_files(repo: str | Path, *, base_ref: str = "HEAD~1") -> list[Path]:
    repo = Path(repo).resolve()
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "diff", "--name-only", f"{base_ref}...HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except OSError as exc:
        raise GitError(f"unable to execute git: {exc}") from exc
    if proc.returncode != 0:
        raise GitError(proc.stderr.strip() or f"git diff failed with exit code {proc.returncode}")
    return [repo / line.strip() for line in proc.stdout.splitlines() if line.strip()]


def changed_task_files(
    repo: str | Path,
    *,
    base_ref: str = "HEAD~1",
    task_filename: str = "task.yaml",
) -> list[Path]:
    repo = Path(repo).resolve()
    out: set[Path] = set()
    for path in changed_files(repo, base_ref=base_ref):
        path = path.resolve()
        if path.name == task_filename and path.is_file():
            out.add(path)
            continue
        current = path.parent if path.suffix else path
        for parent in (current, *current.parents):
            candidate = parent / task_filename
            if candidate.is_file():
                out.add(candidate.resolve())
                break
            if parent == repo:
                break
    return sorted(out)
