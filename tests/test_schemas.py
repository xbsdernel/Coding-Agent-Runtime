"""Round-trip serialisation tests for every frozen schema.

Each test verifies that model_dump → model_validate produces an
identical object, that the schema_version field is present, and
that invalid input is rejected loudly.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from codeagent.schemas import (
    BudgetSpec,
    EventKind,
    ExperimentConfig,
    ResultRow,
    StopReason,
    TraceEvent,
    content_hash,
    seed_all,
    stable_json,
)

# ---- Helpers ---------------------------------------------------------------


def _round_trip(model_cls, data: dict):
    """Serialise to dict and back; return the reconstructed instance."""
    obj = model_cls(**data)
    dumped = obj.model_dump(mode="json")
    reconstructed = model_cls.model_validate(dumped)
    return obj, reconstructed


# ---- TraceEvent ------------------------------------------------------------


TRACE_EVENT_DATA = {
    "run_id": "run-001",
    "step": 0,
    "kind": EventKind.model_request,
    "timestamp": datetime(2026, 1, 1, tzinfo=UTC),
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "cached_tokens": 80,
    "duration_ms": 123.4,
    "content_hash": "abc123",
    "payload": {"messages": [{"role": "user", "content": "hello"}]},
}


class TestTraceEvent:
    def test_round_trip(self):
        original, restored = _round_trip(TraceEvent, TRACE_EVENT_DATA)
        assert original == restored

    def test_schema_version_present(self):
        obj = TraceEvent(**TRACE_EVENT_DATA)
        assert obj.schema_version == 1

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            TraceEvent(**{**TRACE_EVENT_DATA, "bogus_field": 42})

    def test_negative_tokens_rejected(self):
        with pytest.raises(ValidationError):
            TraceEvent(**{**TRACE_EVENT_DATA, "prompt_tokens": -1})

    def test_missing_required_field(self):
        incomplete = {k: v for k, v in TRACE_EVENT_DATA.items() if k != "run_id"}
        with pytest.raises(ValidationError):
            TraceEvent(**incomplete)


# ---- ExperimentConfig ------------------------------------------------------

CONFIG_DATA = {
    "experiment_id": "exp-001",
    "model_name": "qwen-coder-7b",
    "temperature": 0.2,
    "seed": 42,
    "max_steps": 30,
    "max_tokens": 100_000,
    "max_wallclock_s": 600.0,
    "max_cost_usd": 5.0,
    "git_commit": "abc1234",
}


class TestExperimentConfig:
    def test_round_trip(self):
        original, restored = _round_trip(ExperimentConfig, CONFIG_DATA)
        assert original == restored

    def test_schema_version_present(self):
        obj = ExperimentConfig(**CONFIG_DATA)
        assert obj.schema_version == 1

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            ExperimentConfig(**{**CONFIG_DATA, "bogus": True})

    def test_temperature_out_of_range(self):
        with pytest.raises(ValidationError):
            ExperimentConfig(**{**CONFIG_DATA, "temperature": 3.0})

    def test_config_hash_deterministic(self):
        a = ExperimentConfig(**CONFIG_DATA)
        b = ExperimentConfig(**CONFIG_DATA)
        assert a.compute_hash() == b.compute_hash()
        assert len(a.compute_hash()) == 64  # SHA-256 hex

    def test_config_hash_changes_on_field_change(self):
        a = ExperimentConfig(**CONFIG_DATA)
        b = ExperimentConfig(**{**CONFIG_DATA, "temperature": 0.5})
        assert a.compute_hash() != b.compute_hash()


# ---- ResultRow -------------------------------------------------------------

RESULT_DATA = {
    "task_id": "task-42",
    "arm": "baseline",
    "seed": 1,
    "outcome": "pass",
    "prompt_tokens": 5000,
    "cached_tokens": 4000,
    "completion_tokens": 500,
    "cost_usd": 0.01,
    "wallclock_s": 120.0,
    "stop_reason": StopReason.submitted,
    "tamper_flag": False,
    "manifest_id": "manifest-v1",
    "git_commit": "abc1234",
    "config_hash": "deadbeef",
}


class TestResultRow:
    def test_round_trip(self):
        original, restored = _round_trip(ResultRow, RESULT_DATA)
        assert original == restored

    def test_schema_version_present(self):
        obj = ResultRow(**RESULT_DATA)
        assert obj.schema_version == 1

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            ResultRow(**{**RESULT_DATA, "bogus": 1})

    def test_missing_manifest_rejected(self):
        bad = {**RESULT_DATA, "manifest_id": ""}
        with pytest.raises(ValidationError):
            ResultRow(**bad)

    def test_negative_cost_rejected(self):
        with pytest.raises(ValidationError):
            ResultRow(**{**RESULT_DATA, "cost_usd": -0.5})


# ---- BudgetSpec ------------------------------------------------------------

BUDGET_DATA = {
    "max_steps": 30,
    "max_tokens": 100_000,
    "max_wallclock_s": 600.0,
    "max_cost_usd": 5.0,
}


class TestBudgetSpec:
    def test_round_trip(self):
        original, restored = _round_trip(BudgetSpec, BUDGET_DATA)
        assert original == restored

    def test_schema_version_present(self):
        obj = BudgetSpec(**BUDGET_DATA)
        assert obj.schema_version == 1

    def test_extra_field_rejected(self):
        with pytest.raises(ValidationError):
            BudgetSpec(**{**BUDGET_DATA, "bogus": True})

    def test_zero_steps_rejected(self):
        with pytest.raises(ValidationError):
            BudgetSpec(**{**BUDGET_DATA, "max_steps": 0})

    def test_stall_window_default(self):
        obj = BudgetSpec(**BUDGET_DATA)
        assert obj.stall_window == 3
        assert obj.stall_action == "warn_then_stop"


# ---- Utility functions -----------------------------------------------------


class TestUtilities:
    def test_content_hash_deterministic(self):
        assert content_hash("hello") == content_hash("hello")
        assert content_hash("hello") != content_hash("world")
        assert len(content_hash("hello")) == 64

    def test_stable_json_sorted(self):
        a = stable_json({"b": 2, "a": 1})
        b = stable_json({"a": 1, "b": 2})
        assert a == b
        parsed = json.loads(a)
        assert list(parsed.keys()) == ["a", "b"]

    def test_seed_all_deterministic(self):
        import random

        seed_all(42)
        seq1 = [random.random() for _ in range(5)]
        seed_all(42)
        seq2 = [random.random() for _ in range(5)]
        assert seq1 == seq2
