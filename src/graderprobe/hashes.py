"""Content addressing helpers used by evidence and certificates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256_text(payload)


def hash_tree(root: Path, *, ignore_names: frozenset[str] | None = None) -> dict[str, str]:
    skip = ignore_names or frozenset({".git", "__pycache__", ".graderprobe"})
    out: dict[str, str] = {}
    if not root.exists():
        return out
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            continue
        if not path.is_file():
            continue
        if any(part in skip for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        out[rel] = sha256_file(path)
    return out


def merkle_like(file_hashes: Mapping[str, str]) -> str:
    """A deterministic digest over a path→hash map. Not a cryptographic merkle tree."""
    return sha256_json(dict(sorted(file_hashes.items())))
