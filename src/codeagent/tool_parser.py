"""Tool-call parsers and schema validation across multiple interaction modes.

Supports three distinct tool-calling modes:
1. Native tool calling (Qwen2.5-Coder / OpenAI ChatML <tool_call> tags)
2. Plain-text action format (ReAct Action / Action Input blocks)
3. Guided decoding (Grammar-constrained JSON schema outputs)
"""

from __future__ import annotations

import json
import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from codeagent.chat_template import ToolDefinition


class ToolMode(StrEnum):
    """Interaction mode for model tool invocations."""

    NATIVE = "native"
    TEXT_FORMAT = "text_format"
    GUIDED_DECODING = "guided_decoding"


class ParsedToolCall(BaseModel):
    """Result of parsing and validating a model tool invocation."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Name of the called tool function.")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Parsed and validated keyword arguments."
    )
    raw: str = Field(description="Raw text segment parsed.")
    is_valid: bool = Field(description="Whether arguments conform to tool JSON schema.")
    error: str | None = Field(default=None, description="Validation or parsing error details.")


# ---------------------------------------------------------------------------
# Canonical Standard Tools
# ---------------------------------------------------------------------------

VIEW_FILE_TOOL = ToolDefinition(
    name="view_file",
    description="Read file contents or specific line ranges within working directory.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path to file."},
            "start_line": {
                "type": "integer",
                "description": "1-based starting line number (optional).",
            },
            "end_line": {
                "type": "integer",
                "description": "1-based ending line number (optional).",
            },
        },
        "required": ["path"],
    },
)

EDIT_FILE_TOOL = ToolDefinition(
    name="edit_file",
    description="Perform precise search-and-replace modification on an existing file.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path to file to modify."},
            "old_str": {
                "type": "string",
                "description": "Target string to replace (must match exactly).",
            },
            "new_str": {
                "type": "string",
                "description": "Replacement string.",
            },
        },
        "required": ["path", "old_str", "new_str"],
    },
)

STANDARD_TOOLS: dict[str, ToolDefinition] = {
    VIEW_FILE_TOOL.name: VIEW_FILE_TOOL,
    EDIT_FILE_TOOL.name: EDIT_FILE_TOOL,
}


# ---------------------------------------------------------------------------
# Schema Validator
# ---------------------------------------------------------------------------


def validate_tool_arguments(tool: ToolDefinition, args: dict[str, Any]) -> tuple[bool, str | None]:
    """Validate argument dictionary against tool's JSON Schema."""
    params = tool.parameters
    req_fields = params.get("required", [])

    for req in req_fields:
        if req not in args:
            return False, f"Missing required parameter '{req}' for tool '{tool.name}'"

    props = params.get("properties", {})
    for k, val in args.items():
        if k in props:
            expected_type = props[k].get("type")
            if expected_type == "string" and not isinstance(val, str):
                return False, f"Parameter '{k}' expected string, got {type(val).__name__}"
            if expected_type == "integer" and not isinstance(val, int):
                return False, f"Parameter '{k}' expected integer, got {type(val).__name__}"
            if expected_type == "boolean" and not isinstance(val, bool):
                return False, f"Parameter '{k}' expected boolean, got {type(val).__name__}"
            if expected_type == "array" and not isinstance(val, list):
                return False, f"Parameter '{k}' expected array, got {type(val).__name__}"
            if expected_type == "object" and not isinstance(val, dict):
                return False, f"Parameter '{k}' expected object, got {type(val).__name__}"

    return True, None


# ---------------------------------------------------------------------------
# Mode Parsers
# ---------------------------------------------------------------------------


def parse_native_tool_call(
    text: str, tools: dict[str, ToolDefinition] = STANDARD_TOOLS
) -> list[ParsedToolCall]:
    """Parse native <tool_call> JSON blocks as emitted by Qwen2.5-Coder / ChatML."""
    pattern = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)
    matches = list(pattern.finditer(text))

    # Also support raw JSON fallback if enclosed without tags
    if not matches and text.strip().startswith("{") and text.strip().endswith("}"):
        matches = [re.match(r"(.*)", text.strip(), re.DOTALL)]  # type: ignore

    results: list[ParsedToolCall] = []

    for match in matches:
        if not match:
            continue
        raw_segment = match.group(1) if match.lastindex else match.group(0)
        try:
            data = json.loads(raw_segment)
        except json.JSONDecodeError as e:
            results.append(
                ParsedToolCall(
                    name="unknown",
                    arguments={},
                    raw=raw_segment,
                    is_valid=False,
                    error=f"JSON decode failure: {e}",
                )
            )
            continue

        if not isinstance(data, dict) or "name" not in data:
            results.append(
                ParsedToolCall(
                    name="unknown",
                    arguments={},
                    raw=raw_segment,
                    is_valid=False,
                    error="Tool call missing 'name' field",
                )
            )
            continue

        tool_name = str(data["name"])
        args = data.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {"raw": args}

        if tool_name not in tools:
            results.append(
                ParsedToolCall(
                    name=tool_name,
                    arguments=args,
                    raw=raw_segment,
                    is_valid=False,
                    error=f"Tool '{tool_name}' not in recognized tools list",
                )
            )
            continue

        valid, err = validate_tool_arguments(tools[tool_name], args)
        results.append(
            ParsedToolCall(
                name=tool_name,
                arguments=args,
                raw=raw_segment,
                is_valid=valid,
                error=err,
            )
        )

    return results


def parse_plaintext_action(
    text: str, tools: dict[str, ToolDefinition] = STANDARD_TOOLS
) -> list[ParsedToolCall]:
    """Parse ReAct-style Action: <tool>\nAction Input: <json/dict> blocks."""
    action_match = re.search(r"Action:\s*([a-zA-Z0-9_\-]+)", text, re.IGNORECASE)
    if not action_match:
        return []

    tool_name = action_match.group(1).strip()
    after_action = text[action_match.end() :]
    input_match = re.search(r"Action Input:\s*(.+)", after_action, re.DOTALL | re.IGNORECASE)

    raw_input = "{}"
    if input_match:
        raw_val = input_match.group(1).strip()
        stop_match = re.search(r"\n(?:Action|Observation|Thought):", raw_val, re.IGNORECASE)
        raw_input = raw_val[: stop_match.start()].strip() if stop_match else raw_val

    # Try parsing JSON input
    args: dict[str, Any] = {}
    try:
        parsed_input = json.loads(raw_input)
        args = parsed_input if isinstance(parsed_input, dict) else {"input": parsed_input}
    except json.JSONDecodeError:
        # Fallback key-value parser: path=...
        kv_pairs = re.findall(r'(\w+)=["\']?(.*?)["\']?(?:,|$|\s)', raw_input)
        args = dict(kv_pairs) if kv_pairs else {"raw": raw_input}

    if tool_name not in tools:
        return [
            ParsedToolCall(
                name=tool_name,
                arguments=args,
                raw=text,
                is_valid=False,
                error=f"Tool '{tool_name}' not in recognized tools list",
            )
        ]

    valid, err = validate_tool_arguments(tools[tool_name], args)
    return [
        ParsedToolCall(
            name=tool_name,
            arguments=args,
            raw=text,
            is_valid=valid,
            error=err,
        )
    ]


def parse_guided_decoding(
    text: str, tools: dict[str, ToolDefinition] = STANDARD_TOOLS
) -> list[ParsedToolCall]:
    """Parse direct JSON schema object guaranteed by token-level grammar constraint."""
    clean_text = text.strip()
    try:
        data = json.loads(clean_text)
    except json.JSONDecodeError as e:
        return [
            ParsedToolCall(
                name="unknown",
                arguments={},
                raw=clean_text,
                is_valid=False,
                error=f"Grammar constraint violated / invalid JSON: {e}",
            )
        ]

    if not isinstance(data, dict) or "name" not in data:
        return [
            ParsedToolCall(
                name="unknown",
                arguments={},
                raw=clean_text,
                is_valid=False,
                error="Guided decoding JSON missing required 'name' key",
            )
        ]

    tool_name = str(data["name"])
    args = data.get("arguments", {})
    if not isinstance(args, dict):
        args = {"raw": args}

    if tool_name not in tools:
        return [
            ParsedToolCall(
                name=tool_name,
                arguments=args,
                raw=clean_text,
                is_valid=False,
                error=f"Tool '{tool_name}' not in recognized tools list",
            )
        ]

    valid, err = validate_tool_arguments(tools[tool_name], args)
    return [
        ParsedToolCall(
            name=tool_name,
            arguments=args,
            raw=clean_text,
            is_valid=valid,
            error=err,
        )
    ]


def parse_tool_call_by_mode(
    text: str, mode: ToolMode | str, tools: dict[str, ToolDefinition] = STANDARD_TOOLS
) -> list[ParsedToolCall]:
    """Dispatch parsing based on tool interaction mode."""
    mode_str = str(mode).lower()
    if mode_str in (ToolMode.NATIVE, "native"):
        return parse_native_tool_call(text, tools)
    if mode_str in (ToolMode.TEXT_FORMAT, "text_format", "text"):
        return parse_plaintext_action(text, tools)
    if mode_str in (ToolMode.GUIDED_DECODING, "guided_decoding", "guided"):
        return parse_guided_decoding(text, tools)

    raise ValueError(f"Unsupported tool calling mode: '{mode}'")
