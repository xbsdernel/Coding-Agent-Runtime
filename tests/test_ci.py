"""Tests for CI workflow configuration and test marker discipline."""

from __future__ import annotations

from pathlib import Path


def test_ci_workflow_exists_and_valid():
    """Verify GitHub Actions CI workflow exists and defines expected jobs and steps."""
    root = Path(__file__).resolve().parent.parent
    ci_file = root / ".github" / "workflows" / "ci.yml"
    assert ci_file.is_file(), f"CI workflow file not found at {ci_file}"

    content = ci_file.read_text(encoding="utf-8")
    # Verify core triggers
    assert "push:" in content
    assert "pull_request:" in content

    # Verify toolchain steps
    assert "ruff check" in content
    assert "mypy" in content
    assert "pytest" in content
    assert "not slow and not docker and not gpu" in content

    # Verify python matrix
    assert "3.11" in content
    assert "3.12" in content


def test_pyproject_defines_ci_markers():
    """Verify pytest markers are defined in pyproject.toml."""
    root = Path(__file__).resolve().parent.parent
    pyproject = root / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")

    assert "slow:" in content
    assert "docker:" in content
    assert "gpu:" in content
