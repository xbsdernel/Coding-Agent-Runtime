"""Tests for chat-template rendering, prefix stability, and tool-call parsing."""

from __future__ import annotations

import json
import sys
import threading
import time
import urllib.request
from http.server import HTTPServer
from pathlib import Path

from codeagent.chat_template import (
    ChatMessage,
    ToolDefinition,
    apply_chat_template,
    check_prefix_stability,
    parse_tool_calls,
    tokenize_chatml,
)

# Add scripts directory to sys.path so mock_server can be imported
scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from mock_server import MockOpenAIHandler  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def test_prefix_stability_on_append():
    """Verify that appending a new turn preserves the exact prefix of previous turns."""
    messages_turn1 = [
        ChatMessage(role="system", content="You are a professional software engineer."),
        ChatMessage(role="user", content="Inspect the project repository layout."),
    ]
    # Render Turn 1 conversation (without trailing generation prompt for prefix comparison)
    rendered_turn1 = apply_chat_template(messages_turn1, add_generation_prompt=False)
    tokens_turn1 = tokenize_chatml(rendered_turn1)

    # Turn 2 appends assistant response and a new user follow-up
    messages_turn2 = list(messages_turn1) + [
        ChatMessage(
            role="assistant",
            content="I found the src/codeagent package layout with schemas and trace logger.",
        ),
        ChatMessage(role="user", content="Now run the unit test suite."),
    ]
    rendered_turn2 = apply_chat_template(messages_turn2, add_generation_prompt=False)
    tokens_turn2 = tokenize_chatml(rendered_turn2)

    # Prove prefix stability: tokens_turn2 starts with tokens_turn1 verbatim
    assert len(tokens_turn2) > len(tokens_turn1)
    assert check_prefix_stability(tokens_turn1, tokens_turn2) is True
    assert tokens_turn2[: len(tokens_turn1)] == tokens_turn1


def test_prefix_breakage_on_early_token_mutation():
    """Verify that altering an early token breaks prefix matching."""
    messages_original = [
        ChatMessage(
            role="system",
            content="You are an autonomous agent. Timestamp: 2026-11-23T14:00:00Z",
        ),
        ChatMessage(role="user", content="Task 1 description."),
    ]
    rendered_orig = apply_chat_template(messages_original, add_generation_prompt=False)
    tokens_orig = tokenize_chatml(rendered_orig)

    # Mutate early token in system prompt (e.g. wall-clock time changed between turns)
    messages_mutated = [
        ChatMessage(
            role="system",
            content="You are an autonomous agent. Timestamp: 2026-11-23T14:00:15Z",
        ),
        ChatMessage(role="user", content="Task 1 description."),
        ChatMessage(role="assistant", content="Completed Task 1."),
        ChatMessage(role="user", content="Task 2 description."),
    ]
    rendered_mutated = apply_chat_template(messages_mutated, add_generation_prompt=False)
    tokens_mutated = tokenize_chatml(rendered_mutated)

    # Prove prefix breakage
    assert check_prefix_stability(tokens_orig, tokens_mutated) is False
    assert tokens_mutated[: len(tokens_orig)] != tokens_orig


def test_tool_schema_rendering_and_parser():
    """Verify tool schema rendering and structured tool-call extraction."""
    tool = ToolDefinition(
        name="view_file",
        description="Read file contents within working directory.",
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    )

    messages = [
        ChatMessage(role="system", content="You are a coding assistant."),
        ChatMessage(role="user", content="Check src/codeagent/cli.py"),
    ]

    rendered = apply_chat_template(messages, tools=[tool], add_generation_prompt=True)

    # Verify tool schema is rendered deterministically in system block
    assert "view_file" in rendered
    assert "Read file contents within working directory." in rendered
    assert "<|im_start|>assistant\n" in rendered

    # Simulated assistant response emitting tool call
    model_response = (
        "I will inspect the file.\n"
        "<tool_call>\n"
        '{"name": "view_file", "arguments": {"path": "src/codeagent/cli.py"}}\n'
        "</tool_call>"
    )

    parsed_calls = parse_tool_calls(model_response)
    assert len(parsed_calls) == 1
    assert parsed_calls[0]["name"] == "view_file"
    assert parsed_calls[0]["arguments"] == {"path": "src/codeagent/cli.py"}


def test_server_cached_token_counter_confirms_both_cases():
    """Verify server reports cached tokens on stable append and zero on broken prefix."""
    port = 8925
    MockOpenAIHandler.last_prompt_repr = ""
    server = HTTPServer(("127.0.0.1", port), MockOpenAIHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.1)

    url = f"http://127.0.0.1:{port}/v1/chat/completions"

    def send_chat(msgs: list[dict[str, str]]) -> dict:
        data = json.dumps({"model": "test", "messages": msgs}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    try:
        # Turn 1: Cold start
        t1_msgs = [
            {"role": "system", "content": "You are a coding agent with static system prompt."},
            {"role": "user", "content": "Start episode 1."},
        ]
        resp1 = send_chat(t1_msgs)
        cached1 = resp1["usage"]["prompt_tokens_details"]["cached_tokens"]
        assert cached1 == 0  # Cold miss

        # Turn 2: Stable append
        t2_msgs = list(t1_msgs) + [
            {"role": "assistant", "content": "Ready for instructions."},
            {"role": "user", "content": "Run tests."},
        ]
        resp2 = send_chat(t2_msgs)
        cached2 = resp2["usage"]["prompt_tokens_details"]["cached_tokens"]
        assert cached2 > 0  # Cache hit confirmed by server

        # Turn 3: Deliberately broken prefix (altered system message)
        t3_msgs = [
            {"role": "system", "content": "MUTATED SYSTEM PROMPT: time is different now."},
            {"role": "user", "content": "Run tests."},
        ]
        resp3 = send_chat(t3_msgs)
        cached3 = resp3["usage"]["prompt_tokens_details"]["cached_tokens"]
        assert cached3 == 0  # Cache miss confirmed by server
    finally:
        server.shutdown()
        server.server_close()


def test_prefix_stability_report_documented():
    """Verify documentation artifact exists and covers both cases."""
    report = ROOT / "reports" / "prefix_stability.md"
    assert report.is_file(), f"Report not found at {report}"

    content = report.read_text(encoding="utf-8")
    assert "Prefix-Stable" in content
    assert "Broken" in content
    assert "tool_call" in content
