from pathlib import Path

def read_sandbox(root, relative):
    root_abs = Path(root).resolve()
    target = (Path(root) / relative).resolve()
    try:
        target.relative_to(root_abs)
    except ValueError as exc:
        raise PermissionError("escape") from exc
    return target.read_text(encoding="utf-8")
