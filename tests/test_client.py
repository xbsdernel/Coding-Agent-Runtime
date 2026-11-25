"""Tests for :mod:`codeagent.client` with fake-server fault injection."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import httpx
import pytest

from codeagent.client import (
    AsyncChatClient,
    ChatClientError,
    ChatClientTimeoutError,
    ClientTimeoutConfig,
    RetryConfig,
)
from codeagent.schemas import EventKind
from codeagent.trace import TraceReader, TraceWriter


class FaultInjectingTransport(httpx.AsyncBaseTransport):
    """Custom httpx transport that injects delays, errors, 429s, or dropped connections."""

    def __init__(
        self,
        *,
        delay_s: float = 0.0,
        inject_429_count: int = 0,
        inject_500_count: int = 0,
        drop_connection_count: int = 0,
        success_response: dict[str, Any] | None = None,
    ) -> None:
        self.delay_s = delay_s
        self.inject_429_count = inject_429_count
        self.inject_500_count = inject_500_count
        self.drop_connection_count = drop_connection_count
        self.request_count = 0
        self.success_response = success_response or {
            "id": "chatcmpl-test-123",
            "object": "chat.completion",
            "choices": [{"message": {"role": "assistant", "content": "Hello world"}}],
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 5,
                "prompt_tokens_details": {"cached_tokens": 10},
            },
        }

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.request_count += 1

        if self.delay_s > 0:
            await asyncio.sleep(self.delay_s)

        if self.drop_connection_count > 0:
            self.drop_connection_count -= 1
            raise httpx.ConnectError("Connection dropped by peer", request=request)

        if self.inject_429_count > 0:
            self.inject_429_count -= 1
            return httpx.Response(
                status_code=429,
                json={"error": {"message": "Rate limit reached", "type": "rate_limit_error"}},
                request=request,
            )

        if self.inject_500_count > 0:
            self.inject_500_count -= 1
            return httpx.Response(
                status_code=500,
                json={"error": {"message": "Internal server error"}},
                request=request,
            )

        return httpx.Response(
            status_code=200,
            json=self.success_response,
            request=request,
        )


@pytest.mark.asyncio
async def test_successful_request(tmp_path: Path):
    """Happy path: response succeeds and is logged to trace."""
    trace_path = tmp_path / "trace.jsonl"
    transport = FaultInjectingTransport()

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as raw_client:
        with TraceWriter(trace_path) as tw:
            client = AsyncChatClient(
                client=raw_client,
                trace_writer=tw,
            )
            req = {"model": "test-model", "messages": [{"role": "user", "content": "Hi"}]}
            res = await client.post_chat_completion(req, run_id="run-001", step=1)
            assert res["id"] == "chatcmpl-test-123"

    events = list(TraceReader(trace_path).iter_events())
    assert len(events) == 2
    assert events[0].kind == EventKind.model_request
    assert events[0].run_id == "run-001"
    assert events[1].kind == EventKind.model_response
    assert events[1].prompt_tokens == 15
    assert events[1].completion_tokens == 5
    assert events[1].cached_tokens == 10


@pytest.mark.asyncio
async def test_retry_on_429_then_succeed(tmp_path: Path):
    """Fake server returns 429 twice, then succeeds on 3rd attempt."""
    trace_path = tmp_path / "trace_429.jsonl"
    transport = FaultInjectingTransport(inject_429_count=2)

    retry_cfg = RetryConfig(max_retries=3, base_delay_s=0.01, jitter=False)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as raw_client:
        with TraceWriter(trace_path) as tw:
            client = AsyncChatClient(
                client=raw_client,
                retry_config=retry_cfg,
                trace_writer=tw,
            )
            req = {"model": "test-model", "messages": [{"role": "user", "content": "Hi"}]}
            res = await client.post_chat_completion(req, run_id="run-429", step=2)
            assert res["id"] == "chatcmpl-test-123"
            assert transport.request_count == 3

    events = list(TraceReader(trace_path).iter_events())
    # 3 requests, 2 errors (429), 1 success = 6 events
    assert len(events) == 6
    kinds = [e.kind for e in events]
    assert kinds.count(EventKind.model_request) == 3
    assert kinds.count(EventKind.error) == 2
    assert kinds.count(EventKind.model_response) == 1


@pytest.mark.asyncio
async def test_retry_on_dropped_connection(tmp_path: Path):
    """Fake server drops connection once, client retries and succeeds."""
    trace_path = tmp_path / "trace_drop.jsonl"
    transport = FaultInjectingTransport(drop_connection_count=1)
    retry_cfg = RetryConfig(max_retries=2, base_delay_s=0.01, jitter=False)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as raw_client:
        with TraceWriter(trace_path) as tw:
            client = AsyncChatClient(
                client=raw_client,
                retry_config=retry_cfg,
                trace_writer=tw,
            )
            req = {"model": "test-model", "messages": [{"role": "user", "content": "Hi"}]}
            res = await client.post_chat_completion(req, run_id="run-drop", step=3)
            assert res["id"] == "chatcmpl-test-123"
            assert transport.request_count == 2

    events = list(TraceReader(trace_path).iter_events())
    assert len(events) == 4
    assert events[1].kind == EventKind.error
    assert "dropped" in events[1].payload.get("error", "")


@pytest.mark.asyncio
async def test_exceed_max_retries(tmp_path: Path):
    """Fake server always returns 500; client stops after max_retries."""
    trace_path = tmp_path / "trace_500.jsonl"
    transport = FaultInjectingTransport(inject_500_count=10)
    retry_cfg = RetryConfig(max_retries=2, base_delay_s=0.01, jitter=False)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as raw_client:
        with TraceWriter(trace_path) as tw:
            client = AsyncChatClient(
                client=raw_client,
                retry_config=retry_cfg,
                trace_writer=tw,
            )
            req = {"model": "test-model", "messages": [{"role": "user", "content": "Hi"}]}
            with pytest.raises(ChatClientError) as exc_info:
                await client.post_chat_completion(req, run_id="run-fail", step=4)
            assert "HTTP 500" in str(exc_info.value)
            assert transport.request_count == 3  # initial + 2 retries

    events = list(TraceReader(trace_path).iter_events())
    assert len(events) == 6
    assert all(e.kind in (EventKind.model_request, EventKind.error) for e in events)


@pytest.mark.asyncio
async def test_overall_deadline_exceeded(tmp_path: Path):
    """Slow server triggers overall deadline timeout."""
    trace_path = tmp_path / "trace_deadline.jsonl"
    transport = FaultInjectingTransport(delay_s=0.3)
    timeout_cfg = ClientTimeoutConfig(overall_deadline_s=0.15, read_s=5.0)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as raw_client:
        with TraceWriter(trace_path) as tw:
            client = AsyncChatClient(
                client=raw_client,
                timeout_config=timeout_cfg,
                trace_writer=tw,
            )
            req = {"model": "test-model", "messages": [{"role": "user", "content": "Hi"}]}
            with pytest.raises(ChatClientTimeoutError) as exc_info:
                await client.post_chat_completion(req, run_id="run-deadline", step=5)
            assert "deadline" in str(exc_info.value).lower()

    events = list(TraceReader(trace_path).iter_events())
    assert any(
        e.kind == EventKind.error and "timeout" in e.payload.get("error", "").lower()
        for e in events
    )


@pytest.mark.asyncio
async def test_cancellation_cleanup():
    """Canceling a running in-flight request closes cleanly without socket leaks."""
    transport = FaultInjectingTransport(delay_s=2.0)
    timeout_cfg = ClientTimeoutConfig(overall_deadline_s=10.0, read_s=5.0)

    async with AsyncChatClient(base_url="http://test", timeout_config=timeout_cfg) as client:
        # replace client._client transport for testing
        client._client = httpx.AsyncClient(transport=transport, base_url="http://test")

        task = asyncio.create_task(
            client.post_chat_completion(
                {"model": "test", "messages": []},
                run_id="run-cancel",
            )
        )
        await asyncio.sleep(0.05)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

    # Assert client closed properly
    assert client._client.is_closed
