"""Tests for :mod:`codeagent.runner`."""

from __future__ import annotations

import platform
import sys
import textwrap

import pytest

from codeagent.runner import RunResult, run_with_timeout

_IS_WINDOWS = platform.system() == "Windows"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _python() -> str:
    """Return the path to the current Python interpreter."""
    return sys.executable


# ---------------------------------------------------------------------------
# Basic success path
# ---------------------------------------------------------------------------


def test_simple_command_success():
    """A trivially-fast command should succeed with returncode 0."""
    result = run_with_timeout(
        [_python(), "-c", "print('hello')"],
        timeout_s=10.0,
    )
    assert isinstance(result, RunResult)
    assert result.returncode == 0
    assert b"hello" in result.stdout
    assert not result.killed
    assert not result.truncated
    assert result.duration_s >= 0


def test_exit_code_nonzero():
    """Non-zero exit codes must be propagated correctly."""
    result = run_with_timeout(
        [_python(), "-c", "import sys; sys.exit(42)"],
        timeout_s=10.0,
    )
    assert result.returncode == 42
    assert not result.killed


# ---------------------------------------------------------------------------
# Timeout / kill
# ---------------------------------------------------------------------------


def test_timeout_kills_process():
    """A process that sleeps longer than the timeout must be killed."""
    result = run_with_timeout(
        [_python(), "-c", "import time; time.sleep(60)"],
        timeout_s=0.5,
    )
    assert result.killed
    assert result.duration_s < 10.0  # generous upper bound


# ---------------------------------------------------------------------------
# Output cap / truncation
# ---------------------------------------------------------------------------


def test_output_cap_truncated():
    """Writing more than max_bytes must set truncated=True quickly."""
    # Produce ~2 MiB of output; cap at 512 KiB.
    script = textwrap.dedent(
        """
        import sys
        chunk = b"x" * 65536  # 64 KiB
        for _ in range(32):   # 2 MiB total
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
        """
    )
    result = run_with_timeout(
        [_python(), "-c", script],
        timeout_s=15.0,
        max_bytes=512 * 1024,
    )
    assert result.truncated
    assert len(result.stdout) + len(result.stderr) <= 512 * 1024
    # Should finish well within the timeout
    assert result.duration_s < 12.0


# ---------------------------------------------------------------------------
# Child process tree killed (POSIX-only)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(_IS_WINDOWS, reason="Process-group kill is POSIX-only")
def test_children_killed():
    """After timeout, the entire subprocess tree must be dead."""
    psutil = pytest.importorskip("psutil")

    # Script that spawns 5 long-sleeping children
    child_script = textwrap.dedent(
        """
        import subprocess, sys, time

        procs = []
        for _ in range(5):
            p = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(60)"]
            )
            procs.append(p)

        # Print all child PIDs so the test can check them
        for p in procs:
            print(p.pid, flush=True)

        time.sleep(60)
        """
    )

    result = run_with_timeout(
        [_python(), "-c", child_script],
        timeout_s=1.0,
    )
    assert result.killed

    # Give the OS a moment to reap processes
    import time

    time.sleep(0.5)

    # None of the PIDs printed by the child should still be running
    reported_pids: list[int] = []
    for line in result.stdout.decode(errors="replace").splitlines():
        line = line.strip()
        if line.isdigit():
            reported_pids.append(int(line))

    for pid in reported_pids:
        assert not psutil.pid_exists(pid), f"Child PID {pid} is still alive after tree-kill"


# ---------------------------------------------------------------------------
# stderr capture
# ---------------------------------------------------------------------------


def test_stderr_captured():
    """stderr output should be captured in result.stderr."""
    script = "import sys; sys.stderr.write('error_output\\n')"
    result = run_with_timeout([_python(), "-c", script], timeout_s=10.0)
    assert b"error_output" in result.stderr
    assert result.returncode == 0
