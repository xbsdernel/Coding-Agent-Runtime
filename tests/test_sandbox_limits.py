"""Tests for :mod:`codeagent.schemas.SandboxLimits` and its integration with ExperimentConfig."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from codeagent.schemas import ExperimentConfig, SandboxLimits

# ---------------------------------------------------------------------------
# SandboxLimits defaults
# ---------------------------------------------------------------------------


def test_sandbox_limits_defaults():
    limits = SandboxLimits()
    assert limits.memory_limit_mb == 256
    assert limits.cpu_quota_us == 50_000
    assert limits.pids_limit == 64
    assert limits.network_disabled is True
    assert limits.no_new_privileges is True
    assert limits.schema_version == 1


def test_sandbox_limits_custom():
    limits = SandboxLimits(
        memory_limit_mb=512,
        cpu_quota_us=100_000,
        pids_limit=128,
        network_disabled=False,
        no_new_privileges=False,
    )
    assert limits.memory_limit_mb == 512
    assert limits.cpu_quota_us == 100_000
    assert limits.pids_limit == 128
    assert limits.network_disabled is False
    assert limits.no_new_privileges is False


# ---------------------------------------------------------------------------
# SandboxLimits validation
# ---------------------------------------------------------------------------


def test_sandbox_limits_memory_too_low():
    with pytest.raises(ValidationError):
        SandboxLimits(memory_limit_mb=8)  # below ge=16


def test_sandbox_limits_cpu_quota_too_low():
    with pytest.raises(ValidationError):
        SandboxLimits(cpu_quota_us=0)  # below ge=1_000


def test_sandbox_limits_pids_too_low():
    with pytest.raises(ValidationError):
        SandboxLimits(pids_limit=0)  # below ge=1


def test_sandbox_limits_extra_field_rejected():
    with pytest.raises(ValidationError):
        SandboxLimits(**{"memory_limit_mb": 256, "unknown_field": 999})  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# ExperimentConfig integration
# ---------------------------------------------------------------------------


def test_experiment_config_has_sandbox_limits():
    cfg = ExperimentConfig(experiment_id="test", model_name="gpt-4o")
    assert isinstance(cfg.sandbox_limits, SandboxLimits)
    # Default values match SandboxLimits defaults
    assert cfg.sandbox_limits.memory_limit_mb == 256
    assert cfg.sandbox_limits.pids_limit == 64


def test_experiment_config_custom_sandbox_limits():
    limits = SandboxLimits(memory_limit_mb=512, pids_limit=32)
    cfg = ExperimentConfig(
        experiment_id="big-task",
        model_name="gpt-4o",
        sandbox_limits=limits,
    )
    assert cfg.sandbox_limits.memory_limit_mb == 512
    assert cfg.sandbox_limits.pids_limit == 32


def test_sandbox_limits_included_in_config_hash():
    """Different sandbox_limits must produce different config hashes."""
    cfg_a = ExperimentConfig(
        experiment_id="x",
        model_name="m",
        sandbox_limits=SandboxLimits(memory_limit_mb=256),
    )
    cfg_b = ExperimentConfig(
        experiment_id="x",
        model_name="m",
        sandbox_limits=SandboxLimits(memory_limit_mb=512),
    )
    assert cfg_a.compute_hash() != cfg_b.compute_hash()


def test_sandbox_limits_round_trip():
    """SandboxLimits must survive JSON round-trip through ExperimentConfig."""
    limits = SandboxLimits(memory_limit_mb=128, cpu_quota_us=25_000, pids_limit=16)
    cfg = ExperimentConfig(experiment_id="rt", model_name="m", sandbox_limits=limits)
    raw = cfg.model_dump_json()
    cfg2 = ExperimentConfig.model_validate_json(raw)
    assert cfg2.sandbox_limits.memory_limit_mb == 128
    assert cfg2.sandbox_limits.cpu_quota_us == 25_000
    assert cfg2.sandbox_limits.pids_limit == 16


# ---------------------------------------------------------------------------
# docs/sandbox_limits.md existence
# ---------------------------------------------------------------------------


def test_sandbox_limits_doc_exists():
    import pathlib

    doc = pathlib.Path(__file__).parent.parent / "docs" / "sandbox_limits.md"
    assert doc.is_file(), "docs/sandbox_limits.md must be committed"
    content = doc.read_text(encoding="utf-8")
    assert "memory_limit_mb" in content
    assert "cpu_quota" in content
    assert "pids_limit" in content
    assert "network_disabled" in content
    assert "no_new_privileges" in content
