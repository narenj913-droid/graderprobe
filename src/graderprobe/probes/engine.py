"""Apply declared probes and generate conservative deterministic probes."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from graderprobe.isolation import IsolatedWorkspace
from graderprobe.probes.transforms import TransformError, apply_transform
from graderprobe.types import ExpectedRelation, ProbeClass, ProbeMethod, ProbeSpec, TaskSpec, TransformSpec


@dataclass
class AppliedProbe:
    spec: ProbeSpec
    original: str
    transformed: str
    target: str
    method: ProbeMethod
    validation_ok: bool
    validation_error: str = ""


def apply_probe(workspace: IsolatedWorkspace, task: TaskSpec, probe: ProbeSpec) -> AppliedProbe:
    target = probe.target or task.candidate_file
    if not workspace.exists(target):
        raise TransformError(f"probe {probe.id}: target missing: {target}")
    original = workspace.read_text(target)
    if probe.method is ProbeMethod.MODEL_GENERATED:
        # Model-generated probes are proposal inputs only; the transform registry
        # and syntax checks remain authoritative.
        pass
    try:
        transformed = apply_transform(
            original, probe.transform, workspace=workspace.path, target=target
        )
        if transformed == original:
            raise TransformError("transform produced no change")
        workspace.write_text(target, transformed)
        return AppliedProbe(
            spec=probe,
            original=original,
            transformed=transformed,
            target=target,
            method=probe.method,
            validation_ok=True,
        )
    except TransformError as exc:
        return AppliedProbe(
            spec=probe,
            original=original,
            transformed=original,
            target=target,
            method=probe.method,
            validation_ok=False,
            validation_error=str(exc),
        )


class ProbeEngine:
    def __init__(self, task: TaskSpec) -> None:
        self.task = task

    def declared(self) -> list[ProbeSpec]:
        return self.task.all_probes()

    def auto_invariance(self, source: str) -> list[ProbeSpec]:
        """Generate cheap AST-aware candidates that should preserve behavior."""
        probes: list[ProbeSpec] = [
            ProbeSpec(
                id="AUTO-INV-comment",
                probe_class=ProbeClass.INVARIANCE,
                description="Insert a no-op comment",
                expected_relation=ExpectedRelation.PRESERVE,
                transform=TransformSpec(kind="insert_comments", params={"comment": "noop"}),
            ),
            ProbeSpec(
                id="AUTO-INV-whitespace",
                probe_class=ProbeClass.INVARIANCE,
                description="Normalize whitespace without changing the AST",
                expected_relation=ExpectedRelation.PRESERVE,
                transform=TransformSpec(kind="normalize_whitespace", params={"blank_lines": 2}),
            ),
        ]
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return probes

        # Rename the first simple argument. This is structural, not regex-based.
        for node in ast.walk(tree):
            args = getattr(node, "args", None)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and args is not None:
                candidates = [a.arg for a in list(args.posonlyargs) + list(args.args) if a.arg not in {"self", "cls"}]
                if candidates:
                    old = candidates[0]
                    new = f"gp_{old}"
                    all_names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
                    all_names.update(a.arg for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for a in list(n.args.posonlyargs) + list(n.args.args))
                    if new not in all_names:
                        probes.append(
                            ProbeSpec(
                                id="AUTO-INV-rename-arg",
                                probe_class=ProbeClass.INVARIANCE,
                                description=f"AST-rename parameter {old} to {new}",
                                expected_relation=ExpectedRelation.PRESERVE,
                                transform=TransformSpec(kind="rename_identifiers", params={"mapping": {old: new}}),
                                notes="AST-aware syntactic candidate; independent behavior validation provides stronger evidence",
                            )
                        )
                break

        # Target one comparison rather than flipping every comparison in the file.
        compares = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Compare) and any(isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for op in n.ops)
        ]
        if compares:
            node = sorted(compares, key=lambda n: (n.lineno, n.col_offset))[0]
            probes.append(
                ProbeSpec(
                    id="AUTO-INV-rewrite-comparison",
                    probe_class=ProbeClass.INVARIANCE,
                    description=f"AST-rewrite comparison at line {node.lineno}",
                    expected_relation=ExpectedRelation.PRESERVE,
                    transform=TransformSpec(kind="ast_rewrite_comparison", params={"lineno": node.lineno}),
                    notes="Candidate transformation; behavior validation is required for strong evidence",
                )
            )
        return probes

    def auto_sensitivity(self, source: str) -> list[ProbeSpec]:
        """Generate targeted AST mutations; use only with independent behavior validation."""
        probes: list[ProbeSpec] = []
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return probes

        compares = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Compare)
            and any(isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Eq, ast.NotEq)) for op in n.ops)
        ]
        if compares:
            node = sorted(compares, key=lambda n: (n.lineno, n.col_offset))[0]
            probes.append(
                ProbeSpec(
                    id="AUTO-SEN-ast-flip-comparison",
                    probe_class=ProbeClass.SENSITIVITY,
                    description=f"Flip one comparison operator at line {node.lineno}",
                    expected_relation=ExpectedRelation.INVALIDATE,
                    transform=TransformSpec(kind="ast_flip_comparison", params={"lineno": node.lineno}),
                    notes="Heuristic semantic mutation; requires independent behavior validation",
                )
            )

        numeric_constants = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)
        ]
        if numeric_constants:
            node = sorted(numeric_constants, key=lambda n: (n.lineno, n.col_offset))[0]
            probes.append(
                ProbeSpec(
                    id="AUTO-SEN-ast-replace-constant",
                    probe_class=ProbeClass.SENSITIVITY,
                    description=f"Replace one numeric constant at line {node.lineno}",
                    expected_relation=ExpectedRelation.INVALIDATE,
                    transform=TransformSpec(
                        kind="ast_replace_constant",
                        params={"from": node.value, "to": node.value + 1, "lineno": node.lineno},
                    ),
                    notes="Heuristic boundary mutation; requires independent behavior validation",
                )
            )
        return probes
