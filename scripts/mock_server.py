#!/usr/bin/env python3
"""scripts/mock_server.py — Lightweight OpenAI-compatible mock server for offline testing.

Provides mock endpoints for /health, /v1/models, and /v1/chat/completions (both
streaming and non-streaming) without requiring a GPU or large model weights.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


class MockOpenAIHandler(BaseHTTPRequestHandler):
    """Handles OpenAI-compatible API requests."""

    model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct"
    context_length: int = 32768
    last_prompt_repr: str = ""

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default stderr request logging."""
        sys.stdout.write(f"[{self.log_date_time_string()}] {format % args}\n")
        sys.stdout.flush()

    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path in ("/health", "/v1/health"):
            payload = {
                "status": "healthy",
                "engine": "mock",
                "model": self.model_name,
                "context_length": self.context_length,
                "prefix_caching": True,
            }
            self._send_json(200, payload)
        elif self.path in ("/v1/models", "/models"):
            payload = {
                "object": "list",
                "data": [
                    {
                        "id": self.model_name,
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "mock-runtime",
                        "permission": [],
                        "root": self.model_name,
                    }
                ],
            }
            self._send_json(200, payload)
        else:
            self._send_json(404, {"error": f"Path not found: {self.path}"})

    def do_POST(self) -> None:
        """Handle POST requests."""
        if self.path in ("/shutdown", "/v1/shutdown"):
            self._send_json(200, {"status": "shutting_down"})
            threading.Thread(target=self.server.shutdown).start()
            return

        if self.path not in ("/v1/chat/completions", "/chat/completions"):
            self._send_json(404, {"error": f"Path not found: {self.path}"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body"})
            return

        messages = body.get("messages", [])
        is_stream = bool(body.get("stream", False))
        model = body.get("model", self.model_name)

        # Build simulated reply based on prompt context
        user_prompt = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_prompt = m.get("content", "")
                break

        # Check for tool calling request
        tools = body.get("tools")
        if tools or "tool" in user_prompt.lower():
            tool_name = "view_file"
            if tools and isinstance(tools, list) and len(tools) > 0:
                first_tool = tools[0]
                tool_name = first_tool.get("function", {}).get(
                    "name", first_tool.get("name", "view_file")
                )
            response_text = (
                "I will execute the tool.\n<tool_call>\n"
                f'{{"name": "{tool_name}", "arguments": {{"path": "src/codeagent/cli.py"}}}}\n'
                "</tool_call>"
            )
        else:
            response_text = f"Mock response: Processed query regarding '{user_prompt[:40]}'."

        # Compute prefix cache hits by checking common prefix against last prompt
        full_prompt_repr = "|".join(f"{m.get('role')}:{m.get('content')}" for m in messages)
        cached_tokens = 0
        if MockOpenAIHandler.last_prompt_repr:
            # Measure common prefix length
            prefix_len = 0
            for c1, c2 in zip(MockOpenAIHandler.last_prompt_repr, full_prompt_repr, strict=False):
                if c1 == c2:
                    prefix_len += 1
                else:
                    break

            # If common prefix extends through early messages (e.g. >= 20 characters),
            # count cached tokens. If early character broke, cached_tokens is 0.
            if prefix_len >= 20:
                cached_tokens = max(1, len(full_prompt_repr[:prefix_len].split()))
            else:
                cached_tokens = 0

        MockOpenAIHandler.last_prompt_repr = full_prompt_repr

        if is_stream:
            self._send_sse_stream(model, response_text)
        else:
            prompt_tokens = max(1, len(user_prompt.split())) + 15
            completion_tokens = max(1, len(response_text.split()))
            payload = {
                "id": f"chatcmpl-mock-{int(time.time() * 1000)}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_text,
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                    "prompt_tokens_details": {"cached_tokens": cached_tokens},
                },
            }
            self._send_json(200, payload)

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        encoded = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_sse_stream(self, model: str, full_text: str) -> None:
        self.close_connection = True
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        words = full_text.split()
        req_id = f"chatcmpl-stream-{int(time.time() * 1000)}"

        for i, word in enumerate(words):
            chunk = {
                "id": req_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": word + " " if i < len(words) - 1 else word},
                        "finish_reason": None if i < len(words) - 1 else "stop",
                    }
                ],
            }
            line = f"data: {json.dumps(chunk)}\n\n".encode()
            self.wfile.write(line)
            self.wfile.flush()

        # Send terminal [DONE]
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


def run_server(host: str, port: int, model: str, context_length: int) -> None:
    """Run mock server until interrupted."""
    MockOpenAIHandler.model_name = model
    MockOpenAIHandler.context_length = context_length

    server = HTTPServer((host, port), MockOpenAIHandler)
    print(f"Mock OpenAI server listening on http://{host}:{port}")
    print(f"Model: {model} | Context Length: {context_length} | Prefix Caching: enabled")
    sys.stdout.flush()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("Mock server stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock OpenAI-compatible server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument(
        "--model", default="Qwen/Qwen2.5-Coder-7B-Instruct", help="Model name identifier"
    )
    parser.add_argument(
        "--context-length", type=int, default=32768, help="Simulated context length"
    )
    args = parser.parse_args()

    run_server(args.host, args.port, args.model, args.context_length)


if __name__ == "__main__":
    main()
