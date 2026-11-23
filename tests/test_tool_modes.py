"""Tests for tool-calling modes, parsers, and benchmark reports."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts directory to sys.path so benchmark script can be imported
scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from benchmark_tool_modes import benchmark_mode  # noqa: E402

from codeagent.tool_parser import (  # noqa: E402
    EDIT_FILE_TOOL,
    STANDARD_TOOLS,
    VIEW_FILE_TOOL,
    ToolMode,
    parse_guided_decoding,
    parse_native_tool_call,
    parse_plaintext_action,
    parse_tool_call_by_mode,
    validate_tool_arguments,
)

ROOT = Path(__file__).resolve().parent.parent


def test_tool_definitions_schema_validity():
    """Verify tool schemas have correct names, descriptions, and parameter constraints."""
    assert VIEW_FILE_TOOL.name == "view_file"
    assert "path" in VIEW_FILE_TOOL.parameters["required"]
    assert "start_line" in VIEW_FILE_TOOL.parameters["properties"]

    assert EDIT_FILE_TOOL.name == "edit_file"
    assert set(EDIT_FILE_TOOL.parameters["required"]) == {"path", "old_str", "new_str"}


def test_validate_tool_arguments():
    """Test schema validator rejects missing parameters and mismatched types."""
    # Valid call
    valid, err = validate_tool_arguments(VIEW_FILE_TOOL, {"path": "src/main.py", "start_line": 10})
    assert valid is True
    assert err is None

    # Missing required path
    valid, err = validate_tool_arguments(VIEW_FILE_TOOL, {"start_line": 10})
    assert valid is False
    assert "Missing required parameter 'path'" in str(err)

    # Wrong type for start_line
    valid, err = validate_tool_arguments(
        VIEW_FILE_TOOL, {"path": "src/main.py", "start_line": "ten"}
    )
    assert valid is False
    assert "expected integer" in str(err)


def test_parse_native_tool_call():
    """Test native <tool_call> parser for valid, missing args, and invalid JSON."""
    # Valid call
    raw = (
        'I will view the file.\n<tool_call>\n{"name": "view_file", '
        '"arguments": {"path": "cli.py", "start_line": 1}}\n</tool_call>'
    )
    calls = parse_native_tool_call(raw, STANDARD_TOOLS)
    assert len(calls) == 1
    assert calls[0].name == "view_file"
    assert calls[0].arguments == {"path": "cli.py", "start_line": 1}
    assert calls[0].is_valid is True

    # Missing required arg
    raw_missing = (
        '<tool_call>\n{"name": "edit_file", "arguments": {"path": "cli.py"}}\n</tool_call>'
    )
    calls_missing = parse_native_tool_call(raw_missing, STANDARD_TOOLS)
    assert len(calls_missing) == 1
    assert calls_missing[0].is_valid is False
    assert "Missing required parameter" in str(calls_missing[0].error)

    # Malformed JSON
    raw_bad = '<tool_call>\n{"name": "view_file", "arguments": {bad_json\n</tool_call>'
    calls_bad = parse_native_tool_call(raw_bad, STANDARD_TOOLS)
    assert len(calls_bad) == 1
    assert calls_bad[0].is_valid is False
    assert "JSON decode failure" in str(calls_bad[0].error)


def test_parse_plaintext_action():
    """Test ReAct-style Action / Action Input parser."""
    # Valid JSON Action Input
    raw = (
        "Thought: Reading file.\n"
        "Action: view_file\n"
        'Action Input: {"path": "test.py", "start_line": 5}'
    )
    calls = parse_plaintext_action(raw, STANDARD_TOOLS)
    assert len(calls) == 1
    assert calls[0].name == "view_file"
    assert calls[0].arguments["path"] == "test.py"
    assert calls[0].is_valid is True

    # Unknown tool
    raw_unknown = 'Action: delete_everything\nAction Input: {"path": "root"}'
    calls_unknown = parse_plaintext_action(raw_unknown, STANDARD_TOOLS)
    assert len(calls_unknown) == 1
    assert calls_unknown[0].is_valid is False
    assert "not in recognized tools list" in str(calls_unknown[0].error)


def test_parse_guided_decoding():
    """Test direct JSON schema guided output parser."""
    raw = '{"name": "edit_file", "arguments": {"path": "a.py", "old_str": "x", "new_str": "y"}}'
    calls = parse_guided_decoding(raw, STANDARD_TOOLS)
    assert len(calls) == 1
    assert calls[0].name == "edit_file"
    assert calls[0].is_valid is True

    # Missing 'name' field
    raw_bad = '{"tool": "edit_file", "args": {}}'
    calls_bad = parse_guided_decoding(raw_bad, STANDARD_TOOLS)
    assert len(calls_bad) == 1
    assert calls_bad[0].is_valid is False


def test_parse_tool_call_by_mode_dispatcher():
    """Test dispatcher maps mode names properly and rejects unknown modes."""
    native_text = '<tool_call>\n{"name": "view_file", "arguments": {"path": "a.py"}}\n</tool_call>'
    res_native = parse_tool_call_by_mode(native_text, ToolMode.NATIVE, STANDARD_TOOLS)
    assert len(res_native) == 1
    assert res_native[0].is_valid is True

    plain_text = 'Action: view_file\nAction Input: {"path": "a.py"}'
    res_plain = parse_tool_call_by_mode(plain_text, "text_format", STANDARD_TOOLS)
    assert len(res_plain) == 1
    assert res_plain[0].is_valid is True

    with pytest.raises(ValueError, match="Unsupported tool calling mode"):
        parse_tool_call_by_mode("dummy", "unsupported_mode")


def test_benchmark_mode_runner():
    """Verify benchmark_mode executes 50 trials and returns valid statistics."""
    malformed_rate, median_lat = benchmark_mode(ToolMode.NATIVE)
    assert isinstance(malformed_rate, float)
    assert 0.0 <= malformed_rate <= 100.0
    assert median_lat > 0.0


def test_reports_tool_call_modes_content():
    """Verify reports/tool_call_modes.md table and decision paragraph exist."""
    report = ROOT / "reports" / "tool_call_modes.md"
    assert report.is_file(), f"Report not found at {report}"

    text = report.read_text(encoding="utf-8")

    # Table presence (3 rows x 2 metric columns)
    assert "| **Native Tool Calling** |" in text
    assert "| **Plain-Text Action Format** |" in text
    assert "| **Guided Decoding** |" in text
    assert "Malformed Rate" in text
    assert "Median Latency" in text

    # Decision paragraph presence
    assert "## 4. Decision for Stage 6" in text
    assert "Native Tool Calling" in text
