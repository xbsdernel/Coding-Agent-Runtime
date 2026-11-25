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
from codeagent.runner import RunResult, run_with_timeout
from codeagent.sandbox import (
    ContainerExecResult,
    ContainerMetrics,
    DockerSandbox,
    SandboxConfig,
    is_docker_available,
)
from codeagent.schemas import (
    BudgetSpec,
    EventKind,
    ExperimentConfig,
    ResultRow,
    StopReason,
    TraceEvent,
)
from codeagent.splitter import (
    SplitManifest,
    SplitName,
    TaskRecord,
    get_cutoff_for_model,
    split_tasks,
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
    "ContainerExecResult",
    "ContainerMetrics",
    "DockerSandbox",
    "EDIT_FILE_TOOL",
    "EventKind",
    "ExperimentConfig",
    "GradingResult",
    "ImageBuildMetrics",
    "ParsedToolCall",
    "ResultRow",
    "RunResult",
    "SandboxConfig",
    "STANDARD_TOOLS",
    "SplitManifest",
    "SplitName",
    "StopReason",
    "TASK_CALC",
    "TASK_FORMATTER",
    "TASK_GRAPH",
    "TaskInstance",
    "TaskRecord",
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
    "get_cutoff_for_model",
    "grade_instance",
    "is_docker_available",
    "parse_guided_decoding",
    "parse_native_tool_call",
    "parse_plaintext_action",
    "parse_tool_call_by_mode",
    "parse_tool_calls",
    "patch_modifies_test_files",
    "run_with_timeout",
    "split_tasks",
    "strip_test_modifications",
    "tokenize_chatml",
    "validate_tool_arguments",
]
