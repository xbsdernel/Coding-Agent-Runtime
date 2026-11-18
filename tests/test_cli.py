"""Tests for the CLI entry point."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from codeagent.cli import _git_describe, _is_dirty, main


class TestCLI:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Coding-Agent Runtime" in result.output

    def test_version_shows_git_stamp(self):
        runner = CliRunner()
        with patch("codeagent.cli._git_describe", return_value="v0-scaffold-0-g3ab0d58"):
            result = runner.invoke(main, ["--version"])
            assert result.exit_code == 0
            assert "0.1.0" in result.output
            assert "v0-scaffold-0-g3ab0d58" in result.output

    def test_info(self):
        runner = CliRunner()
        with patch("codeagent.cli._git_describe", return_value="v0-scaffold"):
            result = runner.invoke(main, ["info"])
            assert result.exit_code == 0
            assert "codeagent 0.1.0 (git: v0-scaffold)" in result.output

    def test_run_aborts_on_dirty_tree(self):
        runner = CliRunner()
        with patch("codeagent.cli._is_dirty", return_value=True):
            result = runner.invoke(main, ["run"])
            assert result.exit_code == 1
            assert "Refusing to run on a dirty working tree" in result.output

    def test_run_proceeds_on_clean_tree(self):
        runner = CliRunner()
        with patch("codeagent.cli._is_dirty", return_value=False):
            result = runner.invoke(main, ["run"])
            assert result.exit_code == 0
            assert "not yet implemented" in result.output

    def test_git_describe_live(self):
        val = _git_describe()
        assert isinstance(val, str)
        assert len(val) > 0
        assert val != "unknown"

    def test_is_dirty_live(self):
        val = _is_dirty()
        assert isinstance(val, bool)
