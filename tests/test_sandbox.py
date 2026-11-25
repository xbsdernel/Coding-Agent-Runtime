"""Tests for :mod:`codeagent.sandbox` (runs in offline/simulation mode)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from codeagent.sandbox import (
    ContainerExecResult,
    ContainerMetrics,
    DockerSandbox,
    SandboxConfig,
    is_docker_available,
)

# ---------------------------------------------------------------------------
# Config model tests
# ---------------------------------------------------------------------------


def test_sandbox_config_defaults():
    cfg = SandboxConfig()
    assert cfg.image == "python:3.12-slim"
    assert cfg.memory_limit_mb == 256
    assert cfg.network_disabled is True
    assert cfg.user == "nobody"
    assert cfg.no_new_privileges is True


def test_sandbox_config_validation():
    with pytest.raises(ValidationError):
        SandboxConfig(memory_limit_mb=1)  # below minimum of 16
    with pytest.raises(ValidationError):
        SandboxConfig(cpu_quota=0)  # below minimum of 1_000
    with pytest.raises(ValidationError):
        SandboxConfig(pids_limit=0)  # below minimum of 1


def test_sandbox_config_custom():
    cfg = SandboxConfig(
        image="ubuntu:22.04",
        memory_limit_mb=512,
        cpu_quota=25_000,
        pids_limit=32,
        network_disabled=False,
        user="agent",
    )
    assert cfg.image == "ubuntu:22.04"
    assert cfg.memory_limit_mb == 512
    assert cfg.cpu_quota == 25_000
    assert cfg.pids_limit == 32
    assert cfg.network_disabled is False
    assert cfg.user == "agent"


# ---------------------------------------------------------------------------
# is_docker_available
# ---------------------------------------------------------------------------


def test_is_docker_available_returns_bool():
    result = is_docker_available()
    assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# DockerSandbox in offline mode
# ---------------------------------------------------------------------------


@pytest.fixture()
def offline_sandbox() -> DockerSandbox:
    return DockerSandbox(SandboxConfig(), offline=True)


def test_offline_start_records_time(offline_sandbox: DockerSandbox):
    offline_sandbox.start()
    assert offline_sandbox.metrics.start_time_s >= 0.0


def test_offline_exec_returns_result(offline_sandbox: DockerSandbox):
    offline_sandbox.start()
    result = offline_sandbox.exec(["echo", "hello"])
    assert isinstance(result, ContainerExecResult)
    assert result.exit_code == 0
    assert b"simulated" in result.stdout
    assert result.duration_s >= 0.0


def test_offline_exec_records_metric(offline_sandbox: DockerSandbox):
    offline_sandbox.start()
    offline_sandbox.exec(["ls", "-la"])
    assert offline_sandbox.metrics.exec_time_s >= 0.0


def test_offline_reset_fresh_records_metric(offline_sandbox: DockerSandbox):
    offline_sandbox.start()
    offline_sandbox.reset_fresh()
    assert offline_sandbox.metrics.reset_fresh_time_s >= 0.0


def test_offline_reset_snapshot_records_metric(offline_sandbox: DockerSandbox):
    offline_sandbox.start()
    offline_sandbox.reset_snapshot()
    assert offline_sandbox.metrics.reset_snapshot_time_s >= 0.0
    assert offline_sandbox._snapshot_image is not None


def test_offline_stop_is_noop(offline_sandbox: DockerSandbox):
    """stop() in offline mode must not raise."""
    offline_sandbox.start()
    offline_sandbox.stop()  # should not raise


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


def test_context_manager_offline():
    cfg = SandboxConfig()
    with DockerSandbox(cfg, offline=True) as sb:
        result = sb.exec(["python", "-c", "print('ok')"])
        assert result.exit_code == 0
    # After __exit__ metrics should still be accessible
    assert sb.metrics.start_time_s >= 0.0


# ---------------------------------------------------------------------------
# Metrics model
# ---------------------------------------------------------------------------


def test_container_metrics_defaults():
    m = ContainerMetrics()
    assert m.start_time_s == 0.0
    assert m.exec_time_s == 0.0
    assert m.reset_fresh_time_s == 0.0
    assert m.reset_snapshot_time_s == 0.0
