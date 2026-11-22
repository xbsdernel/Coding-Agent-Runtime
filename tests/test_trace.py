"""Tests for append-only JSONL TraceWriter and TraceReader."""

from __future__ import annotations

from pathlib import Path

import pytest

from codeagent.schemas import EventKind, TraceEvent
from codeagent.trace import TraceReader, TraceWriter


def test_20_event_round_trip_and_aggregates(tmp_path: Path):
    trace_path = tmp_path / "episode_001.jsonl"
    run_id = "test-run-42"

    expected_prompt_tokens = 0
    expected_completion_tokens = 0
    expected_cached_tokens = 0
    expected_duration_ms = 0.0

    # Write 20 synthetic events alternating across kinds
    kinds = [
        EventKind.model_request,
        EventKind.model_response,
        EventKind.tool_call,
        EventKind.tool_result,
        EventKind.state_change,
    ]

    with TraceWriter(trace_path) as writer:
        for step in range(20):
            kind = kinds[step % len(kinds)]
            prompt = (
                100 + step * 10
                if kind in (EventKind.model_request, EventKind.model_response)
                else 0
            )
            completion = 50 + step * 2 if kind == EventKind.model_response else 0
            cached = 80 if kind in (EventKind.model_request, EventKind.model_response) else 0
            dur = 15.5 * (step + 1)

            expected_prompt_tokens += prompt
            expected_completion_tokens += completion
            expected_cached_tokens += cached
            expected_duration_ms += dur

            writer.log(
                run_id=run_id,
                step=step,
                kind=kind,
                payload={"turn": step, "data": f"content-step-{step}"},
                prompt_tokens=prompt,
                completion_tokens=completion,
                cached_tokens=cached,
                duration_ms=dur,
            )

    assert trace_path.exists()
    reader = TraceReader(trace_path)
    events = reader.events()

    # Verify count and round-trip fidelity
    assert len(events) == 20
    for idx, event in enumerate(events):
        assert event.run_id == run_id
        assert event.step == idx
        assert event.kind == kinds[idx % len(kinds)]
        assert len(event.content_hash) == 64
        assert event.payload["turn"] == idx

    # Verify aggregates match exact calculated values
    assert reader.total_prompt_tokens() == expected_prompt_tokens
    assert reader.total_completion_tokens() == expected_completion_tokens
    assert reader.total_cached_tokens() == expected_cached_tokens
    assert reader.total_duration_ms() == pytest.approx(expected_duration_ms, 1e-4)

    summary = reader.token_summary()
    assert summary["prompt_tokens"] == expected_prompt_tokens
    assert summary["completion_tokens"] == expected_completion_tokens
    assert summary["cached_tokens"] == expected_cached_tokens
    assert summary["total_tokens"] == expected_prompt_tokens + expected_completion_tokens

    timeline = reader.timeline()
    assert len(timeline) == 20
    assert timeline[0]["step"] == 0
    assert timeline[19]["step"] == 19


def test_rejects_unhashed_events(tmp_path: Path):
    trace_path = tmp_path / "unhashed.jsonl"
    writer = TraceWriter(trace_path, require_hash=True)

    unhashed_event = TraceEvent(
        run_id="run-1",
        step=0,
        kind=EventKind.state_change,
        content_hash="",  # Empty hash
        payload={"msg": "state"},
    )

    with pytest.raises(ValueError, match="missing required content_hash"):
        writer.write(unhashed_event)
    writer.close()


def test_reader_rejects_malformed_json(tmp_path: Path):
    bad_trace = tmp_path / "bad.jsonl"
    bad_trace.write_text("not a valid json line\n", encoding="utf-8")

    reader = TraceReader(bad_trace)
    with pytest.raises(ValueError, match="Malformed trace event"):
        list(reader.iter_events())


def test_reader_rejects_schema_invalid_event(tmp_path: Path):
    invalid_trace = tmp_path / "invalid_schema.jsonl"
    # Negative step index or missing run_id violates TraceEvent schema
    invalid_trace.write_text('{"step": -5, "kind": "plan"}\n', encoding="utf-8")

    reader = TraceReader(invalid_trace)
    with pytest.raises(ValueError, match="Malformed trace event"):
        list(reader.iter_events())


def test_reader_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        TraceReader("does_not_exist.jsonl")
