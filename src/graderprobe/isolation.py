"""Isolated workspaces for candidate execution.

Candidate code and benchmark artifacts are treated as untrusted. This module
copies a task tree into a fresh directory and never writes back into the source
 tree. Isolation here is process-and-directory isolation, not a VM/container
security boundary; Docker mode in execution.py provides stronger containment.
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Iterator

SKIP_NAMES = frozenset({".git", "__pycache__", ".graderprobe", ".venv", "node_modules"})
SECRET_TOKENS = ("TOKEN", "SECRET", "PASSWORD", "API_KEY")


def resolve_within(root: Path, relative: str, *, allow_missing: bool = True) -> Path:
    root_resolved = root.resolve()
    candidate = Path(relative)
    if candidate.is_absolute():
        raise PermissionError(f"absolute path is not allowed: {relative}")
    resolved = (root_resolved / candidate).resolve(strict=not allow_missing)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise PermissionError(f"path escapes workspace: {relative}") from exc
    return resolved


class IsolatedWorkspace:
    """A temporary copy of a task directory that is deleted on close."""

    def __init__(self, source: Path, *, prefix: str = "graderprobe-", copy_mode: str = "auto") -> None:
        self.source = source.resolve()
        if not self.source.is_dir():
            raise NotADirectoryError(f"workspace source is not a directory: {self.source}")
        self._root = Path(tempfile.mkdtemp(prefix=prefix))
        self.path = self._root / "work"
        self.copy_mode = copy_mode
        _validate_tree_for_copy(self.source)
        _copy_tree(self.source, self.path, copy_mode=copy_mode)

    def close(self) -> None:
        shutil.rmtree(self._root, ignore_errors=True)

    def __enter__(self) -> "IsolatedWorkspace":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def write_text(self, relative: str, content: str) -> Path:
        dest = resolve_within(self.path, relative, allow_missing=True)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        return dest

    def read_text(self, relative: str) -> str:
        return resolve_within(self.path, relative, allow_missing=False).read_text(encoding="utf-8")

    def exists(self, relative: str) -> bool:
        try:
            return resolve_within(self.path, relative, allow_missing=True).exists()
        except PermissionError:
            return False


def _validate_tree_for_copy(src: Path) -> None:
    """Reject symlinks before any fast-copy path can duplicate them."""
    for root, dirs, files in os.walk(src, followlinks=False):
        dirs[:] = [name for name in dirs if name not in SKIP_NAMES]
        for name in dirs + files:
            path = Path(root) / name
            if path.is_symlink():
                raise PermissionError(f"refusing to copy symlink from task tree: {path}")
            if not (path.is_dir() or path.is_file()):
                raise OSError(f"unsupported filesystem entry in task tree: {path}")


def _copy_file(src: Path, dest: Path, *, copy_mode: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Spawning `cp` for tiny files is slower than Python's copy2. Use the
    # accelerated reflink path only for sufficiently large files.
    use_reflink = (
        copy_mode in {"auto", "reflink"}
        and _reflink_copy_available()
        and src.stat().st_size >= 1024 * 1024
    )
    if use_reflink:
        try:
            subprocess.run(
                ["cp", "--reflink=auto", "--no-preserve=ownership", str(src), str(dest)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            _drop_write_on_evaluator(src, dest)
            return
        except (OSError, subprocess.CalledProcessError):
            if copy_mode == "reflink":
                raise
    shutil.copy2(src, dest)
    _drop_write_on_evaluator(src, dest)


def _reflink_copy_available() -> bool:
    return os.name == "posix" and shutil.which("cp") is not None


def _copy_tree(src: Path, dest: Path, *, copy_mode: str = "auto") -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in SKIP_NAMES:
            continue
        target = dest / item.name
        if item.is_dir():
            _copy_tree(item, target, copy_mode=copy_mode)
        elif item.is_file():
            _copy_file(item, target, copy_mode=copy_mode)
        else:
            raise OSError(f"unsupported filesystem entry in task tree: {item}")


def _drop_write_on_evaluator(src: Path, dest: Path) -> None:
    mode = dest.stat().st_mode
    dest.chmod(mode & ~stat.S_IWGRP & ~stat.S_IWOTH)


def iter_python_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        if any(part in SKIP_NAMES for part in path.parts):
            continue
        yield path


def default_child_env(
    extra: dict[str, str] | None = None,
    *,
    inherit_secrets: bool = False,
) -> dict[str, str]:
    env = dict(os.environ)
    if not inherit_secrets:
        for key in list(env):
            if any(tag in key.upper() for tag in SECRET_TOKENS):
                env.pop(key, None)
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["GRADERPROBE"] = "1"
    if extra:
        env.update(extra)
    return env
