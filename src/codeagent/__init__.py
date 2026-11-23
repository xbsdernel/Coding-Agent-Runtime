"""Coding-Agent Runtime — autonomous code-repair agent framework."""

from codeagent.chat_template import (
    ChatMessage,
    ToolDefinition,
    apply_chat_template,
    check_prefix_stability,
    parse_tool_calls,
    tokenize_chatml,
)
from codeagent.grader import (
    GradingResult,
    ImageBuildMetrics,
    build_task_image,
    generate_task_images_report,
    grade_instance,
    patch_modifies_test_files,
    strip_test_modifications,
)
from codeagent.schemas import (
    BudgetSpec,
    EventKind,
    ExperimentConfig,
    ResultRow,
    StopReason,
    TraceEvent,
)
from codeagent.task import (
    BENCHMARK_TASKS,
    TASK_CALC,
    TASK_FORMATTER,
    TASK_GRAPH,
    TaskInstance,
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
    "BENCHMARK_TASKS",
    "BudgetSpec",
    "ChatMessage",
    "EDIT_FILE_TOOL",
    "EventKind",
    "ExperimentConfig",
    "GradingResult",
    "ImageBuildMetrics",
    "ParsedToolCall",
    "ResultRow",
    "STANDARD_TOOLS",
    "StopReason",
    "TASK_CALC",
    "TASK_FORMATTER",
    "TASK_GRAPH",
    "TaskInstance",
    "ToolDefinition",
    "ToolMode",
    "TraceEvent",
    "TraceReader",
    "TraceWriter",
    "VIEW_FILE_TOOL",
    "apply_chat_template",
    "build_task_image",
    "check_prefix_stability",
    "generate_task_images_report",
    "grade_instance",
    "parse_guided_decoding",
    "parse_native_tool_call",
    "parse_plaintext_action",
    "parse_tool_call_by_mode",
    "parse_tool_calls",
    "patch_modifies_test_files",
    "strip_test_modifications",
    "tokenize_chatml",
    "validate_tool_arguments",
]
