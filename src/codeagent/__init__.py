"""Coding-Agent Runtime — autonomous code-repair agent framework."""

from codeagent.chat_template import (
    ChatMessage,
    ToolDefinition,
    apply_chat_template,
    check_prefix_stability,
    parse_tool_calls,
    tokenize_chatml,
)
from codeagent.schemas import (
    BudgetSpec,
    EventKind,
    ExperimentConfig,
    ResultRow,
    StopReason,
    TraceEvent,
)
from codeagent.tool_parser import (
    EDIT_FILE_TOOL,
    STANDARD_TOOLS,
    VIEW_FILE_TOOL,
    ParsedToolCall,
    ToolMode,
    parse_guided_decoding,
    parse_native_tool_call,
    parse_plaintext_action,
    parse_tool_call_by_mode,
    validate_tool_arguments,
)
from codeagent.trace import TraceReader, TraceWriter

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "BudgetSpec",
    "ChatMessage",
    "EDIT_FILE_TOOL",
    "EventKind",
    "ExperimentConfig",
    "ParsedToolCall",
    "ResultRow",
    "STANDARD_TOOLS",
    "StopReason",
    "ToolDefinition",
    "ToolMode",
    "TraceEvent",
    "TraceReader",
    "TraceWriter",
    "VIEW_FILE_TOOL",
    "apply_chat_template",
    "check_prefix_stability",
    "parse_guided_decoding",
    "parse_native_tool_call",
    "parse_plaintext_action",
    "parse_tool_call_by_mode",
    "parse_tool_calls",
    "tokenize_chatml",
    "validate_tool_arguments",
]
