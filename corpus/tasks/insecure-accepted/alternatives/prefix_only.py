import os

def read_sandbox(root, relative):
    if relative.startswith("../"):
        raise PermissionError("escape")
    target = os.path.join(root, relative)
    with open(target, encoding="utf-8") as handle:
        return handle.read()
