"""Core Pydantic schemas for frozen interfaces.

Every schema carries a ``schema_version`` field so that serialised
records remain identifiable across upgrades.  Validation is strict:
extra fields are forbidden and bad input fails loudly.
"""

from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_RNG_SEED: int = 42


def seed_all(seed: int = _RNG_SEED) -> None:
    """Seed Python stdlib RNG for deterministic runs."""
    random.seed(seed)


def content_hash(data: str) -> str:
    """Return a stable SHA-256 hex digest of *data*."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def stable_json(obj: Any) -> str:
    """Serialise *obj* to JSON with sorted keys for deterministic hashing."""
    return json.dumps(obj, sort_keys=True, default=str)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class StopReason(str, Enum):
    """Why an episode ended."""

    submitted = "submitted"
    budget_steps = "budget_steps"
    budget_tokens = "budget_tokens"
    budget_wallclock = "budget_wallclock"
    budget_cost = "budget_cost"
    stalled = "stalled"
    errored = "errored"
    unfinished = "unfinished"


class EventKind(str, Enum):
    """Discriminator for trace events."""

    model_request = "model_request"
    model_response = "model_response"
    tool_call = "tool_call"
    tool_result = "tool_result"
    state_change = "state_change"
    plan = "plan"
    error = "error"


# ---------------------------------------------------------------------------
# 1. TraceEvent
# ---------------------------------------------------------------------------


class TraceEvent(BaseModel):
    """A single entry in the append-only JSONL event log.

    One event per model call, tool call or state change.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=1, frozen=True)
    run_id: str = Field(..., description="Unique identifier for this run / episode.")
    step: int = Field(..., ge=0, description="Zero-based step counter within the run.")
    kind: EventKind
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC wall-clock time of the event.",
    )
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    cached_tokens: int = Field(default=0, ge=0)
    duration_ms: float = Field(default=0.0, ge=0.0)
    content_hash: str = Field(
        default="",
        description="SHA-256 of the payload (request or response body).",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary event-specific data (request, response, args …).",
    )


# ---------------------------------------------------------------------------
# 2. ExperimentConfig
# ---------------------------------------------------------------------------


class ExperimentConfig(BaseModel):
    """Immutable experiment configuration snapshotted before every run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=1, frozen=True)
    experiment_id: str = Field(..., description="Human-readable experiment name.")
    model_name: str = Field(..., description="Served model identifier.")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, gt=0.0, le=1.0)
    top_k: int = Field(default=-1, description="-1 means disabled.")
    seed: int | None = Field(default=None, description="Per-request RNG seed.")
    max_steps: int = Field(default=30, gt=0)
    max_tokens: int = Field(default=100_000, gt=0)
    max_wallclock_s: float = Field(default=600.0, gt=0.0)
    max_cost_usd: float = Field(default=5.0, gt=0.0)
    context_policy: str = Field(default="full_history")
    edit_format: str = Field(default="search_replace")
    tools_enabled: list[str] = Field(default_factory=lambda: ["view", "search", "edit", "run", "submit"])
    hooks_enabled: list[str] = Field(default_factory=list)
    git_commit: str = Field(default="", description="HEAD SHA at launch time.")
    config_hash: str = Field(default="", description="SHA-256 of this config's stable JSON.")

    def compute_hash(self) -> str:
        """Compute and return the config hash from all fields except config_hash itself."""
        d = self.model_dump(exclude={"config_hash"})
        h = content_hash(stable_json(d))
        return h


# ---------------------------------------------------------------------------
# 3. ResultRow
# ---------------------------------------------------------------------------


class ResultRow(BaseModel):
    """One row per episode in the columnar result store."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=1, frozen=True)
    task_id: str
    arm: str = Field(..., description="Experimental arm / configuration label.")
    seed: int
    outcome: str = Field(..., description="pass | fail | error")
    prompt_tokens: int = Field(default=0, ge=0)
    cached_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0.0)
    wallclock_s: float = Field(default=0.0, ge=0.0)
    stop_reason: StopReason
    tamper_flag: bool = Field(default=False)
    manifest_id: str = Field(..., min_length=1, description="ID linking to the task-set manifest.")
    git_commit: str = Field(default="")
    config_hash: str = Field(default="")


# ---------------------------------------------------------------------------
# 4. BudgetSpec
# ---------------------------------------------------------------------------


class BudgetSpec(BaseModel):
    """Budget limits enforced by the agent loop for a single episode."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=1, frozen=True)
    max_steps: int = Field(..., gt=0, description="Maximum ReAct steps per episode.")
    max_tokens: int = Field(..., gt=0, description="Cumulative prompt + completion tokens.")
    max_wallclock_s: float = Field(..., gt=0.0, description="Wall-clock seconds.")
    max_cost_usd: float = Field(..., gt=0.0, description="Estimated cost ceiling in USD.")
    stall_window: int = Field(
        default=3,
        gt=0,
        description="Number of consecutive identical actions before stall detection fires.",
    )
    stall_action: str = Field(
        default="warn_then_stop",
        description="Policy when a stall is detected: warn_then_stop | stop_immediately.",
    )
