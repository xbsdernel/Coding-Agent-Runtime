"""Core tools: view, search, edit, run, submit for repository manipulation.

Implements the five core tools against a scratch repository inside the sandbox:
- view: Inspect file contents or line ranges.
- search: Search for regex patterns or text in files.
- edit: Modify files with search-and-replace or line-range replacement.
- run: Execute commands in the scratch repo environment with timeout.
- submit: Finalize the episode and submit the task solution.

Each tool enforces an observation byte cap, returns deterministic error
messages on failure, and includes a usage example in its description.
"""

from __future__ import annotations

import fnmatch
import os
import re
import shutil
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from codeagent.chat_template import ToolDefinition
from codeagent.runner import run_with_timeout

__all__ = [
    "CoreToolRegistry",
    "EditFormat",
    "ToolExecutionResult",
    "get_core_tool_definitions",
    "is_ripgrep_available",
]


def is_ripgrep_available() -> bool:
    """Check if the ripgrep (`rg`) executable is available in PATH."""
    return shutil.which("rg") is not None


class EditFormat(StrEnum):
    """Format for file editing operations."""

    SEARCH_REPLACE = "search_replace"
    LINE_RANGE = "line_range"


class ToolExecutionResult(BaseModel):
    """Result of executing an agent tool."""

    model_config = ConfigDict(extra="forbid")

    output: str = Field(description="Captured observation text (or error message).")
    is_error: bool = Field(default=False, description="Whether the tool call resulted in an error.")
    truncated: bool = Field(default=False, description="Whether output was capped at max_bytes.")


# ---------------------------------------------------------------------------
# Tool Definitions with Usage Examples
# ---------------------------------------------------------------------------

VIEW_TOOL_DEF = ToolDefinition(
    name="view",
    description=(
        "View file contents or specific line ranges within the repository.\n"
        "Usage example:\n"
        '{"path": "src/module.py", "start_line": 1, "end_line": 20}'
    ),
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

SEARCH_TOOL_DEF = ToolDefinition(
    name="search",
    description=(
        "Search for regex patterns or text across files in a directory or single file.\n"
        "Supports ripgrep when available, falling back to python search with ignore rules,\n"
        "file-type filters, context lines, and output capping.\n"
        "Usage example:\n"
        '{"pattern": "def parse_args", "path": "src", "file_type": "py", "context_lines": 1}'
    ),
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex or string pattern to match."},
            "path": {
                "type": "string",
                "description": "Relative directory or file path to search (default: '.').",
            },
            "file_type": {
                "type": "string",
                "description": "Optional file extension or type filter (e.g., 'py', 'md', 'json').",
            },
            "context_lines": {
                "type": "integer",
                "description": "Number of context lines before and after match (default: 0).",
            },
        },
        "required": ["pattern"],
    },
)

EDIT_TOOL_SEARCH_REPLACE_DEF = ToolDefinition(
    name="edit",
    description=(
        "Edit an existing file by replacing an exact string match (search-and-replace).\n"
        "Usage example:\n"
        '{"path": "src/calc.py", "old_str": "return a - b", "new_str": "return a + b"}'
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path to file."},
            "old_str": {"type": "string", "description": "Exact text to replace."},
            "new_str": {"type": "string", "description": "Replacement text."},
        },
        "required": ["path", "old_str", "new_str"],
    },
)

EDIT_TOOL_LINE_RANGE_DEF = ToolDefinition(
    name="edit",
    description=(
        "Edit an existing file by replacing lines between start_line and end_line.\n"
        "Usage example:\n"
        '{"path": "src/calc.py", "start_line": 10, "end_line": 12, "new_code": "    return a + b"}'
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path to file."},
            "start_line": {"type": "integer", "description": "1-based starting line to replace."},
            "end_line": {"type": "integer", "description": "1-based ending line to replace."},
            "new_code": {"type": "string", "description": "Replacement code string."},
        },
        "required": ["path", "start_line", "end_line", "new_code"],
    },
)

RUN_TOOL_DEF = ToolDefinition(
    name="run",
    description=(
        "Execute a shell command inside the repository workspace with timeout.\n"
        "Usage example:\n"
        '{"command": "pytest tests/test_calc.py"}'
    ),
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command line to execute."},
        },
        "required": ["command"],
    },
)

SUBMIT_TOOL_DEF = ToolDefinition(
    name="submit",
    description=(
        "Finalize and submit the task solution when work is finished.\n"
        "Usage example:\n"
        '{"message": "Fixed the calculation bug in src/calc.py"}'
    ),
    parameters={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Optional summary or explanation of the submitted solution.",
            },
        },
    },
)


def get_core_tool_definitions(
    edit_format: EditFormat | str = EditFormat.SEARCH_REPLACE,
) -> dict[str, ToolDefinition]:
    """Return dictionary of ToolDefinitions matching the requested edit format."""
    edit_fmt = EditFormat(edit_format)
    edit_def = (
        EDIT_TOOL_SEARCH_REPLACE_DEF
        if edit_fmt == EditFormat.SEARCH_REPLACE
        else EDIT_TOOL_LINE_RANGE_DEF
    )
    return {
        "view": VIEW_TOOL_DEF,
        "search": SEARCH_TOOL_DEF,
        "edit": edit_def,
        "run": RUN_TOOL_DEF,
        "submit": SUBMIT_TOOL_DEF,
    }


# ---------------------------------------------------------------------------
# Core Tool Registry & Implementation
# ---------------------------------------------------------------------------


class CoreToolRegistry:
    """Dispatches and executes the 5 core tools in a scratch repository.

    Parameters
    ----------
    repo_dir:
        Root directory of the repository/scratch workspace.
    max_observation_bytes:
        Maximum bytes permitted in an observation before truncation.
    edit_format:
        Editing format mode ('search_replace' or 'line_range').
    command_timeout_s:
        Timeout in seconds for run tool executions.
    """

    def __init__(
        self,
        repo_dir: str | Path,
        max_observation_bytes: int = 16 * 1024,  # 16 KB default observation cap
        edit_format: EditFormat | str = EditFormat.SEARCH_REPLACE,
        command_timeout_s: float = 30.0,
    ) -> None:
        self.repo_dir = Path(repo_dir).resolve()
        self.max_observation_bytes = max_observation_bytes
        self.edit_format = EditFormat(edit_format)
        self.command_timeout_s = command_timeout_s
        self.submitted = False
        self.submission_message: str | None = None

    def _cap_output(
        self, text: str, is_error: bool = False, truncation_note: str | None = None
    ) -> ToolExecutionResult:
        """Enforce observation byte cap on output string."""
        encoded = text.encode("utf-8", errors="replace")
        truncated = False
        if len(encoded) > self.max_observation_bytes:
            truncated = True
            capped_bytes = encoded[: self.max_observation_bytes]
            # Decode cleanly ignoring split multi-byte characters at cut point
            capped_str = capped_bytes.decode("utf-8", errors="ignore")
            note = truncation_note or "[OUTPUT TRUNCATED: observation exceeded byte cap]"
            text = f"{capped_str}\n{note}"

        return ToolExecutionResult(output=text, is_error=is_error, truncated=truncated)

    def _resolve_safe_path(self, rel_path: str) -> Path:
        """Resolve a relative path ensuring it does not escape repo_dir."""
        target = (self.repo_dir / rel_path).resolve()
        if not str(target).startswith(str(self.repo_dir)):
            raise ValueError(f"Path '{rel_path}' escapes the repository root")
        return target

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> ToolExecutionResult:
        """Dispatch and execute tool call."""
        try:
            if tool_name == "view":
                return self.view(**arguments)
            if tool_name == "search":
                return self.search(**arguments)
            if tool_name == "edit":
                return self.edit(**arguments)
            if tool_name == "run":
                return self.run(**arguments)
            if tool_name == "submit":
                return self.submit(**arguments)
            return self._cap_output(f"Error: Unknown tool '{tool_name}'", is_error=True)
        except TypeError as e:
            return self._cap_output(
                f"Error: Invalid arguments for tool '{tool_name}': {e}", is_error=True
            )
        except Exception as e:
            return self._cap_output(
                f"Error: Tool execution failed for '{tool_name}': {e}", is_error=True
            )

    # -----------------------------------------------------------------------
    # Tool: view
    # -----------------------------------------------------------------------

    def view(
        self,
        path: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> ToolExecutionResult:
        """View file contents or line slice."""
        try:
            resolved = self._resolve_safe_path(path)
        except ValueError as err:
            return self._cap_output(f"Error: {err}", is_error=True)

        if not resolved.exists():
            return self._cap_output(f"Error: File '{path}' does not exist", is_error=True)
        if resolved.is_dir():
            return self._cap_output(f"Error: '{path}' is a directory, not a file", is_error=True)

        try:
            lines = resolved.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        except Exception as e:
            return self._cap_output(f"Error reading file '{path}': {e}", is_error=True)

        total_lines = len(lines)
        if start_line is not None and end_line is not None and start_line > end_line:
            return self._cap_output(
                f"Error: start_line ({start_line}) cannot be greater than end_line ({end_line})",
                is_error=True,
            )

        s_line = 1 if start_line is None else max(1, start_line)
        e_line = total_lines if end_line is None else min(total_lines, end_line)

        if s_line > total_lines and total_lines > 0:
            return self._cap_output(
                f"Error: start_line {s_line} exceeds total lines ({total_lines}) in '{path}'",
                is_error=True,
            )

        selected_lines = lines[s_line - 1 : e_line]
        formatted = []
        for idx, line in enumerate(selected_lines, start=s_line):
            formatted.append(f"{idx:4d} | {line}")

        return self._cap_output("".join(formatted))

    # -----------------------------------------------------------------------
    # Tool: search
    # -----------------------------------------------------------------------

    def _load_ignore_patterns(self) -> list[str]:
        """Load ignore patterns from .gitignore and standard defaults."""
        patterns = [
            ".git",
            ".git/*",
            "*.pyc",
            "__pycache__",
            "__pycache__/*",
            ".pytest_cache",
            ".pytest_cache/*",
            ".venv",
            ".venv/*",
            "*.egg-info",
        ]
        gitignore = self.repo_dir / ".gitignore"
        if gitignore.is_file():
            try:
                for line in gitignore.read_text(encoding="utf-8", errors="replace").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)
            except Exception:
                pass
        return patterns

    def _is_ignored(self, path: Path, ignore_patterns: list[str]) -> bool:
        """Check if relative path matches any ignore pattern."""
        try:
            rel = path.relative_to(self.repo_dir).as_posix()
        except ValueError:
            rel = path.as_posix()

        name = path.name
        for pat in ignore_patterns:
            pat_clean = pat.rstrip("/")
            if fnmatch.fnmatch(name, pat_clean) or fnmatch.fnmatch(rel, pat_clean):
                return True
            if pat.endswith("/*") and (
                fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat_clean + "/*")
            ):
                return True
            # Also match subdirectories
            parts = rel.split("/")
            if any(fnmatch.fnmatch(part, pat_clean) for part in parts):
                return True
        return False

    def search(
        self,
        pattern: str,
        path: str = ".",
        file_type: str | None = None,
        context_lines: int = 0,
    ) -> ToolExecutionResult:
        """Search regex or text across workspace using ripgrep or Python fallback."""
        try:
            target = self._resolve_safe_path(path)
        except ValueError as err:
            return self._cap_output(f"Error: {err}", is_error=True)

        if not target.exists():
            return self._cap_output(f"Error: Search path '{path}' does not exist", is_error=True)

        # Try ripgrep if installed
        if is_ripgrep_available():
            res = self._search_with_ripgrep(pattern, target, file_type, context_lines)
            if res is not None:
                return res

        # Python fallback search
        return self._search_with_python(pattern, target, file_type, context_lines)

    def _search_with_ripgrep(
        self,
        pattern: str,
        target: Path,
        file_type: str | None,
        context_lines: int,
    ) -> ToolExecutionResult | None:
        """Execute search using ripgrep binary."""
        cmd = ["rg", "--line-number", "--color", "never", "--no-heading"]
        if context_lines > 0:
            cmd.extend(["-C", str(context_lines)])
        if file_type:
            ft = file_type.lstrip(".")
            cmd.extend(["-g", f"*.{ft}"])

        cmd.extend([pattern, str(target)])
        try:
            res = run_with_timeout(
                cmd,
                cwd=str(self.repo_dir),
                timeout_s=self.command_timeout_s,
                max_bytes=self.max_observation_bytes,
            )
        except Exception:
            return None

        # ripgrep returns 0 if match found, 1 if no match, 2 if error
        if res.returncode == 1:
            rel = target.relative_to(self.repo_dir).as_posix() if target != self.repo_dir else "."
            return self._cap_output(f"No matches found for pattern '{pattern}' in '{rel}'")

        if res.returncode == 0:
            out_str = res.stdout.decode("utf-8", errors="replace").strip()
            # Normalize target paths relative to repo_dir if possible
            return self._cap_output(
                out_str, truncation_note="[OUTPUT TRUNCATED: results truncated at limit]"
            )

        if res.returncode != 0 and res.stderr:
            err_text = res.stderr.decode("utf-8", errors="replace").strip()
            return self._cap_output(f"Error: ripgrep failed: {err_text}", is_error=True)

        return None

    def _search_with_python(
        self,
        pattern: str,
        target: Path,
        file_type: str | None,
        context_lines: int,
    ) -> ToolExecutionResult:
        """Execute search using pure Python regex and directory traversal."""
        try:
            regex = re.compile(pattern)
        except re.error as err:
            return self._cap_output(
                f"Error: Invalid regular expression pattern '{pattern}': {err}", is_error=True
            )

        ignore_patterns = self._load_ignore_patterns()
        clean_ext = f".{file_type.lstrip('.')}" if file_type else None

        files_to_search: list[Path] = []
        if target.is_file():
            if not self._is_ignored(target, ignore_patterns) and (
                clean_ext is None or target.suffix == clean_ext
            ):
                files_to_search.append(target)
        else:
            for root, dirs, files in os.walk(target):
                # Filter directories in-place to respect ignores
                root_path = Path(root)
                dirs[:] = [d for d in dirs if not self._is_ignored(root_path / d, ignore_patterns)]
                for f in files:
                    file_p = root_path / f
                    if self._is_ignored(file_p, ignore_patterns):
                        continue
                    if clean_ext and file_p.suffix != clean_ext:
                        continue
                    files_to_search.append(file_p)

        matches: list[str] = []
        for file_path in files_to_search:
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
            except Exception:
                continue

            rel_file = file_path.relative_to(self.repo_dir).as_posix()
            total = len(lines)
            matched_indices = [idx for idx, line in enumerate(lines) if regex.search(line)]

            if not matched_indices:
                continue

            if context_lines <= 0:
                for idx in matched_indices:
                    matches.append(f"{rel_file}:{idx + 1}: {lines[idx]}")
            else:
                # Group matches with context lines
                emitted_indices: set[int] = set()
                for idx in matched_indices:
                    start_ctx = max(0, idx - context_lines)
                    end_ctx = min(total, idx + context_lines + 1)
                    for c_idx in range(start_ctx, end_ctx):
                        if c_idx not in emitted_indices:
                            sep = ":" if c_idx == idx else "-"
                            matches.append(f"{rel_file}{sep}{c_idx + 1}{sep} {lines[c_idx]}")
                            emitted_indices.add(c_idx)

        rel_target = (
            target.relative_to(self.repo_dir).as_posix() if target != self.repo_dir else "."
        )
        if not matches:
            return self._cap_output(f"No matches found for pattern '{pattern}' in '{rel_target}'")

        return self._cap_output(
            "\n".join(matches),
            truncation_note="[OUTPUT TRUNCATED: results truncated at limit]",
        )

    # -----------------------------------------------------------------------
    # Tool: edit
    # -----------------------------------------------------------------------

    def edit(
        self,
        path: str,
        old_str: str | None = None,
        new_str: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        new_code: str | None = None,
    ) -> ToolExecutionResult:
        """Edit file based on configured edit_format."""
        try:
            target = self._resolve_safe_path(path)
        except ValueError as err:
            return self._cap_output(f"Error: {err}", is_error=True)

        if not target.exists():
            return self._cap_output(f"Error: File '{path}' does not exist", is_error=True)
        if target.is_dir():
            return self._cap_output(f"Error: '{path}' is a directory, not a file", is_error=True)

        try:
            content = target.read_text(encoding="utf-8")
        except Exception as e:
            return self._cap_output(f"Error reading file '{path}': {e}", is_error=True)

        if self.edit_format == EditFormat.SEARCH_REPLACE:
            if old_str is None or new_str is None:
                return self._cap_output(
                    "Error: 'old_str' and 'new_str' required for search_replace edit format",
                    is_error=True,
                )

            count = content.count(old_str)
            if count == 0:
                return self._cap_output(
                    f"Error: Target 'old_str' not found in '{path}'", is_error=True
                )
            if count > 1:
                return self._cap_output(
                    f"Error: Target 'old_str' appears {count} times in '{path}'. Must be unique.",
                    is_error=True,
                )

            new_content = content.replace(old_str, new_str, 1)
            target.write_text(new_content, encoding="utf-8")
            return self._cap_output(f"Successfully replaced match in '{path}'")

        if self.edit_format == EditFormat.LINE_RANGE:
            if start_line is None or end_line is None or new_code is None:
                return self._cap_output(
                    "Error: 'start_line', 'end_line', and 'new_code' required for line_range edit",
                    is_error=True,
                )

            lines = content.splitlines(keepends=True)
            total = len(lines)
            if start_line < 1 or start_line > total:
                return self._cap_output(
                    f"Error: start_line {start_line} out of range [1, {total}] for '{path}'",
                    is_error=True,
                )
            if end_line < start_line or end_line > total:
                return self._cap_output(
                    f"Error: end_line {end_line} out of range [{start_line}, {total}] for '{path}'",
                    is_error=True,
                )

            replacement = new_code if new_code.endswith("\n") else new_code + "\n"
            new_lines = lines[: start_line - 1] + [replacement] + lines[end_line:]
            target.write_text("".join(new_lines), encoding="utf-8")
            return self._cap_output(
                f"Successfully replaced lines {start_line}-{end_line} in '{path}'"
            )

        return self._cap_output(
            f"Error: Unsupported edit format '{self.edit_format}'", is_error=True
        )

    # -----------------------------------------------------------------------
    # Tool: run
    # -----------------------------------------------------------------------

    def run(self, command: str) -> ToolExecutionResult:
        """Run a shell command inside the repository directory."""
        if not command.strip():
            return self._cap_output("Error: Empty command string provided", is_error=True)

        res = run_with_timeout(
            command,
            cwd=str(self.repo_dir),
            timeout_s=self.command_timeout_s,
            max_bytes=self.max_observation_bytes,
        )

        out_text = res.stdout.decode("utf-8", errors="replace")
        err_text = res.stderr.decode("utf-8", errors="replace")

        combined = []
        if out_text:
            combined.append(out_text)
        if err_text:
            combined.append(err_text)
        if res.killed:
            combined.append(f"[Command timed out after {self.command_timeout_s}s and was killed]")

        result_str = (
            "\n".join(combined) if combined else f"[Command exited with code {res.returncode}]"
        )
        is_err = res.returncode != 0 or res.killed
        capped = self._cap_output(result_str, is_error=is_err)
        if res.truncated:
            capped = capped.model_copy(
                update={
                    "truncated": True,
                    "output": capped.output + "\n[OUTPUT TRUNCATED: observation exceeded byte cap]"
                    if not capped.truncated
                    else capped.output,
                }
            )
        return capped

    # -----------------------------------------------------------------------
    # Tool: submit
    # -----------------------------------------------------------------------

    def submit(self, message: str | None = None) -> ToolExecutionResult:
        """Submit the solution and complete the task."""
        self.submitted = True
        self.submission_message = message
        msg = f"Task submitted successfully. {message or ''}".strip()
        return self._cap_output(msg)
