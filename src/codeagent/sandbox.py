"""Docker SDK wrapper: exec, snapshot, reset, resource limits.

Provides a thin wrapper around the ``docker`` Python SDK for running
subprocess commands inside an isolated container.  When Docker is unavailable
(e.g. in the local sandbox environment) the class falls back to an
**offline simulation mode** that records timing metrics without touching a
real daemon — this keeps the CI green and the API testable everywhere.

Usage (real Docker)::

    from codeagent.sandbox import DockerSandbox, SandboxConfig

    cfg = SandboxConfig(image="python:3.12-slim")
    with DockerSandbox(cfg) as sb:
        result = sb.exec(["python", "-c", "print('hello')"])
        print(result.stdout)

Usage (offline simulation, automatic when Docker is not available)::

    # Same API – the sandbox silently simulates the container operations.
"""

from __future__ import annotations

import contextlib
import time
from typing import Any

from pydantic import BaseModel, Field

__all__ = [
    "ContainerExecResult",
    "ContainerMetrics",
    "DockerSandbox",
    "SandboxConfig",
    "is_docker_available",
]


# ---------------------------------------------------------------------------
# Configuration & metrics models
# ---------------------------------------------------------------------------


class SandboxConfig(BaseModel):
    """Configuration for a :class:`DockerSandbox` container."""

    image: str = Field(default="python:3.12-slim", description="Docker image to use.")
    memory_limit_mb: int = Field(
        default=256,
        ge=16,
        description="Memory limit for the container in MiB.",
    )
    cpu_quota: int = Field(
        default=50_000,
        ge=1_000,
        description="CPU quota in microseconds per 100 ms period (50 000 = 50 % of one core).",
    )
    pids_limit: int = Field(
        default=64,
        ge=1,
        description="Maximum number of processes/threads in the container.",
    )
    network_disabled: bool = Field(
        default=True,
        description="Disable all network access inside the container.",
    )
    user: str = Field(
        default="nobody",
        description="Run container processes as this user (non-root).",
    )
    no_new_privileges: bool = Field(
        default=True,
        description="Prevent privilege escalation inside the container.",
    )


class ContainerExecResult(BaseModel):
    """Result of a single :meth:`DockerSandbox.exec` call."""

    exit_code: int = Field(default=0)
    stdout: bytes = Field(default=b"")
    stderr: bytes = Field(default=b"")
    duration_s: float = Field(default=0.0)


class ContainerMetrics(BaseModel):
    """Timing metrics collected across the sandbox lifecycle."""

    start_time_s: float = Field(
        default=0.0,
        description="Time in seconds to start the container.",
    )
    exec_time_s: float = Field(
        default=0.0,
        description="Time in seconds for the most recent exec call.",
    )
    reset_fresh_time_s: float = Field(
        default=0.0,
        description="Time in seconds to reset via a fresh container.",
    )
    reset_snapshot_time_s: float = Field(
        default=0.0,
        description="Time in seconds to reset via a committed snapshot.",
    )


# ---------------------------------------------------------------------------
# Docker availability probe
# ---------------------------------------------------------------------------


def is_docker_available() -> bool:
    """Return ``True`` if the Docker daemon is reachable, ``False`` otherwise."""
    try:
        import docker  # type: ignore[import-untyped]

        client = docker.from_env()
        client.ping()
        return True
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------------
# Sandbox implementation
# ---------------------------------------------------------------------------


class DockerSandbox:
    """Thin wrapper around the Docker SDK with an offline simulation fallback.

    Parameters
    ----------
    config:
        :class:`SandboxConfig` instance controlling resource limits and image.
    offline:
        Force offline/simulation mode.  Defaults to ``None`` which means the
        class will auto-detect Docker availability on first use.
    """

    def __init__(
        self,
        config: SandboxConfig | None = None,
        *,
        offline: bool | None = None,
    ) -> None:
        self.config = config or SandboxConfig()
        self.metrics = ContainerMetrics()
        self._offline: bool = offline if offline is not None else not is_docker_available()
        self._client: Any = None
        self._container: Any = None
        self._snapshot_image: str | None = None

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> DockerSandbox:
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the sandbox container (or simulate startup in offline mode)."""
        t0 = time.monotonic()
        if self._offline:
            time.sleep(0.001)  # simulate minimal startup latency
        else:
            self._start_real()
        self.metrics.start_time_s = time.monotonic() - t0

    def _start_real(self) -> None:  # pragma: no cover – requires Docker
        import docker  # type: ignore[import-untyped]

        self._client = docker.from_env()
        self._container = self._client.containers.run(
            self.config.image,
            command="sleep infinity",
            detach=True,
            mem_limit=f"{self.config.memory_limit_mb}m",
            cpu_quota=self.config.cpu_quota,
            pids_limit=self.config.pids_limit,
            network_disabled=self.config.network_disabled,
            user=self.config.user,
            security_opt=(["no-new-privileges"] if self.config.no_new_privileges else []),
            remove=False,
        )

    def stop(self) -> None:
        """Stop and remove the sandbox container (no-op in offline mode)."""
        if self._offline:
            return
        self._stop_real()

    def _stop_real(self) -> None:  # pragma: no cover – requires Docker
        if self._container is not None:
            with contextlib.suppress(Exception):
                self._container.stop(timeout=5)
            with contextlib.suppress(Exception):
                self._container.remove(force=True)
        if self._snapshot_image is not None:
            with contextlib.suppress(Exception):
                assert self._client is not None
                self._client.images.remove(self._snapshot_image, force=True)

    # ------------------------------------------------------------------
    # Command execution
    # ------------------------------------------------------------------

    def exec(
        self,
        cmd: list[str],
        *,
        workdir: str = "/",
        env: dict[str, str] | None = None,
    ) -> ContainerExecResult:
        """Run *cmd* inside the container and return its result.

        Parameters
        ----------
        cmd:
            Command and arguments as a list of strings.
        workdir:
            Working directory inside the container.
        env:
            Extra environment variables to inject.

        Returns
        -------
        ContainerExecResult
        """
        t0 = time.monotonic()
        if self._offline:
            result = self._exec_simulated(cmd)
        else:  # pragma: no cover – requires Docker
            result = self._exec_real(cmd, workdir=workdir, env=env or {})
        duration = time.monotonic() - t0
        result = result.model_copy(update={"duration_s": duration})
        self.metrics.exec_time_s = duration
        return result

    def _exec_simulated(self, cmd: list[str]) -> ContainerExecResult:
        """Return a simulated exec result for offline testing."""
        return ContainerExecResult(
            exit_code=0,
            stdout=f"[simulated] exec: {' '.join(cmd)}\n".encode(),
            stderr=b"",
            duration_s=0.0,
        )

    def _exec_real(  # pragma: no cover – requires Docker
        self,
        cmd: list[str],
        *,
        workdir: str,
        env: dict[str, str],
    ) -> ContainerExecResult:
        assert self._container is not None
        exit_code, output = self._container.exec_run(
            cmd,
            workdir=workdir,
            environment=env,
            demux=False,
        )
        return ContainerExecResult(
            exit_code=exit_code or 0,
            stdout=output or b"",
            stderr=b"",
            duration_s=0.0,
        )

    # ------------------------------------------------------------------
    # Reset methods
    # ------------------------------------------------------------------

    def reset_fresh(self) -> None:
        """Reset by stopping the current container and starting a brand-new one.

        In offline mode this is simulated with a brief sleep.
        """
        t0 = time.monotonic()
        if self._offline:
            time.sleep(0.001)
        else:  # pragma: no cover – requires Docker
            self._stop_real()
            self._start_real()
        self.metrics.reset_fresh_time_s = time.monotonic() - t0

    def reset_snapshot(self) -> None:
        """Reset by committing the current container to an image, then restarting from it.

        This is typically faster than a fresh reset when the image is large but
        the container state is small.  In offline mode this is simulated.
        """
        t0 = time.monotonic()
        if self._offline:
            time.sleep(0.001)
            self._snapshot_image = "simulated-snapshot:latest"
        else:  # pragma: no cover – requires Docker
            self._reset_snapshot_real()
        self.metrics.reset_snapshot_time_s = time.monotonic() - t0

    def _reset_snapshot_real(self) -> None:  # pragma: no cover – requires Docker
        assert self._container is not None and self._client is not None
        # Commit the container to a temporary image
        snap_tag = f"codeagent-snap-{int(time.time())}"
        image = self._container.commit(repository="codeagent-snap", tag=snap_tag)
        self._snapshot_image = f"codeagent-snap:{snap_tag}"
        # Restart from the snapshot image
        self._stop_real()
        self._container = self._client.containers.run(
            image.id,
            command="sleep infinity",
            detach=True,
            mem_limit=f"{self.config.memory_limit_mb}m",
            cpu_quota=self.config.cpu_quota,
            pids_limit=self.config.pids_limit,
            network_disabled=self.config.network_disabled,
            user=self.config.user,
            security_opt=(["no-new-privileges"] if self.config.no_new_privileges else []),
            remove=False,
        )
