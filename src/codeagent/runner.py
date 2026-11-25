"""Process runner with timeout, tree-kill, and output capping.

Provides :func:`run_with_timeout` which starts a subprocess, streams its
stdout/stderr into memory up to *max_bytes*, and forcibly terminates the
entire process tree if the timeout fires.

Platform notes
--------------
* **POSIX** (Linux, macOS – including the CI runners): uses
  ``start_new_session=True`` so the child gets its own session/process-group,
  then ``os.killpg`` with ``SIGTERM`` → grace → ``SIGKILL``.
* **Windows**: uses ``CREATE_NEW_PROCESS_GROUP`` and
  ``taskkill /F /T /PID <pid>`` for tree-kill (no POSIX signals).
"""

from __future__ import annotations

import contextlib
import os
import platform
import signal
import subprocess
import threading
import time
from collections.abc import Sequence

from pydantic import BaseModel, Field

__all__ = ["RunResult", "run_with_timeout"]

_IS_WINDOWS = platform.system() == "Windows"

# Grace period (seconds) between SIGTERM and SIGKILL on POSIX.
_SIGTERM_GRACE = 2.0


class RunResult(BaseModel):
    """Result of a :func:`run_with_timeout` call."""

    returncode: int = Field(..., description="Process exit code (or -1 if kill failed).")
    stdout: bytes = Field(default=b"", description="Captured standard output (possibly truncated).")
    stderr: bytes = Field(default=b"", description="Captured standard error (possibly truncated).")
    duration_s: float = Field(..., description="Wall-clock seconds from spawn to completion.")
    truncated: bool = Field(
        default=False,
        description="True when combined stdout+stderr reached *max_bytes* and was cut off.",
    )
    killed: bool = Field(
        default=False,
        description="True when the process was terminated due to timeout.",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _kill_tree_posix(pid: int, sig: int) -> None:  # pragma: no cover – OS-dependent
    """Send *sig* to the process group that *pid* leads."""
    with contextlib.suppress(ProcessLookupError):
        pgid = os.getpgid(pid)  # type: ignore[attr-defined]
        os.killpg(pgid, sig)  # type: ignore[attr-defined]


def _kill_tree_windows(pid: int) -> None:  # pragma: no cover – OS-dependent
    """Kill *pid* and all its descendants using ``taskkill``."""
    try:
        subprocess.run(  # noqa: S603
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
        )
    except FileNotFoundError:
        # taskkill not found – fall back to plain terminate
        with contextlib.suppress(ProcessLookupError):
            os.kill(pid, signal.SIGTERM)


def _make_popen_kwargs(cwd: str | None, env: dict[str, str] | None) -> dict[str, object]:
    """Return ``Popen`` kwargs appropriate for the current platform."""
    kwargs: dict[str, object] = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "cwd": cwd,
        "env": env,
    }
    if _IS_WINDOWS:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    return kwargs


def _reader_thread(
    stream: object,
    buf: list[bytes],
    byte_counter: list[int],
    lock: threading.Lock,
    max_bytes: int,
    truncated_flag: list[bool],
) -> None:
    """Read *stream* in chunks, appending to *buf* until *max_bytes* reached.

    After the byte cap is hit the stream is **drained** (data discarded) so the
    subprocess is not blocked waiting for the pipe buffer to be consumed.
    """
    chunk_size = 4096
    while True:
        try:
            chunk = stream.read(chunk_size)  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            break
        if not chunk:
            break
        with lock:
            remaining = max_bytes - byte_counter[0]
            if remaining <= 0:
                # Byte cap already hit – drain without buffering
                truncated_flag[0] = True
                continue
            if len(chunk) > remaining:
                chunk = chunk[:remaining]
                truncated_flag[0] = True
            buf.append(chunk)
            byte_counter[0] += len(chunk)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_with_timeout(
    cmd: Sequence[str] | str,
    *,
    timeout_s: float = 30.0,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MiB
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> RunResult:
    """Run *cmd* with a hard timeout and byte cap on its output.

    Parameters
    ----------
    cmd:
        Command and arguments (list) or a shell string.
    timeout_s:
        Maximum wall-clock seconds to wait before killing the process tree.
    max_bytes:
        Combined stdout+stderr byte cap.  When reached the streams are closed
        and the process may continue until it exits or times out, but no more
        output is captured.
    cwd:
        Working directory for the subprocess.
    env:
        Environment variables mapping (``None`` = inherit).

    Returns
    -------
    RunResult
        Contains ``returncode``, ``stdout``, ``stderr``, ``duration_s``,
        ``truncated``, and ``killed``.
    """
    shell = isinstance(cmd, str)
    popen_kwargs = _make_popen_kwargs(cwd, env)
    if shell:
        popen_kwargs["shell"] = True

    start = time.monotonic()
    proc = subprocess.Popen(cmd, **popen_kwargs)  # type: ignore[call-overload]  # noqa: S603

    # Shared state between reader threads
    lock = threading.Lock()
    byte_counter: list[int] = [0]
    truncated_flag: list[bool] = [False]
    stdout_buf: list[bytes] = []
    stderr_buf: list[bytes] = []

    t_out = threading.Thread(
        target=_reader_thread,
        args=(proc.stdout, stdout_buf, byte_counter, lock, max_bytes, truncated_flag),
        daemon=True,
    )
    t_err = threading.Thread(
        target=_reader_thread,
        args=(proc.stderr, stderr_buf, byte_counter, lock, max_bytes, truncated_flag),
        daemon=True,
    )
    t_out.start()
    t_err.start()

    killed = False
    try:
        proc.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        killed = True
        pid = proc.pid
        if _IS_WINDOWS:
            _kill_tree_windows(pid)
        else:
            # SIGTERM first, then SIGKILL after grace period
            _kill_tree_posix(pid, signal.SIGTERM)
            try:
                proc.wait(timeout=_SIGTERM_GRACE)
            except subprocess.TimeoutExpired:
                _kill_tree_posix(pid, signal.SIGKILL)  # type: ignore[attr-defined]
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=5.0)

    # Close the pipes so reader threads unblock and finish
    with contextlib.suppress(Exception):  # noqa: BLE001
        proc.stdout.close()
    with contextlib.suppress(Exception):  # noqa: BLE001
        proc.stderr.close()
    t_out.join(timeout=5.0)
    t_err.join(timeout=5.0)

    duration_s = time.monotonic() - start
    return RunResult(
        returncode=proc.returncode if proc.returncode is not None else -1,
        stdout=b"".join(stdout_buf),
        stderr=b"".join(stderr_buf),
        duration_s=duration_s,
        truncated=truncated_flag[0],
        killed=killed,
    )
