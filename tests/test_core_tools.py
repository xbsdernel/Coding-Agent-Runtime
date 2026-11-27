"""Tests for ISS-018: Core tools: view, search, edit, run, submit.

Verifies:
- Normal output and deterministic error output for each of the 5 tools.
- Observation size capping (max_bytes limit) on all tools.
- Switching edit format (search_replace vs line_range) via config.
- Tool descriptions contain usage examples.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from codeagent.tools import (
    CoreToolRegistry,
    EditFormat,
    check_syntax,
    get_core_tool_definitions,
)


@pytest.fixture
def scratch_repo(tmp_path: Path) -> Path:
    """Create a temporary scratch repository fixture with sample files and git repo."""
    repo = tmp_path / "scratch_repo"
    repo.mkdir()
    (repo / "src").mkdir()

    # Create sample files
    (repo / "README.md").write_text("# Scratch Project\nA demo repo for testing tools.\n")
    (repo / "src" / "calc.py").write_text(
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n\n"
        "def sub(a: int, b: int) -> int:\n"
        "    return a - b\n"
    )
    (repo / "src" / "utils.py").write_text(
        "def log(msg: str) -> None:\n    print(f'[LOG] {msg}')\n"
    )

    # Initialize a git repo inside scratch_repo for git apply tests
    subprocess.run(["git", "init"], cwd=str(repo), capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=str(repo), capture_output=True, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(repo),
        capture_output=True,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=str(repo), capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"], cwd=str(repo), capture_output=True, check=True
    )

    return repo


# ---------------------------------------------------------------------------
# Tool Descriptions & Examples Tests
# ---------------------------------------------------------------------------


def test_tool_definitions_include_examples():
    """All core tools must include a usage example in their description."""
    defs = get_core_tool_definitions(EditFormat.SEARCH_REPLACE)
    assert len(defs) >= 5
    for name, tool_def in defs.items():
        assert "example" in tool_def.description.lower(), f"Tool '{name}' lacks usage example."

    # Also test line_range edit definition
    lr_defs = get_core_tool_definitions(EditFormat.LINE_RANGE)
    assert "example" in lr_defs["edit"].description.lower()


# ---------------------------------------------------------------------------
# Tool: view Tests
# ---------------------------------------------------------------------------


def test_view_tool_normal(scratch_repo: Path):
    """View tool displays file contents with line numbers."""
    registry = CoreToolRegistry(scratch_repo)
    res = registry.execute("view", {"path": "src/calc.py"})
    assert not res.is_error
    assert "1 | def add(a: int, b: int) -> int:" in res.output
    assert "2 |     return a + b" in res.output

    # View line slice
    slice_res = registry.execute("view", {"path": "src/calc.py", "start_line": 4, "end_line": 5})
    assert not slice_res.is_error
    assert "4 | def sub(a: int, b: int) -> int:" in slice_res.output
    assert "1 |" not in slice_res.output


def test_view_tool_error(scratch_repo: Path):
    """View tool returns deterministic error on nonexistent file or invalid lines."""
    registry = CoreToolRegistry(scratch_repo)
    # Nonexistent file
    res1 = registry.execute("view", {"path": "nonexistent.py"})
    assert res1.is_error
    assert "Error: File 'nonexistent.py' does not exist" in res1.output

    # Path escaping repo root
    res2 = registry.execute("view", {"path": "../../outside.txt"})
    assert res2.is_error
    assert "escapes the repository root" in res2.output

    # Invalid line ranges
    res3 = registry.execute("view", {"path": "src/calc.py", "start_line": 10, "end_line": 5})
    assert res3.is_error
    assert "cannot be greater than end_line" in res3.output


# ---------------------------------------------------------------------------
# Tool: search Tests
# ---------------------------------------------------------------------------


def test_search_tool_normal(scratch_repo: Path):
    """Search tool finds regex and text patterns across files."""
    registry = CoreToolRegistry(scratch_repo)
    res = registry.execute("search", {"pattern": "def add", "path": "."})
    assert not res.is_error
    assert "src/calc.py" in res.output or "src\\calc.py" in res.output
    assert "def add(a: int, b: int) -> int:" in res.output


def test_search_tool_file_type_filtering(scratch_repo: Path):
    """Search tool filters by file extension."""
    registry = CoreToolRegistry(scratch_repo)
    # Search in .md only
    res_md = registry.execute("search", {"pattern": "Scratch", "file_type": "md"})
    assert not res_md.is_error
    assert "README.md" in res_md.output

    # Searching for pattern in py files when it's only in md
    res_py = registry.execute("search", {"pattern": "Scratch", "file_type": "py"})
    assert "No matches found" in res_py.output


def test_search_tool_ignore_rules(scratch_repo: Path):
    """Search tool ignores files specified in .gitignore and standard ignore patterns."""
    registry = CoreToolRegistry(scratch_repo)
    # Create an ignored directory and file
    ignored_dir = scratch_repo / "ignored_folder"
    ignored_dir.mkdir()
    (ignored_dir / "secret.py").write_text("def secret_key(): return 12345\n")

    # Add to .gitignore
    (scratch_repo / ".gitignore").write_text("ignored_folder/\n*.tmp\n")
    (scratch_repo / "temp.tmp").write_text("def secret_key(): return 67890\n")

    res = registry.execute("search", {"pattern": "secret_key"})
    assert "No matches found" in res.output


def test_search_tool_context_lines(scratch_repo: Path):
    """Search tool supports context lines around matches."""
    registry = CoreToolRegistry(scratch_repo)
    res = registry.execute(
        "search", {"pattern": "def sub", "path": "src/calc.py", "context_lines": 1}
    )
    assert not res.is_error
    # calc.py has:
    # 2 |     return a + b
    # 3 |
    # 4 | def sub(a: int, b: int) -> int:
    # 5 |     return a - b
    assert "calc.py:4:" in res.output
    assert "calc.py-5-" in res.output


def test_search_tool_ripgrep_delegation(scratch_repo: Path, monkeypatch: pytest.MonkeyPatch):
    """Search tool properly invokes ripgrep when available."""
    from unittest.mock import MagicMock

    from codeagent.runner import RunResult

    registry = CoreToolRegistry(scratch_repo)
    monkeypatch.setattr("codeagent.tools.is_ripgrep_available", lambda: True)

    mock_run = MagicMock(
        return_value=RunResult(
            returncode=0,
            stdout=b"src/calc.py:1: def add(a: int, b: int) -> int:\n",
            stderr=b"",
            duration_s=0.01,
            truncated=False,
            killed=False,
        )
    )
    monkeypatch.setattr("codeagent.tools.run_with_timeout", mock_run)

    res = registry.execute("search", {"pattern": "def add", "file_type": "py", "context_lines": 2})
    assert not res.is_error
    assert "def add" in res.output
    assert mock_run.called
    args = mock_run.call_args[0][0]
    assert "rg" in args
    assert "-C" in args
    assert "2" in args
    assert "-g" in args
    assert "*.py" in args


def test_search_tool_error(scratch_repo: Path):
    """Search tool returns deterministic error on invalid regex or bad path."""
    registry = CoreToolRegistry(scratch_repo)
    # Invalid regex
    res1 = registry.execute("search", {"pattern": "[unclosed bracket", "path": "."})
    assert res1.is_error
    assert "Error: Invalid regular expression pattern" in res1.output

    # Nonexistent search path
    res2 = registry.execute("search", {"pattern": "foo", "path": "does_not_exist"})
    assert res2.is_error
    assert "Error: Search path 'does_not_exist' does not exist" in res2.output


# ---------------------------------------------------------------------------
# Tool: edit Tests (Search-and-Replace & Line-Range)
# ---------------------------------------------------------------------------


def test_edit_search_replace_normal(scratch_repo: Path):
    """Edit with search_replace modifies unique target string."""
    registry = CoreToolRegistry(scratch_repo, edit_format=EditFormat.SEARCH_REPLACE)
    res = registry.execute(
        "edit",
        {"path": "src/calc.py", "old_str": "return a + b", "new_str": "return a + b + 1"},
    )
    assert not res.is_error
    assert "Successfully replaced match" in res.output
    # Verify file content on disk
    content = (scratch_repo / "src" / "calc.py").read_text(encoding="utf-8")
    assert "return a + b + 1" in content


def test_edit_search_replace_error(scratch_repo: Path):
    """Edit with search_replace returns deterministic error if target missing or ambiguous."""
    registry = CoreToolRegistry(scratch_repo, edit_format=EditFormat.SEARCH_REPLACE)

    # Missing target string
    res1 = registry.execute(
        "edit",
        {"path": "src/calc.py", "old_str": "def multiply", "new_str": "def prod"},
    )
    assert res1.is_error
    assert "Error: Target 'old_str' not found" in res1.output

    # Non-unique target string
    res2 = registry.execute(
        "edit",
        {"path": "src/calc.py", "old_str": "int", "new_str": "float"},
    )
    assert res2.is_error
    assert "Must be unique" in res2.output

    # Syntactically broken edit rejected and file unchanged
    orig_content = (scratch_repo / "src" / "calc.py").read_text(encoding="utf-8")
    res_syntax = registry.execute(
        "edit",
        {"path": "src/calc.py", "old_str": "return a + b", "new_str": "return a + + * def"},
    )
    assert res_syntax.is_error
    assert "Syntax error at line" in res_syntax.output
    assert "File left unchanged" in res_syntax.output
    # Verify file was indeed unchanged
    assert (scratch_repo / "src" / "calc.py").read_text(encoding="utf-8") == orig_content


def test_edit_line_range_normal(scratch_repo: Path):
    """Edit with line_range replaces lines correctly."""
    registry = CoreToolRegistry(scratch_repo, edit_format=EditFormat.LINE_RANGE)
    res = registry.execute(
        "edit",
        {
            "path": "src/calc.py",
            "start_line": 1,
            "end_line": 2,
            "new_code": "def add(a: float, b: float) -> float:\n    return a + b",
        },
    )
    assert not res.is_error
    assert "Successfully replaced lines 1-2" in res.output
    content = (scratch_repo / "src" / "calc.py").read_text(encoding="utf-8")
    assert "def add(a: float, b: float) -> float:" in content
    assert "def sub" in content  # untouched


def test_edit_line_range_error(scratch_repo: Path):
    """Edit with line_range returns deterministic error on invalid ranges."""
    registry = CoreToolRegistry(scratch_repo, edit_format=EditFormat.LINE_RANGE)
    res = registry.execute(
        "edit",
        {
            "path": "src/calc.py",
            "start_line": 100,
            "end_line": 105,
            "new_code": "foo",
        },
    )
    assert res.is_error
    assert "out of range" in res.output

    # Syntactically broken edit rejected and file unchanged
    orig_content = (scratch_repo / "src" / "calc.py").read_text(encoding="utf-8")
    res_syntax = registry.execute(
        "edit",
        {
            "path": "src/calc.py",
            "start_line": 1,
            "end_line": 2,
            "new_code": "def ( invalid syntax :::",
        },
    )
    assert res_syntax.is_error
    assert "Syntax error at line" in res_syntax.output
    assert "File left unchanged" in res_syntax.output
    assert (scratch_repo / "src" / "calc.py").read_text(encoding="utf-8") == orig_content


def test_switching_edit_format_single_config(scratch_repo: Path):
    """Switching edit format is a single config value change."""
    # Format 1: search_replace
    reg_sr = CoreToolRegistry(scratch_repo, edit_format="search_replace")
    assert reg_sr.edit_format == EditFormat.SEARCH_REPLACE

    # Format 2: line_range
    reg_lr = CoreToolRegistry(scratch_repo, edit_format="line_range")
    assert reg_lr.edit_format == EditFormat.LINE_RANGE


# ---------------------------------------------------------------------------
# Tool: run Tests
# ---------------------------------------------------------------------------


def test_run_tool_normal(scratch_repo: Path):
    """Run tool executes command and captures output."""
    registry = CoreToolRegistry(scratch_repo)
    cmd = f'"{sys.executable}" -c "print(\'Agent testing run tool\')"'
    res = registry.execute("run", {"command": cmd})
    assert not res.is_error
    assert "Agent testing run tool" in res.output


def test_run_tool_error(scratch_repo: Path):
    """Run tool returns error indication and output for failing commands."""
    registry = CoreToolRegistry(scratch_repo)
    cmd = f'"{sys.executable}" -c "import sys; print(\'Crash!\', file=sys.stderr); sys.exit(1)"'
    res = registry.execute("run", {"command": cmd})
    assert res.is_error
    assert "Crash!" in res.output


def test_run_tool_empty_command_error(scratch_repo: Path):
    """Run tool rejects blank command."""
    registry = CoreToolRegistry(scratch_repo)
    res = registry.execute("run", {"command": "   "})
    assert res.is_error
    assert "Error: Empty command string provided" in res.output


# ---------------------------------------------------------------------------
# Tool: submit Tests
# ---------------------------------------------------------------------------


def test_submit_tool_normal(scratch_repo: Path):
    """Submit tool records submission message and state."""
    registry = CoreToolRegistry(scratch_repo)
    assert not registry.submitted
    res = registry.execute("submit", {"message": "All unit tests pass."})
    assert not res.is_error
    assert registry.submitted
    assert registry.submission_message == "All unit tests pass."
    assert "Task submitted successfully." in res.output


def test_submit_tool_error(scratch_repo: Path):
    """Submit tool rejects unexpected arguments deterministically."""
    registry = CoreToolRegistry(scratch_repo)
    res = registry.execute("submit", {"unexpected_param": 123})
    assert res.is_error
    assert "Invalid arguments for tool 'submit'" in res.output


# ---------------------------------------------------------------------------
# Observation Byte Capping on All Tools
# ---------------------------------------------------------------------------


def test_observation_byte_capping(scratch_repo: Path):
    """Every tool enforces observation byte cap when output exceeds max_observation_bytes."""
    cap = 50  # 50 bytes cap
    registry = CoreToolRegistry(scratch_repo, max_observation_bytes=cap)

    # 1. view capped
    res_view = registry.execute("view", {"path": "README.md"})
    assert res_view.truncated
    assert "[OUTPUT TRUNCATED: observation exceeded byte cap]" in res_view.output

    # 2. search capped
    res_search = registry.execute("search", {"pattern": "def", "path": "."})
    assert res_search.truncated
    assert "results truncated" in res_search.output

    # 3. run capped
    cmd = f'"{sys.executable}" -c "print(\'A\' * 200)"'
    res_run = registry.execute("run", {"command": cmd})
    assert res_run.truncated
    assert "[OUTPUT TRUNCATED: observation exceeded byte cap]" in res_run.output

    # 4. edit capped
    large_new_code = "X" * 100
    res_edit = registry.execute(
        "edit",
        {"path": "src/calc.py", "old_str": "return a - b", "new_str": large_new_code},
    )
    assert not res_edit.is_error
    long_msg_res = registry._cap_output("Z" * 100)
    assert long_msg_res.truncated

    # 5. submit capped
    long_msg = "Solved! " * 20
    res_submit = registry.execute("submit", {"message": long_msg})
    assert res_submit.truncated
    assert "[OUTPUT TRUNCATED: observation exceeded byte cap]" in res_submit.output


# ---------------------------------------------------------------------------
# Patch Tool Safety Tests (ISS-020)
# ---------------------------------------------------------------------------


def test_patch_normal(scratch_repo: Path):
    """Normal patch applies cleanly."""
    registry = CoreToolRegistry(scratch_repo)
    patch_str = (
        "--- a/src/calc.py\n"
        "+++ b/src/calc.py\n"
        "@@ -4,2 +4,2 @@\n"
        "-def sub(a: int, b: int) -> int:\n"
        "-    return a - b\n"
        "+def sub(a: int, b: int) -> int:\n"
        "+    return a - b - 1\n"
    )
    res = registry.execute("patch", {"patch": patch_str})
    assert not res.is_error
    assert "Patch applied successfully." in res.output
    content = (scratch_repo / "src" / "calc.py").read_text(encoding="utf-8")
    assert "return a - b - 1" in content


def test_patch_broken_rejected_pre_apply(scratch_repo: Path):
    """A broken patch is rejected pre-apply by git apply --check; file unchanged."""
    registry = CoreToolRegistry(scratch_repo)
    orig_content = (scratch_repo / "src" / "calc.py").read_text(encoding="utf-8")

    # Mismatched hunk that cannot apply
    broken_patch = (
        "--- a/src/calc.py\n"
        "+++ b/src/calc.py\n"
        "@@ -1,2 +1,2 @@\n"
        "-nonexistent line that does not match anything in calc.py\n"
        "+new replacement line\n"
    )
    res = registry.execute("patch", {"patch": broken_patch})
    assert res.is_error
    assert "Patch rejected pre-apply" in res.output
    assert "File left unchanged" in res.output
    # Verify file is completely unchanged
    assert (scratch_repo / "src" / "calc.py").read_text(encoding="utf-8") == orig_content


def test_patch_syntactically_broken_rejected_post_apply(scratch_repo: Path):
    """A syntactically broken edit in a patch is rejected post-apply; file is reverted."""
    registry = CoreToolRegistry(scratch_repo)
    orig_content = (scratch_repo / "src" / "calc.py").read_text(encoding="utf-8")

    # Valid diff hunk but syntactically broken Python code
    syntax_broken_patch = (
        "--- a/src/calc.py\n"
        "+++ b/src/calc.py\n"
        "@@ -1,5 +1,5 @@\n"
        " def add(a: int, b: int) -> int:\n"
        "-    return a + b\n"
        "+    return a + * broken syntax\n"
        " \n"
        " def sub(a: int, b: int) -> int:\n"
        "     return a - b\n"
    )
    res = registry.execute("patch", {"patch": syntax_broken_patch})
    assert res.is_error
    assert "Patch rejected post-apply due to Syntax error at line" in res.output
    assert "File reverted." in res.output
    # Verify file was reverted to original content
    assert (scratch_repo / "src" / "calc.py").read_text(encoding="utf-8") == orig_content


def test_check_syntax_helper():
    """check_syntax returns proper line numbers and errors."""
    valid, err, line = check_syntax("def ok():\n    pass\n", "test.py")
    assert valid
    assert err is None
    assert line is None

    valid, err, line = check_syntax("def broken(\n", "test.py")
    assert not valid
    assert "Syntax error at line" in err
    assert line == 1

    # JSON syntax
    valid, err, line = check_syntax('{"key": "val"}', "data.json")
    assert valid

    valid, err, line = check_syntax('{"key": val}', "data.json")
    assert not valid
    assert "JSON syntax error at line" in err
