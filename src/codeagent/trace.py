"""Append-only JSONL trace logger and reader.

Implements structured telemetry for agent episodes conforming to
OpenTelemetry GenAI semantic conventions and the frozen TraceEvent schema.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from codeagent.schemas import EventKind, TraceEvent, content_hash, stable_json


class TraceWriter:
    """Append-only JSONL event stream writer."""

    def __init__(self, path: Path | str, require_hash: bool = True) -> None:
        self.path = Path(path)
        self.require_hash = require_hash
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Open file in append mode with explicit utf-8 encoding
        self._file = open(self.path, "a", encoding="utf-8")  # noqa: SIM115

    def __enter__(self) -> TraceWriter:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close underlying file descriptor."""
        if not self._file.closed:
            self._file.flush()
            self._file.close()

    def write(self, event: TraceEvent) -> None:
        """Append a validated TraceEvent to the trace file."""
        if self.require_hash and not event.content_hash:
            raise ValueError(
                f"TraceEvent step={event.step} kind={event.kind} missing required content_hash."
            )
        line = event.model_dump_json()
        self._file.write(line + "\n")
        self._file.flush()

    def log(
        self,
        run_id: str,
        step: int,
        kind: EventKind | str,
        payload: dict[str, Any] | None = None,
        *,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cached_tokens: int = 0,
        duration_ms: float = 0.0,
        content_hash_override: str | None = None,
    ) -> TraceEvent:
        """Create, hash, validate, and write a TraceEvent."""
        p = payload or {}
        chash = content_hash_override or content_hash(stable_json(p))
        k = EventKind(kind) if isinstance(kind, str) else kind
        event = TraceEvent(
            run_id=run_id,
            step=step,
            kind=k,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached_tokens=cached_tokens,
            duration_ms=duration_ms,
            content_hash=chash,
            payload=p,
        )
        self.write(event)
        return event


class TraceReader:
    """Reader and aggregator for append-only JSONL trace files."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Trace file does not exist: {self.path}")

    def iter_events(self) -> Iterator[TraceEvent]:
        """Stream validated TraceEvents line-by-line."""
        with open(self.path, encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                raw = line.strip()
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                    yield TraceEvent.model_validate(data)
                except (json.JSONDecodeError, ValidationError) as e:
                    msg = f"Malformed trace event at line {line_no} in {self.path}: {e}"
                    raise ValueError(msg) from e

    def events(self) -> list[TraceEvent]:
        """Read all events into memory."""
        return list(self.iter_events())

    def total_prompt_tokens(self) -> int:
        """Recompute cumulative prompt tokens from events."""
        return sum(e.prompt_tokens for e in self.iter_events())

    def total_completion_tokens(self) -> int:
        """Recompute cumulative completion tokens from events."""
        return sum(e.completion_tokens for e in self.iter_events())

    def total_cached_tokens(self) -> int:
        """Recompute cumulative cached tokens from events."""
        return sum(e.cached_tokens for e in self.iter_events())

    def total_duration_ms(self) -> float:
        """Recompute cumulative duration in ms."""
        return sum(e.duration_ms for e in self.iter_events())

    def token_summary(self) -> dict[str, int]:
        """Return aggregated token metrics."""
        prompt = self.total_prompt_tokens()
        completion = self.total_completion_tokens()
        cached = self.total_cached_tokens()
        return {
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "cached_tokens": cached,
            "total_tokens": prompt + completion,
        }

    def timeline(self) -> list[dict[str, Any]]:
        """Return a simplified event timeline."""
        return [
            {
                "step": e.step,
                "timestamp": e.timestamp.isoformat(),
                "kind": e.kind.value,
                "prompt_tokens": e.prompt_tokens,
                "completion_tokens": e.completion_tokens,
                "cached_tokens": e.cached_tokens,
                "duration_ms": e.duration_ms,
            }
            for e in self.iter_events()
        ]
