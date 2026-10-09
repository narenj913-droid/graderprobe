import os

def read_sandbox(root, relative):
    root_abs = os.path.abspath(root)
    target = os.path.abspath(os.path.join(root, relative))
    if os.path.commonpath([root_abs, target]) != root_abs:
        raise PermissionError("escape")
    with open(target, encoding="utf-8") as handle:
        return handle.read()
