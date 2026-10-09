"""Locate the bundled offline demonstration corpus."""

from __future__ import annotations

from pathlib import Path

from graderprobe.task import load_task
from graderprobe.types import TaskSpec

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = PACKAGE_ROOT / "corpus" / "tasks"


def corpus_dir() -> Path:
    env = Path(__file__).resolve().parents[2] / "corpus" / "tasks"
    if env.is_dir():
        return env
    # Editable install fallback: look next to the package.
    alt = Path(__file__).resolve().parents[1].parent / "corpus" / "tasks"
    return alt if alt.is_dir() else CORPUS_DIR


def list_task_files(root: Path | None = None) -> list[Path]:
    root = root or corpus_dir()
    files = sorted(root.glob("*/task.yaml"))
    return files


def load_corpus(root: Path | None = None) -> list[TaskSpec]:
    return [load_task(path) for path in list_task_files(root)]
