"""Budgeted counterfactual minimization.

The minimizer is deliberately empirical: it does not claim global semantic
minimality. It first reduces line-level edit atoms, then (when budget remains)
tries character-level reductions inside surviving changed lines. Predicate
results are cached by content hash to avoid duplicate executions.
"""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import hashlib
from typing import Callable


@dataclass(frozen=True)
class DiffHunk:
    index: int
    tag: str
    original_start: int
    original_end: int
    transformed_start: int
    transformed_end: int


@dataclass(frozen=True)
class _EditAtom:
    original_start: int
    original_end: int
    transformed_text: str
    original_text: str


@dataclass(frozen=True)
class MinimizationResult:
    source: str
    minimized: str
    hunks_total: int
    hunks_kept: int
    attempts: int
    budget: int
    minimality: str
    strategy: str = "line-atom"
    budget_exhausted: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "minimized": self.minimized,
            "hunks_total": self.hunks_total,
            "hunks_kept": self.hunks_kept,
            "attempts": self.attempts,
            "budget": self.budget,
            "minimality": self.minimality,
            "strategy": self.strategy,
            "budget_exhausted": self.budget_exhausted,
        }


def minimize_by_diff_hunks(
    original: str,
    transformed: str,
    predicate: Callable[[str], bool],
    *,
    budget: int = 24,
) -> MinimizationResult | None:
    """Reduce a counterfactual while preserving a truthy predicate.

    The algorithm is hierarchical and budgeted:
      1. atomic line edits from SequenceMatcher
      2. character-chunk reduction within surviving changed lines

    The result is never advertised as globally minimal.
    """
    if budget <= 0 or original == transformed:
        return None

    atoms = _line_atoms(original, transformed)
    if not atoms:
        return None

    cache: dict[str, bool] = {}
    attempts = 0

    def check(candidate: str) -> bool:
        nonlocal attempts
        key = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
        cached = cache.get(key)
        if cached is not None:
            return cached
        if attempts >= budget:
            return False
        attempts += 1
        result = bool(predicate(candidate))
        cache[key] = result
        return result

    current = set(range(len(atoms)))
    n = 2
    while len(current) > 1 and attempts < budget:
        ordered = sorted(current)
        chunk_count = min(n, len(ordered))
        chunks = [ordered[i::chunk_count] for i in range(chunk_count)]
        reduced = False
        for chunk in chunks:
            if attempts >= budget:
                break
            trial = current - set(chunk)
            if check(_build_from_atoms(original, atoms, trial)):
                current = trial
                n = max(2, n - 1)
                reduced = True
                break
        if not reduced:
            if n >= len(current):
                break
            n = min(len(current), n * 2)

    minimized = _build_from_atoms(original, atoms, current)
    strategy = "line-atom"

    # Character-level phase: only touch surviving changed line regions. This
    # often shrinks a one-line operator mutation from an entire line to the
    # smallest textual change that still satisfies the predicate.
    if attempts < budget and minimized != original:
        reduced = _character_reduce(original, minimized, check, lambda: attempts < budget)
        if reduced != minimized:
            minimized = reduced
            strategy = "line-atom+character"

    exhausted = attempts >= budget
    return MinimizationResult(
        source="original_to_transformed",
        minimized=minimized,
        hunks_total=len(atoms),
        hunks_kept=_count_surviving_atoms(original, transformed, minimized),
        attempts=attempts,
        budget=budget,
        minimality=(
            "best-effort hierarchical reduction; execution budget exhausted"
            if exhausted
            else ("1-minimal by hierarchical line/character edit under execution budget"
                  if strategy.endswith("character")
                  else "1-minimal by atomic line edit under execution budget")
        ),
        strategy=strategy,
        budget_exhausted=exhausted,
    )


def _line_atoms(original: str, transformed: str) -> list[_EditAtom]:
    old = original.splitlines(keepends=True)
    new = transformed.splitlines(keepends=True)
    atoms: list[_EditAtom] = []
    for tag, i1, i2, j1, j2 in SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        old_chunk = old[i1:i2]
        new_chunk = new[j1:j2]
        if tag == "replace":
            for k in range(max(len(old_chunk), len(new_chunk))):
                o = old_chunk[k] if k < len(old_chunk) else ""
                n = new_chunk[k] if k < len(new_chunk) else ""
                atoms.append(_EditAtom(i1 + min(k, len(old_chunk)), i1 + min(k + 1, len(old_chunk)), n, o))
        elif tag == "delete":
            for k, line in enumerate(old_chunk):
                atoms.append(_EditAtom(i1 + k, i1 + k + 1, "", line))
        elif tag == "insert":
            for k, line in enumerate(new_chunk):
                atoms.append(_EditAtom(i1, i1, line, ""))
    return atoms


def _build_from_atoms(original: str, atoms: list[_EditAtom], selected: set[int]) -> str:
    old = original.splitlines(keepends=True)
    out: list[str] = []
    pos = 0
    last_consumed = 0
    for idx, atom in enumerate(atoms):
        if atom.original_start < last_consumed and atom.original_start != atom.original_end:
            continue
        out.extend(old[pos:atom.original_start])
        if idx in selected:
            out.append(atom.transformed_text)
        else:
            out.append(atom.original_text)
        pos = max(pos, atom.original_end)
        last_consumed = max(last_consumed, atom.original_end)
    out.extend(old[pos:])
    return "".join(out)


def _character_reduce(
    original: str,
    current: str,
    check: Callable[[str], bool],
    budget_left: Callable[[], bool],
) -> str:
    # Work line-by-line so newline structure stays stable as long as possible.
    old_lines = original.splitlines(keepends=True)
    cur_lines = current.splitlines(keepends=True)
    if len(old_lines) != len(cur_lines):
        return current

    result = list(cur_lines)
    for line_idx, (old_line, cur_line) in enumerate(zip(old_lines, result)):
        if old_line == cur_line or not budget_left():
            continue
        old_body = old_line.rstrip("\n")
        cur_body = cur_line.rstrip("\n")
        if old_body == cur_body:
            continue

        matcher = SequenceMatcher(a=old_body, b=cur_body, autojunk=False)
        changed_spans = [op for op in matcher.get_opcodes() if op[0] != "equal"]
        for tag, _i1, _i2, j1, j2 in changed_spans:
            if not budget_left():
                break
            if tag not in {"replace", "insert"}:
                continue
            changed = cur_body[j1:j2]
            if not changed:
                continue
            # Try removing chunks from the changed text, progressively.
            n = 2
            while len(changed) > 1 and budget_left():
                width = max(1, (len(changed) + n - 1) // n)
                reduced_here = False
                start = 0
                while start < len(changed) and budget_left():
                    end = min(len(changed), start + width)
                    trial_changed = changed[:start] + changed[end:]
                    trial_body = cur_body[:j1] + trial_changed + cur_body[j2:]
                    trial_lines = list(result)
                    trial_lines[line_idx] = trial_body + ("\n" if cur_line.endswith("\n") else "")
                    trial = "".join(trial_lines)
                    if check(trial):
                        result = trial_lines
                        cur_body = trial_body
                        changed = trial_changed
                        reduced_here = True
                        break
                    start = end
                if not reduced_here:
                    if n >= len(changed):
                        break
                    n = min(len(changed), n * 2)
    return "".join(result)


def _count_surviving_atoms(original: str, transformed: str, minimized: str) -> int:
    original_lines = original.splitlines(keepends=True)
    transformed_lines = transformed.splitlines(keepends=True)
    minimized_lines = minimized.splitlines(keepends=True)
    original_ops = [op for op in SequenceMatcher(a=original_lines, b=transformed_lines, autojunk=False).get_opcodes() if op[0] != "equal"]
    total = 0
    for tag, i1, i2, j1, j2 in original_ops:
        width = max(i2 - i1, j2 - j1)
        total += width
    # A conservative indicator: whether the minimized text still differs from original.
    if minimized_lines == original_lines:
        return 0
    return min(total, max(1, len([1 for a, b in zip(original_lines, minimized_lines) if a != b])))
