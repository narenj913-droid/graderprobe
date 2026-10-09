"""Deterministic candidate transformations.

Operators are intentionally conservative. Invariance operators are *intended*
to preserve behavior; sensitivity operators are *intended* to violate a stated
requirement. The evaluator's reaction is the measurement. AST-aware operators
provide structural targeting without claiming semantic equivalence.
"""

from __future__ import annotations

import ast
import re
import textwrap
from pathlib import Path
from typing import Any, Callable

from graderprobe.isolation import resolve_within
from graderprobe.types import TransformSpec


class TransformError(ValueError):
    """Raised when a transform cannot be applied structurally."""


TransformFn = Callable[[str, dict[str, Any], Path], str]


def apply_transform(source: str, spec: TransformSpec, *, workspace: Path, target: str) -> str:
    fn = TRANSFORMS.get(spec.kind)
    if fn is None:
        raise TransformError(f"unknown transform kind: {spec.kind}")
    return fn(source, dict(spec.params), workspace)


def transform_replace_file(source: str, params: dict[str, Any], workspace: Path) -> str:
    rel = params.get("source") or params.get("path")
    if not rel:
        raise TransformError("replace_file requires source")
    try:
        path = resolve_within(workspace, str(rel), allow_missing=False)
    except PermissionError as exc:
        raise TransformError(str(exc)) from exc
    if not path.is_file():
        raise TransformError(f"replace_file missing: {rel}")
    return path.read_text(encoding="utf-8")


def transform_rename_identifiers(source: str, params: dict[str, Any], workspace: Path) -> str:
    mapping = params.get("mapping") or {}
    if not mapping:
        raise TransformError("rename_identifiers requires mapping")
    tree = _parse(source)

    class Renamer(ast.NodeTransformer):
        def visit_Name(self, node: ast.Name) -> ast.Name:
            if node.id in mapping:
                return ast.copy_location(ast.Name(id=mapping[node.id], ctx=node.ctx), node)
            return node

        def visit_arg(self, node: ast.arg) -> ast.arg:
            if node.arg in mapping:
                node.arg = mapping[node.arg]
            return node

        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
            if node.name in mapping:
                node.name = mapping[node.name]
            return self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
            if node.name in mapping:
                node.name = mapping[node.name]
            return self.generic_visit(node)

    tree = Renamer().visit(tree)
    ast.fix_missing_locations(tree)
    return _unparse(tree)


def transform_insert_comments(source: str, params: dict[str, Any], workspace: Path) -> str:
    comment = str(params.get("comment", "invariance: formatting only"))
    return f"# {comment}\n{source}"


def transform_normalize_whitespace(source: str, params: dict[str, Any], workspace: Path) -> str:
    extra = max(0, int(params.get("blank_lines", 1)))
    body = source.rstrip() + ("\n" * (extra + 1))
    return body.replace("\t", "    ")


def transform_rewrite_comparisons(source: str, params: dict[str, Any], workspace: Path) -> str:
    tree = _parse(source)

    class Rewrite(ast.NodeTransformer):
        def visit_Compare(self, node: ast.Compare) -> ast.AST:
            self.generic_visit(node)
            if len(node.ops) != 1 or len(node.comparators) != 1:
                return node
            op = node.ops[0]
            swapped = {ast.Lt: ast.Gt, ast.LtE: ast.GtE, ast.Gt: ast.Lt, ast.GtE: ast.LtE}
            if type(op) in swapped:
                return ast.copy_location(
                    ast.Compare(
                        left=node.comparators[0],
                        ops=[swapped[type(op)]()],
                        comparators=[node.left],
                    ),
                    node,
                )
            return node

    tree = Rewrite().visit(tree)
    ast.fix_missing_locations(tree)
    out = _unparse(tree)
    if out == _unparse(_parse(source)):
        raise TransformError("rewrite_comparisons found no supported comparison")
    return out


def transform_expand_return(source: str, params: dict[str, Any], workspace: Path) -> str:
    name = str(params.get("name", "_probe_result"))
    tree = _parse(source)

    class Expand(ast.NodeTransformer):
        def visit_Return(self, node: ast.Return) -> ast.AST | list[ast.AST]:
            if node.value is None:
                return node
            assign = ast.Assign(
                targets=[ast.Name(id=name, ctx=ast.Store())],
                value=node.value,
            )
            ret = ast.Return(value=ast.Name(id=name, ctx=ast.Load()))
            return [ast.copy_location(assign, node), ast.copy_location(ret, node)]

    tree = Expand().visit(tree)
    ast.fix_missing_locations(tree)
    return _unparse(tree)


def transform_quote_style(source: str, params: dict[str, Any], workspace: Path) -> str:
    tree = _parse(source)
    text = _unparse(tree)
    style = str(params.get("style", "single"))
    if style == "single":
        return text
    if style == "double":
        return text.replace("'", '"')
    raise TransformError(f"unsupported quote style: {style}")


def transform_delete_matching(source: str, params: dict[str, Any], workspace: Path) -> str:
    pattern = params.get("pattern")
    if not pattern:
        raise TransformError("delete_matching requires pattern")
    regex = re.compile(str(pattern))
    kept = [line for line in source.splitlines(True) if not regex.search(line)]
    if kept == list(source.splitlines(True)):
        raise TransformError("delete_matching did not change source")
    return "".join(kept)


def transform_replace_literal(source: str, params: dict[str, Any], workspace: Path) -> str:
    before = params.get("from")
    after = params.get("to")
    if before is None or after is None:
        raise TransformError("replace_literal requires from and to")
    tree = _parse(source)
    changed = False

    class Lit(ast.NodeTransformer):
        def visit_Constant(self, node: ast.Constant) -> ast.AST:
            nonlocal changed
            if node.value == before:
                changed = True
                return ast.copy_location(ast.Constant(value=after), node)
            return node

    tree = Lit().visit(tree)
    ast.fix_missing_locations(tree)
    if not changed:
        raise TransformError("replace_literal did not find matching literal")
    return _unparse(tree)


def transform_flip_operator(source: str, params: dict[str, Any], workspace: Path) -> str:
    """Flip all supported comparisons; prefer ``ast_flip_comparison`` for targeted probes."""
    tree = _parse(source)
    changed = False
    mapping = {
        ast.LtE: ast.Lt,
        ast.GtE: ast.Gt,
        ast.Lt: ast.LtE,
        ast.Gt: ast.GtE,
        ast.Eq: ast.NotEq,
        ast.NotEq: ast.Eq,
        ast.Is: ast.IsNot,
        ast.IsNot: ast.Is,
    }

    class FlipOp(ast.NodeTransformer):
        def visit_Compare(self, node: ast.Compare) -> ast.AST:
            nonlocal changed
            self.generic_visit(node)
            new_ops = []
            for op in node.ops:
                new_type = mapping.get(type(op))
                if new_type is None:
                    new_ops.append(op)
                else:
                    changed = True
                    new_ops.append(new_type())
            node.ops = new_ops
            return node

    tree = FlipOp().visit(tree)
    ast.fix_missing_locations(tree)
    if not changed:
        raise TransformError("flip_operator found no supported comparison")
    return _unparse(tree)


def transform_ast_rewrite_comparison(source: str, params: dict[str, Any], workspace: Path) -> str:
    """Rewrite one strict comparison to an operand-swapped equivalent."""
    tree = _parse(source)
    lineno = params.get("lineno")
    occurrence = max(1, int(params.get("occurrence", 1)))
    pairs = {ast.Lt: ast.Gt, ast.LtE: ast.GtE, ast.Gt: ast.Lt, ast.GtE: ast.LtE}
    candidates = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in pairs
    ]
    if lineno is not None:
        candidates = [node for node in candidates if node.lineno == int(lineno)]
    candidates = sorted(candidates, key=lambda node: (node.lineno, node.col_offset))
    if len(candidates) < occurrence:
        raise TransformError("ast_rewrite_comparison target not found")
    node = candidates[occurrence - 1]
    op = type(node.ops[0])
    replacement = ast.Compare(
        left=node.comparators[0],
        ops=[pairs[op]()],
        comparators=[node.left],
    )
    tree = _replace_identity(tree, node, replacement)
    ast.fix_missing_locations(tree)
    return _unparse(tree)


def _replace_identity(tree: ast.AST, target: ast.AST, replacement: ast.AST) -> ast.AST:
    class Replacer(ast.NodeTransformer):
        def generic_visit(self, node: ast.AST) -> ast.AST:
            if node is target:
                return ast.copy_location(replacement, target)
            return super().generic_visit(node)
    return Replacer().visit(tree)


def transform_ast_flip_comparison(source: str, params: dict[str, Any], workspace: Path) -> str:
    """Flip one comparison selected by source location or ordinal."""
    tree = _parse(source)
    lineno = params.get("lineno")
    occurrence = max(1, int(params.get("occurrence", 1)))
    mapping = {
        ast.LtE: ast.Lt,
        ast.GtE: ast.Gt,
        ast.Lt: ast.LtE,
        ast.Gt: ast.GtE,
        ast.Eq: ast.NotEq,
        ast.NotEq: ast.Eq,
        ast.Is: ast.IsNot,
        ast.IsNot: ast.Is,
    }
    candidates = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Compare) and any(type(op) in mapping for op in node.ops)
    ]
    if lineno is not None:
        candidates = [node for node in candidates if getattr(node, "lineno", None) == int(lineno)]
    if len(candidates) < occurrence:
        raise TransformError("ast_flip_comparison target not found")
    node = sorted(candidates, key=lambda item: (item.lineno, item.col_offset))[occurrence - 1]
    changed = False
    for idx, op in enumerate(node.ops):
        replacement = mapping.get(type(op))
        if replacement is not None:
            node.ops[idx] = replacement()
            changed = True
            break
    if not changed:
        raise TransformError("ast_flip_comparison target has no supported operator")
    ast.fix_missing_locations(tree)
    return _unparse(tree)


def transform_ast_replace_constant(source: str, params: dict[str, Any], workspace: Path) -> str:
    """Replace one literal at an optional source location."""
    tree = _parse(source)
    before = params.get("from")
    if "to" not in params:
        raise TransformError("ast_replace_constant requires 'to'")
    after = params["to"]
    lineno = params.get("lineno")
    occurrence = max(1, int(params.get("occurrence", 1)))
    nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Constant) and node.value == before]
    if lineno is not None:
        nodes = [node for node in nodes if getattr(node, "lineno", None) == int(lineno)]
    if len(nodes) < occurrence:
        raise TransformError("ast_replace_constant target not found")
    node = sorted(nodes, key=lambda item: (item.lineno, item.col_offset))[occurrence - 1]
    replacement = ast.copy_location(ast.Constant(value=after), node)

    class ReplaceOne(ast.NodeTransformer):
        def visit_Constant(self, current: ast.Constant) -> ast.AST:
            if current is node:
                return replacement
            return current

    tree = ReplaceOne().visit(tree)
    ast.fix_missing_locations(tree)
    return _unparse(tree)


def transform_constant_return(source: str, params: dict[str, Any], workspace: Path) -> str:
    value = params.get("value", None)
    fn_name = params.get("function")
    tree = _parse(source)
    changed = False

    class Const(ast.NodeTransformer):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
            nonlocal changed
            if fn_name and node.name != fn_name:
                return self.generic_visit(node)
            changed = True
            node.body = [ast.copy_location(ast.Return(value=ast.Constant(value=value)), node.body[0] if node.body else node)]
            return node

    tree = Const().visit(tree)
    ast.fix_missing_locations(tree)
    if not changed:
        raise TransformError("constant_return target function not found")
    return _unparse(tree)


def transform_prepend_text(source: str, params: dict[str, Any], workspace: Path) -> str:
    return str(params.get("text", "")) + source


def transform_wrap_function(source: str, params: dict[str, Any], workspace: Path) -> str:
    fn_name = str(params.get("function", ""))
    helper = str(params.get("helper", f"{fn_name}_impl" if fn_name else "_impl"))
    if not fn_name:
        raise TransformError("wrap_function requires function")
    tree = _parse(source)

    class Wrap(ast.NodeTransformer):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> list[ast.AST]:
            if node.name != fn_name:
                return [self.generic_visit(node)]
            inner = ast.FunctionDef(
                name=helper,
                args=node.args,
                body=node.body,
                decorator_list=[],
                returns=node.returns,
            )
            args_fwd, keywords_fwd = _forward_call(node.args)
            outer = ast.FunctionDef(
                name=fn_name,
                args=node.args,
                body=[
                    ast.Return(
                        value=ast.Call(
                            func=ast.Name(id=helper, ctx=ast.Load()),
                            args=args_fwd,
                            keywords=keywords_fwd,
                        )
                    )
                ],
                decorator_list=node.decorator_list,
                returns=node.returns,
            )
            return [inner, outer]

    tree = Wrap().visit(tree)
    ast.fix_missing_locations(tree)
    return _unparse(tree)


def _forward_call(args: ast.arguments) -> tuple[list[ast.expr], list[ast.keyword]]:
    positional: list[ast.expr] = []
    keywords: list[ast.keyword] = []
    for arg in list(args.posonlyargs) + list(args.args):
        positional.append(ast.Name(id=arg.arg, ctx=ast.Load()))
    if args.vararg:
        positional.append(ast.Starred(value=ast.Name(id=args.vararg.arg, ctx=ast.Load()), ctx=ast.Load()))
    if args.kwonlyargs:
        for arg in args.kwonlyargs:
            keywords.append(ast.keyword(arg=arg.arg, value=ast.Name(id=arg.arg, ctx=ast.Load())))
    if args.kwarg:
        keywords.append(ast.keyword(arg=None, value=ast.Name(id=args.kwarg.arg, ctx=ast.Load())))
    return positional, keywords


def _parse(source: str) -> ast.AST:
    try:
        return ast.parse(textwrap.dedent(source))
    except SyntaxError as exc:
        raise TransformError(f"candidate is not parseable Python: {exc}") from exc


def _unparse(tree: ast.AST) -> str:
    try:
        return ast.unparse(tree) + "\n"
    except Exception as exc:  # noqa: BLE001
        raise TransformError(f"failed to render transformed Python: {exc}") from exc


TRANSFORMS: dict[str, TransformFn] = {
    "replace_file": transform_replace_file,
    "rename_identifiers": transform_rename_identifiers,
    "insert_comments": transform_insert_comments,
    "normalize_whitespace": transform_normalize_whitespace,
    "rewrite_comparisons": transform_rewrite_comparisons,
    "expand_return": transform_expand_return,
    "quote_style": transform_quote_style,
    "delete_matching": transform_delete_matching,
    "replace_literal": transform_replace_literal,
    "flip_operator": transform_flip_operator,
    "ast_flip_comparison": transform_ast_flip_comparison,
    "ast_rewrite_comparison": transform_ast_rewrite_comparison,
    "ast_replace_constant": transform_ast_replace_constant,
    "constant_return": transform_constant_return,
    "prepend_text": transform_prepend_text,
    "wrap_function": transform_wrap_function,
}
