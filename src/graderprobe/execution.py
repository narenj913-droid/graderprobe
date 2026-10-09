"""Differential execution of evaluators.

Infrastructure failures are never silently converted into FAIL. The default
backend is a local subprocess. Optional Docker execution provides a stronger,
documented isolation mode when Docker is available.
"""

from __future__ import annotations

import os
import shutil
import contextlib
import hashlib
import signal
import subprocess
import sys
import threading
import time
import tempfile
from pathlib import Path
from typing import Callable, Iterator

from graderprobe.isolation import IsolatedWorkspace, default_child_env, resolve_within
from graderprobe.types import EvaluatorSpec, ExecutionResult, Verdict

VERDICT_MARKERS = {
    "GRADERPROBE_VERDICT: PASS": Verdict.PASS,
    "GRADERPROBE_VERDICT: FAIL": Verdict.FAIL,
    "GRADERPROBE_VERDICT: INCONCLUSIVE": Verdict.INCONCLUSIVE,
    "GRADERPROBE_VERDICT: ERROR": Verdict.ERROR,
}
CPU_TIME_SLACK = 1.0
_DEFAULT_EXECUTION_SLOTS = 4
_execution_slots_lock = threading.Lock()
_execution_slots = threading.BoundedSemaphore(_DEFAULT_EXECUTION_SLOTS)
_execution_slots_capacity = _DEFAULT_EXECUTION_SLOTS


def set_execution_slots(slots: int) -> int:
    """Set the process-wide evaluator concurrency budget before a run."""
    global _execution_slots, _execution_slots_capacity
    slots = max(1, int(slots))
    with _execution_slots_lock:
        # This is intended to be called before worker threads start. Replacing the
        # semaphore is deterministic and avoids unsafe dynamic resizing.
        _execution_slots = threading.BoundedSemaphore(slots)
        _execution_slots_capacity = slots
    return slots


def execution_slots() -> int:
    return _execution_slots_capacity


@contextlib.contextmanager
def execution_slot() -> Iterator[None]:
    """Cap total subprocess concurrency across nested task/probe workers."""
    _execution_slots.acquire()
    try:
        yield
    finally:
        _execution_slots.release()


def run_evaluator(
    workspace: IsolatedWorkspace,
    spec: EvaluatorSpec,
    *,
    attempt: int = 1,
    extra_env: dict[str, str] | None = None,
    inherit_secrets: bool = False,
    cpu_limit_seconds: float | None = None,
    address_space_bytes: int | None = None,
) -> ExecutionResult:
    work = resolve_within(workspace.path, spec.working_dir, allow_missing=True)
    work.mkdir(parents=True, exist_ok=True)
    if not work.is_dir():
        raise NotADirectoryError(f"evaluator working_dir is not a directory: {spec.working_dir}")

    timeout = max(0.1, float(spec.timeout_seconds))
    if spec.backend == "docker":
        return _run_docker(
            workspace, work, spec, attempt=attempt, extra_env=extra_env,
            inherit_secrets=inherit_secrets, timeout=timeout
        )
    if spec.backend != "process":
        return _error_result(workspace, spec, attempt, f"unsupported execution backend: {spec.backend}")

    env = default_child_env(spec.environment, inherit_secrets=inherit_secrets)
    env["GRADERPROBE_ATTEMPT"] = str(attempt)
    env["GRADERPROBE_WORKSPACE"] = str(workspace.path)
    if extra_env:
        env.update(extra_env)

    cpu_limit = timeout + CPU_TIME_SLACK if cpu_limit_seconds is None else cpu_limit_seconds
    started = time.perf_counter()
    timed_out = False
    error_message = ""
    exit_code: int | None = None
    stdout = ""
    stderr = ""

    if spec.network == "blocked":
        return _error_result(
            workspace, spec, attempt,
            "network policy 'blocked' requested, but the local process backend has no network sandbox; use sandbox.backend='docker'"
        )

    command = list(spec.command)
    if os.name == "posix" and (cpu_limit_seconds is not None or address_space_bytes is not None):
        command = [
            sys.executable, str(Path(__file__).resolve().with_name("_limit_exec.py")),
            "--cpu", str(cpu_limit),
            "--address-space", str(address_space_bytes or 0),
            "--", *command,
        ]

    process: subprocess.Popen[bytes] | None = None
    with execution_slot(), tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        popen_kwargs: dict[str, object] = {
            "cwd": str(work),
            "env": env,
            "stdout": stdout_file,
            "stderr": stderr_file,
        }
        if os.name == "posix":
            popen_kwargs["start_new_session"] = True
        try:
            process = subprocess.Popen(command, **popen_kwargs)  # type: ignore[arg-type]
            completed = _poll_process_until(process, timeout)
            if not completed:
                timed_out = True
                error_message = f"timeout after {timeout}s"
                _terminate_process_tree(process)
                if not _poll_process_until(process, 2.0):
                    _terminate_process_tree(process, force=True)
                    if not _poll_process_until(process, 1.0):
                        error_message = f"timeout after {timeout}s; process tree did not terminate"
            exit_code = process.returncode
        except OSError as exc:
            error_message = f"os error: {exc}"
        except Exception as exc:  # noqa: BLE001
            error_message = f"harness error: {type(exc).__name__}: {exc}"
            stderr = str(exc)
        finally:
            if process is not None and process.poll() is None:
                _terminate_process_tree(process, force=True)
                _poll_process_until(process, 1.0)
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = stdout_file.read().decode("utf-8", errors="replace")
            stderr_text = stderr_file.read().decode("utf-8", errors="replace")
            if stderr_text:
                stderr = stderr_text if not stderr else (stderr + "\n" + stderr_text)
    duration_ms = (time.perf_counter() - started) * 1000.0
    verdict = interpret_verdict(spec, exit_code=exit_code, stdout=stdout, stderr=stderr, timed_out=timed_out, error_message=error_message)
    result = ExecutionResult(
        verdict=verdict, exit_code=exit_code, stdout=stdout, stderr=stderr,
        duration_ms=duration_ms, timed_out=timed_out, workspace=str(workspace.path),
        command=list(spec.command), environment={"GRADERPROBE_ATTEMPT": str(attempt)},
        error_message=error_message, attempt=attempt,
    )
    return _enrich_execution_result(result, spec)


def _run_docker(
    workspace: IsolatedWorkspace, work: Path, spec: EvaluatorSpec, *,
    attempt: int, extra_env: dict[str, str] | None, inherit_secrets: bool, timeout: float
) -> ExecutionResult:
    if shutil.which("docker") is None:
        return _error_result(workspace, spec, attempt, "docker executable not found")
    if not spec.container_image:
        return _error_result(workspace, spec, attempt, "docker backend requires a container image")
    if spec.network == "blocked" and spec.container_network != "none":
        return _error_result(workspace, spec, attempt, "blocked evaluator network requires sandbox.network='none'")

    work_rel = work.relative_to(workspace.path).as_posix() or "."
    container_work = "/workspace" if work_rel == "." else f"/workspace/{work_rel}"
    tmp_dir = workspace.path / ".graderprobe-tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    env = _docker_env(spec, attempt=attempt, workspace=workspace.path, extra_env=extra_env, inherit_secrets=inherit_secrets)
    command = build_docker_command(
        spec, workspace_path=workspace.path, container_workdir=container_work,
        env=env, command=spec.command
    )
    started = time.perf_counter()
    timed_out = False
    error_message = ""
    stdout = stderr = ""
    exit_code: int | None = None
    process: subprocess.Popen[str] | None = None
    with execution_slot():
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                exit_code = process.returncode
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                stdout = _decode(exc.stdout)
                stderr = _decode(exc.stderr)
                error_message = f"timeout after {timeout}s"
                _terminate_process_tree(process)
                more_out, more_err = process.communicate()
                stdout += _decode(more_out)
                stderr += _decode(more_err)
                exit_code = process.returncode
        except OSError as exc:
            error_message = f"docker os error: {exc}"
            stderr = str(exc)
        except Exception as exc:  # noqa: BLE001
            error_message = f"docker harness error: {type(exc).__name__}: {exc}"
            stderr = str(exc)
        finally:
            if process is not None and process.poll() is None:
                _terminate_process_tree(process)

    duration_ms = (time.perf_counter() - started) * 1000.0
    verdict = interpret_verdict(spec, exit_code=exit_code, stdout=stdout, stderr=stderr, timed_out=timed_out, error_message=error_message)
    result = ExecutionResult(
        verdict=verdict, exit_code=exit_code, stdout=stdout, stderr=stderr,
        duration_ms=duration_ms, timed_out=timed_out, workspace=str(workspace.path),
        command=list(spec.command), environment={"GRADERPROBE_ATTEMPT": str(attempt)},
        error_message=error_message, attempt=attempt,
    )
    return _enrich_execution_result(result, spec)


def build_docker_command(
    spec: EvaluatorSpec, *, workspace_path: Path, container_workdir: str,
    env: dict[str, str], command: list[str]
) -> list[str]:
    network = spec.container_network
    if spec.network == "blocked":
        network = "none"
    args = [
        "docker", "run", "--rm", "--init",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--read-only",
        "--pids-limit", "128",
        "--memory", spec.container_memory,
        "--cpus", spec.container_cpus,
        "--network", network,
        "-v", f"{workspace_path.resolve()}:/workspace:rw",
        "-w", container_workdir,
    ]
    for key, value in sorted(env.items()):
        args.extend(["-e", f"{key}={value}"])
    args.append(spec.container_image or "")
    args.extend(command)
    return args


def _docker_env(
    spec: EvaluatorSpec, *, attempt: int, workspace: Path,
    extra_env: dict[str, str] | None, inherit_secrets: bool
) -> dict[str, str]:
    env = {
        "PYTHONHASHSEED": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "GRADERPROBE": "1",
        "GRADERPROBE_ATTEMPT": str(attempt),
        "GRADERPROBE_WORKSPACE": "/workspace",
        "TMPDIR": "/workspace/.graderprobe-tmp",
    }
    env.update(spec.environment)
    if inherit_secrets:
        host = default_child_env({}, inherit_secrets=True)
        env.update(host)
    if extra_env:
        env.update(extra_env)
    return env


def _error_result(workspace: IsolatedWorkspace, spec: EvaluatorSpec, attempt: int, message: str) -> ExecutionResult:
    return ExecutionResult(
        verdict=Verdict.ERROR, exit_code=None, stdout="", stderr=message, duration_ms=0.0,
        timed_out=False, workspace=str(workspace.path), command=list(spec.command),
        environment={"GRADERPROBE_ATTEMPT": str(attempt)}, error_message=message, attempt=attempt
    )


def _poll_process_until(process: subprocess.Popen[object], timeout: float) -> bool:
    """Poll with waitpid(WNOHANG)-backed Popen.poll until the deadline."""
    deadline = time.monotonic() + max(0.0, float(timeout))
    while process.poll() is None:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(0.01, remaining))
    return True


def _terminate_process_tree(process: subprocess.Popen[object], *, force: bool = False) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        sig = signal.SIGKILL if force else signal.SIGTERM
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            return
        except OSError:
            try:
                (process.kill if force else process.terminate)()
            except (OSError, ProcessLookupError):
                return
        if not force:
            _poll_process_until(process, 0.5)
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    try:
                        process.kill()
                    except (OSError, ProcessLookupError):
                        return
                _poll_process_until(process, 1.0)
        else:
            _poll_process_until(process, 1.0)
    else:
        try:
            (process.kill if force else process.terminate)()
        except (OSError, ProcessLookupError):
            return
        _poll_process_until(process, 1.0)


def interpret_verdict(
    spec: EvaluatorSpec, *, exit_code: int | None, stdout: str, stderr: str,
    timed_out: bool, error_message: str
) -> Verdict:
    if timed_out:
        return Verdict.TIMEOUT
    if spec.verdict_protocol == "marker":
        marker_verdict = _parse_marker_verdict(stdout, stderr)
        return marker_verdict if marker_verdict is not None else Verdict.ERROR
    if spec.verdict_protocol != "exit_code":
        return Verdict.ERROR
    if error_message and exit_code is None:
        return Verdict.ERROR
    if exit_code is None:
        return Verdict.ERROR
    if exit_code in spec.pass_exit_codes:
        return Verdict.PASS
    if exit_code in spec.fail_exit_codes:
        return Verdict.FAIL
    if exit_code in spec.inconclusive_exit_codes:
        return Verdict.INCONCLUSIVE
    return Verdict.ERROR


def _parse_marker_verdict(stdout: str, stderr: str) -> Verdict | None:
    found: list[Verdict] = []
    for line in f"{stdout}\n{stderr}".splitlines():
        verdict = VERDICT_MARKERS.get(line.strip())
        if verdict is not None:
            found.append(verdict)
    if not found or len(set(found)) != 1:
        return Verdict.ERROR if found else None
    return found[0]


def _decode(data: bytes | str | None) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    return data.decode("utf-8", errors="replace")



def _execution_contract(spec) -> dict[str, object]:
    return {
        "command": list(spec.command),
        "working_dir": spec.working_dir,
        "timeout_seconds": spec.timeout_seconds,
        "pass_exit_codes": list(spec.pass_exit_codes),
        "fail_exit_codes": list(spec.fail_exit_codes),
        "inconclusive_exit_codes": list(spec.inconclusive_exit_codes),
        "verdict_protocol": spec.verdict_protocol,
        "environment": dict(sorted(spec.environment.items())),
        "network": spec.network,
        "backend": spec.backend,
        "container_image": spec.container_image,
        "container_network": spec.container_network,
        "container_memory": spec.container_memory,
        "container_cpus": spec.container_cpus,
    }


def _enrich_execution_result(result: ExecutionResult, spec) -> ExecutionResult:
    from dataclasses import replace
    import json
    payload = json.dumps(_execution_contract(spec), sort_keys=True, separators=(",", ":"), default=str).encode()
    contract_hash = hashlib.sha256(payload).hexdigest()
    return replace(
        result,
        stdout_sha256=hashlib.sha256(result.stdout.encode("utf-8")).hexdigest(),
        stderr_sha256=hashlib.sha256(result.stderr.encode("utf-8")).hexdigest(),
        execution_contract_sha256=contract_hash,
    )

def snapshot_candidate(workspace: IsolatedWorkspace, relative: str) -> str:
    path = resolve_within(workspace.path, relative, allow_missing=False)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")
