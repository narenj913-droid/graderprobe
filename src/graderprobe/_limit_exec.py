"""POSIX resource-limit trampoline used instead of subprocess preexec_fn."""
from __future__ import annotations

import os
import resource
import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        separator = args.index("--")
    except ValueError:
        print("graderprobe._limit_exec: missing -- separator", file=sys.stderr)
        return 64
    opts = args[:separator]
    command = args[separator + 1 :]
    if not command:
        print("graderprobe._limit_exec: missing command", file=sys.stderr)
        return 64

    cpu = 0.0
    address_space = 0
    i = 0
    while i < len(opts):
        if opts[i] == "--cpu" and i + 1 < len(opts):
            cpu = float(opts[i + 1]); i += 2; continue
        if opts[i] == "--address-space" and i + 1 < len(opts):
            address_space = int(opts[i + 1]); i += 2; continue
        print(f"graderprobe._limit_exec: unknown option {opts[i]}", file=sys.stderr)
        return 64

    if cpu > 0:
        seconds = max(1, int(cpu))
        resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))
    if address_space > 0:
        resource.setrlimit(resource.RLIMIT_AS, (address_space, address_space))
    os.execvp(command[0], command)
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
