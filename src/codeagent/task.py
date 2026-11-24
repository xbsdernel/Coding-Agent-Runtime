"""Task environment and benchmark instance schemas for evaluation.

Defines benchmark instances containing base code, authoritative test suites,
and reference gold patches.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskInstance(BaseModel):
    """Specification of an evaluation benchmark instance."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., description="Unique instance identifier.")
    repo_name: str = Field(..., description="Repository or package name.")
    base_commit: str = Field(default="HEAD", description="Base commit hash or reference.")
    created_at: datetime = Field(
        default_factory=lambda: datetime(2025, 1, 1, tzinfo=UTC),
        description="UTC creation timestamp of the issue/PR for contamination splitting.",
    )
    problem_statement: str = Field(..., description="Task issue or bug description.")
    base_files: dict[str, str] = Field(
        ..., description="Initial source files mapping relative path to content."
    )
    test_patch: str = Field(..., description="Unified diff adding the authoritative test suite.")
    gold_patch: str = Field(..., description="Unified diff that fixes the problem.")
    test_files: list[str] = Field(
        ..., description="List of test file paths that the grader strictly owns."
    )
    test_command: str = Field(
        default="pytest", description="Command to run tests (e.g. 'pytest -q')."
    )
    dockerfile: str = Field(default="", description="Dockerfile specification for the image.")
    image_name: str = Field(default="", description="Tag for the built container image.")
    base_image: str = Field(default="python:3.11-slim", description="Base docker image.")


# ---------------------------------------------------------------------------
# Benchmark Task Instances (3 canonical benchmark environments)
# ---------------------------------------------------------------------------

TASK_CALC = TaskInstance(
    task_id="calc_001_div_zero",
    repo_name="pycalculator",
    base_commit="c101a01",
    created_at=datetime(2024, 3, 15, tzinfo=UTC),
    problem_statement=(
        "Calculator.divide currently raises unhandled ZeroDivisionError when denominator "
        "is zero. It should validate arguments and raise custom CalculationError instead."
    ),
    base_files={
        "calc/__init__.py": (
            "from calc.core import CalculationError, Calculator\n\n"
            '__all__ = ["CalculationError", "Calculator"]\n'
        ),
        "calc/core.py": (
            '"""Core calculator functions."""\n\n\n'
            "class CalculationError(Exception):\n"
            '    """Custom exception raised for calculation errors."""\n\n\n'
            "class Calculator:\n"
            '    """Arithmetic calculator."""\n\n'
            "    def add(self, a: float, b: float) -> float:\n"
            "        return a + b\n\n"
            "    def divide(self, a: float, b: float) -> float:\n"
            "        return a / b\n"
        ),
    },
    test_files=["tests/test_calc.py"],
    test_patch=(
        "diff --git a/tests/test_calc.py b/tests/test_calc.py\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        "+++ b/tests/test_calc.py\n"
        "@@ -0,0 +1,18 @@\n"
        "+import pytest\n"
        "+from calc.core import CalculationError, Calculator\n"
        "+\n"
        "+\n"
        "+def test_add():\n"
        "+    c = Calculator()\n"
        "+    assert c.add(2, 3) == 5\n"
        "+\n"
        "+\n"
        "+def test_divide_valid():\n"
        "+    c = Calculator()\n"
        "+    assert c.divide(10, 2) == 5.0\n"
        "+\n"
        "+\n"
        "+def test_divide_by_zero():\n"
        "+    c = Calculator()\n"
        '+    with pytest.raises(CalculationError, match="Division by zero"):\n'
        "+        c.divide(10, 0)\n"
    ),
    gold_patch=(
        "diff --git a/calc/core.py b/calc/core.py\n"
        "--- a/calc/core.py\n"
        "+++ b/calc/core.py\n"
        "@@ -12,4 +12,6 @@\n"
        "         return a + b\n"
        " \n"
        "     def divide(self, a: float, b: float) -> float:\n"
        "+        if b == 0:\n"
        '+            raise CalculationError("Division by zero")\n'
        "         return a / b\n"
    ),
    test_command="pytest tests/test_calc.py",
    dockerfile=(
        "FROM python:3.11-slim\n"
        "WORKDIR /workspace\n"
        "COPY . /workspace\n"
        "RUN pip install pytest\n"
        'CMD ["pytest", "tests/test_calc.py"]\n'
    ),
    image_name="task-env-calc:latest",
)

TASK_FORMATTER = TaskInstance(
    task_id="formatter_002_truncate",
    repo_name="text-formatter",
    base_commit="f202b02",
    created_at=datetime(2024, 11, 10, tzinfo=UTC),
    problem_statement=(
        "truncate(text, max_len, suffix) appends suffix unconditionally even when "
        "text length <= max_len, and mishandles max_len <= len(suffix)."
    ),
    base_files={
        "formatter/__init__.py": (
            'from formatter.core import truncate\n\n__all__ = ["truncate"]\n'
        ),
        "formatter/core.py": (
            '"""Text formatting utilities."""\n\n\n'
            'def truncate(text: str, max_len: int, suffix: str = "...") -> str:\n'
            '    """Truncate text to max_len appending suffix."""\n'
            "    return text[:max_len] + suffix\n"
        ),
    },
    test_files=["tests/test_formatter.py"],
    test_patch=(
        "diff --git a/tests/test_formatter.py b/tests/test_formatter.py\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        "+++ b/tests/test_formatter.py\n"
        "@@ -0,0 +1,17 @@\n"
        "+from formatter.core import truncate\n"
        "+\n"
        "+\n"
        "+def test_truncate_shorter():\n"
        '+    assert truncate("hello", 10) == "hello"\n'
        "+\n"
        "+\n"
        "+def test_truncate_exact():\n"
        '+    assert truncate("hello", 5) == "hello"\n'
        "+\n"
        "+\n"
        "+def test_truncate_longer():\n"
        '+    assert truncate("hello world", 8, "...") == "hello..."\n'
        "+\n"
        "+\n"
        "+def test_truncate_short_max_len():\n"
        '+    assert truncate("hello", 2, "...") == "he"\n'
    ),
    gold_patch=(
        "diff --git a/formatter/core.py b/formatter/core.py\n"
        "--- a/formatter/core.py\n"
        "+++ b/formatter/core.py\n"
        "@@ -3,4 +3,8 @@\n"
        " \n"
        ' def truncate(text: str, max_len: int, suffix: str = "...") -> str:\n'
        '     """Truncate text to max_len appending suffix."""\n'
        "+    if len(text) <= max_len:\n"
        "+        return text\n"
        "+    if max_len <= len(suffix):\n"
        "+        return text[:max_len]\n"
        "-    return text[:max_len] + suffix\n"
        "+    return text[: max_len - len(suffix)] + suffix\n"
    ),
    test_command="pytest tests/test_formatter.py",
    dockerfile=(
        "FROM python:3.11-slim\n"
        "WORKDIR /workspace\n"
        "COPY . /workspace\n"
        "RUN pip install pytest\n"
        'CMD ["pytest", "tests/test_formatter.py"]\n'
    ),
    image_name="task-env-formatter:latest",
)

TASK_GRAPH = TaskInstance(
    task_id="graph_003_cycle",
    repo_name="graph-utils",
    base_commit="g303c03",
    created_at=datetime(2025, 1, 20, tzinfo=UTC),
    problem_statement=(
        "detect_cycle(adj) returns False for all graphs. It should accurately detect "
        "directed cycles in both connected and disconnected graphs."
    ),
    base_files={
        "graph/__init__.py": (
            'from graph.core import detect_cycle\n\n__all__ = ["detect_cycle"]\n'
        ),
        "graph/core.py": (
            '"""Graph utilities."""\n\n\n'
            "def detect_cycle(adj: dict[str, list[str]]) -> bool:\n"
            '    """Return True if directed graph contains a cycle."""\n'
            "    return False\n"
        ),
    },
    test_files=["tests/test_graph.py"],
    test_patch=(
        "diff --git a/tests/test_graph.py b/tests/test_graph.py\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        "+++ b/tests/test_graph.py\n"
        "@@ -0,0 +1,16 @@\n"
        "+from graph.core import detect_cycle\n"
        "+\n"
        "+\n"
        "+def test_dag_no_cycle():\n"
        '+    graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}\n'
        "+    assert detect_cycle(graph) is False\n"
        "+\n"
        "+\n"
        "+def test_direct_cycle():\n"
        '+    graph = {"A": ["B"], "B": ["C"], "C": ["A"]}\n'
        "+    assert detect_cycle(graph) is True\n"
        "+\n"
        "+\n"
        "+def test_disconnected_cycle():\n"
        '+    graph = {"A": ["B"], "B": [], "C": ["D"], "D": ["E"], "E": ["C"]}\n'
        "+    assert detect_cycle(graph) is True\n"
    ),
    gold_patch=(
        "diff --git a/graph/core.py b/graph/core.py\n"
        "--- a/graph/core.py\n"
        "+++ b/graph/core.py\n"
        "@@ -3,4 +3,23 @@\n"
        " \n"
        " def detect_cycle(adj: dict[str, list[str]]) -> bool:\n"
        '     """Return True if directed graph contains a cycle."""\n'
        "+    visited: set[str] = set()\n"
        "+    rec_stack: set[str] = set()\n"
        "+\n"
        "+    def dfs(node: str) -> bool:\n"
        "+        visited.add(node)\n"
        "+        rec_stack.add(node)\n"
        "+        for neighbor in adj.get(node, []):\n"
        "+            if neighbor not in visited:\n"
        "+                if dfs(neighbor):\n"
        "+                    return True\n"
        "+            elif neighbor in rec_stack:\n"
        "+                return True\n"
        "+        rec_stack.remove(node)\n"
        "+        return False\n"
        "+\n"
        "+    for node in list(adj.keys()):\n"
        "+        if node not in visited:\n"
        "+            if dfs(node):\n"
        "+                return True\n"
        "     return False\n"
    ),
    test_command="pytest tests/test_graph.py",
    dockerfile=(
        "FROM python:3.11-slim\n"
        "WORKDIR /workspace\n"
        "COPY . /workspace\n"
        "RUN pip install pytest\n"
        'CMD ["pytest", "tests/test_graph.py"]\n'
    ),
    image_name="task-env-graph:latest",
)

BENCHMARK_TASKS: dict[str, TaskInstance] = {
    TASK_CALC.task_id: TASK_CALC,
    TASK_FORMATTER.task_id: TASK_FORMATTER,
    TASK_GRAPH.task_id: TASK_GRAPH,
}
