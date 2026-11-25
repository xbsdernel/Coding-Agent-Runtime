"""Async HTTP client wrapper for chat completions with timeouts, retries, and tracing.

Provides :class:`AsyncChatClient`, a robust wrapper around :class:`httpx.AsyncClient`
with fine-grained timeout controls, exponential back-off with jitter, deadline
enforcement, and automatic logging of all attempts to a :class:`TraceWriter`.
"""

from __future__ import annotations

import asyncio
import contextlib
import random
import time
from typing import TYPE_CHECKING, Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

from codeagent.schemas import EventKind

if TYPE_CHECKING:
    from codeagent.trace import TraceWriter

__all__ = [
    "AsyncChatClient",
    "ChatClientError",
    "ChatClientTimeoutError",
    "ClientTimeoutConfig",
    "RetryConfig",
]


class ChatClientError(Exception):
    """Base error raised by AsyncChatClient."""


class ChatClientTimeoutError(ChatClientError):
    """Raised when an overall deadline or request timeout is exceeded."""


class ClientTimeoutConfig(BaseModel):
    """Fine-grained timeout parameters for HTTP requests."""

    model_config = ConfigDict(extra="forbid")

    connect_s: float = Field(default=5.0, ge=0.0, description="Socket connect timeout.")
    read_s: float = Field(default=30.0, ge=0.0, description="Socket read timeout.")
    write_s: float = Field(default=10.0, ge=0.0, description="Socket write timeout.")
    pool_s: float = Field(default=5.0, ge=0.0, description="Pool connection acquisition timeout.")
    overall_deadline_s: float = Field(
        default=60.0,
        gt=0.0,
        description="Overall wall-clock deadline spanning all retry attempts.",
    )

    def to_httpx_timeout(self) -> httpx.Timeout:
        """Convert individual timeouts to httpx.Timeout."""
        return httpx.Timeout(
            connect=self.connect_s,
            read=self.read_s,
            write=self.write_s,
            pool=self.pool_s,
        )


class RetryConfig(BaseModel):
    """Parameters for exponential back-off retry loop."""

    model_config = ConfigDict(extra="forbid")

    max_retries: int = Field(default=3, ge=0, description="Max retry attempts after initial try.")
    base_delay_s: float = Field(default=0.5, ge=0.0, description="Initial back-off delay.")
    max_delay_s: float = Field(default=10.0, ge=0.0, description="Ceiling for back-off delay.")
    jitter: bool = Field(default=True, description="Add random jitter to retry delay.")
    retry_status_codes: list[int] = Field(
        default_factory=lambda: [429, 500, 502, 503, 504],
        description="HTTP status codes that trigger a retry.",
    )

    def compute_delay(self, attempt: int) -> float:
        """Compute exponential back-off delay with optional uniform jitter."""
        delay = float(min(self.max_delay_s, self.base_delay_s * (2**attempt)))
        if self.jitter and delay > 0:
            delay = float(random.uniform(0.5 * delay, delay))
        return delay


class AsyncChatClient:
    """Async client wrapper for model server endpoints."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        *,
        timeout_config: ClientTimeoutConfig | None = None,
        retry_config: RetryConfig | None = None,
        trace_writer: TraceWriter | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_config = timeout_config or ClientTimeoutConfig()
        self.retry_config = retry_config or RetryConfig()
        self.trace_writer = trace_writer
        self._external_client = client is not None
        self._client = client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout_config.to_httpx_timeout(),
        )

    async def __aenter__(self) -> AsyncChatClient:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client session if owned."""
        if not self._external_client and not self._client.is_closed:
            await self._client.aclose()

    def _log_trace(
        self,
        run_id: str | None,
        step: int,
        kind: EventKind | str,
        payload: dict[str, Any],
        duration_ms: float = 0.0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cached_tokens: int = 0,
    ) -> None:
        """Log event to trace_writer if one is configured."""
        if self.trace_writer is None or not run_id:
            return
        with contextlib.suppress(Exception):
            self.trace_writer.log(
                run_id=run_id,
                step=step,
                kind=kind,
                payload=payload,
                duration_ms=duration_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cached_tokens=cached_tokens,
            )

    async def post_chat_completion(
        self,
        request: dict[str, Any],
        *,
        run_id: str | None = None,
        step: int = 0,
        endpoint: str = "/v1/chat/completions",
    ) -> dict[str, Any]:
        """Send chat completion request with deadline enforcement and retries."""
        deadline = time.monotonic() + self.timeout_config.overall_deadline_s
        attempt = 0
        last_error: Exception | None = None

        while True:
            remaining_time = deadline - time.monotonic()
            if remaining_time <= 0:
                msg = f"Overall deadline of {self.timeout_config.overall_deadline_s}s exceeded"
                self._log_trace(
                    run_id=run_id,
                    step=step,
                    kind=EventKind.error,
                    payload={"error": msg, "attempt": attempt, "stage": "deadline_check"},
                )
                raise ChatClientTimeoutError(msg) from last_error

            current_timeout = httpx.Timeout(
                connect=min(self.timeout_config.connect_s, remaining_time),
                read=min(self.timeout_config.read_s, remaining_time),
                write=min(self.timeout_config.write_s, remaining_time),
                pool=min(self.timeout_config.pool_s, remaining_time),
            )

            t0 = time.monotonic()
            self._log_trace(
                run_id=run_id,
                step=step,
                kind=EventKind.model_request,
                payload={
                    "attempt": attempt,
                    "endpoint": endpoint,
                    "model": request.get("model", ""),
                    "messages_count": len(request.get("messages", [])),
                },
            )

            try:
                response = await asyncio.wait_for(
                    self._client.post(
                        endpoint,
                        json=request,
                        timeout=current_timeout,
                    ),
                    timeout=remaining_time,
                )
                duration_ms = (time.monotonic() - t0) * 1000.0

                if response.status_code in self.retry_config.retry_status_codes:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    self._log_trace(
                        run_id=run_id,
                        step=step,
                        kind=EventKind.error,
                        payload={
                            "attempt": attempt,
                            "status_code": response.status_code,
                            "error": error_msg,
                        },
                        duration_ms=duration_ms,
                    )
                    last_error = ChatClientError(error_msg)
                else:
                    response.raise_for_status()
                    data: dict[str, Any] = response.json()
                    usage = data.get("usage", {})
                    self._log_trace(
                        run_id=run_id,
                        step=step,
                        kind=EventKind.model_response,
                        payload={
                            "attempt": attempt,
                            "status_code": response.status_code,
                            "id": data.get("id", ""),
                        },
                        duration_ms=duration_ms,
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                        cached_tokens=usage.get("prompt_tokens_details", {}).get(
                            "cached_tokens", 0
                        ),
                    )
                    return data

            except (httpx.TimeoutException, TimeoutError) as exc:
                duration_ms = (time.monotonic() - t0) * 1000.0
                error_msg = f"Request timeout: {exc}"
                self._log_trace(
                    run_id=run_id,
                    step=step,
                    kind=EventKind.error,
                    payload={"attempt": attempt, "error": error_msg, "exception": str(type(exc))},
                    duration_ms=duration_ms,
                )
                err_timeout = ChatClientTimeoutError(error_msg)
                err_timeout.__cause__ = exc
                last_error = err_timeout

            except (httpx.NetworkError, httpx.HTTPStatusError) as exc:
                duration_ms = (time.monotonic() - t0) * 1000.0
                error_msg = f"HTTP/Network error: {exc}"
                self._log_trace(
                    run_id=run_id,
                    step=step,
                    kind=EventKind.error,
                    payload={"attempt": attempt, "error": error_msg, "exception": str(type(exc))},
                    duration_ms=duration_ms,
                )
                err_network = ChatClientError(error_msg)
                err_network.__cause__ = exc
                last_error = err_network

            # Check if we can retry
            if attempt >= self.retry_config.max_retries:
                raise last_error or ChatClientError("Request failed after retries")

            delay = self.retry_config.compute_delay(attempt)
            # Ensure delay doesn't overshoot remaining deadline
            time_left = deadline - time.monotonic()
            if time_left <= 0:
                raise ChatClientTimeoutError(
                    f"Overall deadline of {self.timeout_config.overall_deadline_s}s exceeded"
                ) from last_error

            delay = min(delay, max(0.0, time_left))
            await asyncio.sleep(delay)
            attempt += 1
