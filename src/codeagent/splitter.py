"""Contamination-aware task splitting relative to model training cutoff.

Separates benchmark tasks into ``training`` (pre-cutoff), ``dev`` (post-cutoff),
and ``main`` (post-cutoff) splits, recording the assignment in a reproducible
manifest protected by a deterministic SHA-256 content hash.
"""

from __future__ import annotations

import json
import random
from collections.abc import Sequence
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from codeagent.schemas import content_hash, stable_json

# ---------------------------------------------------------------------------
# Constants & Types
# ---------------------------------------------------------------------------

DEFAULT_MODEL_NAME = "Qwen/Qwen2.5-Coder-7B-Instruct"
DEFAULT_CUTOFF_DATE = datetime(2024, 9, 1, tzinfo=UTC)

MODEL_CUTOFF_DATES: dict[str, datetime] = {
    "Qwen/Qwen2.5-Coder-7B-Instruct": datetime(2024, 9, 1, tzinfo=UTC),
    "DeepSeek-Coder-V2-Lite-Instruct": datetime(2024, 6, 1, tzinfo=UTC),
    "Meta-Llama/Llama-3.1-8B-Instruct": datetime(2024, 3, 1, tzinfo=UTC),
}


class SplitName(StrEnum):
    """Disjoint dataset split buckets."""

    training = "training"
    dev = "dev"
    main = "main"


@runtime_checkable
class SplittableTask(Protocol):
    """Minimal protocol required by the contamination-aware splitter."""

    @property
    def task_id(self) -> str: ...

    @property
    def created_at(self) -> datetime: ...


class TaskRecord(BaseModel):
    """Lightweight task metadata record for splitting datasets without full files."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(..., min_length=1)
    created_at: datetime
    repo_name: str = Field(default="")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def normalize_utc(dt: date | datetime) -> datetime:
    """Normalize a date or datetime to a timezone-aware UTC datetime."""
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    return datetime(dt.year, dt.month, dt.day, tzinfo=UTC)


def get_cutoff_for_model(model_name: str) -> datetime:
    """Return the configured training cutoff UTC datetime for a model."""
    return MODEL_CUTOFF_DATES.get(model_name, DEFAULT_CUTOFF_DATE)


# ---------------------------------------------------------------------------
# Split Manifest Schema
# ---------------------------------------------------------------------------


class SplitManifest(BaseModel):
    """Reproducible manifest recording contamination-aware task splits."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=1, frozen=True)
    manifest_id: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)
    cutoff_date: str = Field(..., description="ISO-8601 UTC cutoff timestamp.")
    seed: int = Field(..., description="RNG seed used for post-cutoff dev/main split.")
    dev_ratio: float = Field(..., ge=0.0, le=1.0)
    splits: dict[SplitName, list[str]]
    task_dates: dict[str, str]
    counts: dict[SplitName, int]
    content_hash: str = Field(default="", description="SHA-256 hash of deterministic fields.")

    def compute_hash(self) -> str:
        """Compute deterministic SHA-256 content hash excluding manifest_id and content_hash."""
        payload = self.model_dump(exclude={"content_hash", "manifest_id"})
        return content_hash(stable_json(payload))

    def verify_hash(self) -> bool:
        """Return True if stored content_hash matches the recomputed hash."""
        return bool(self.content_hash) and self.content_hash == self.compute_hash()

    def save(self, path: Path) -> None:
        """Write manifest JSON to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> SplitManifest:
        """Load manifest JSON from disk and verify its content hash."""
        raw = json.loads(path.read_text(encoding="utf-8"))
        manifest = cls.model_validate(raw)
        if not manifest.verify_hash():
            raise ValueError(
                f"SplitManifest hash mismatch in {path}: "
                f"expected {manifest.compute_hash()}, got {manifest.content_hash}"
            )
        return manifest


# ---------------------------------------------------------------------------
# Task Splitter
# ---------------------------------------------------------------------------


def split_tasks(
    tasks: Sequence[SplittableTask],
    *,
    cutoff_date: date | datetime | None = None,
    dev_ratio: float = 0.2,
    seed: int = 42,
    model_name: str = DEFAULT_MODEL_NAME,
) -> SplitManifest:
    """Partition tasks into disjoint ``training``, ``dev``, and ``main`` splits.

    Rules:
    1. Tasks with ``created_at < cutoff_date`` are placed strictly in ``training``
       (excluded from ``dev`` and ``main`` to prevent data contamination).
    2. Tasks with ``created_at >= cutoff_date`` are deterministically sorted by
       ``(created_at, task_id)``, shuffled with ``random.Random(seed)``, and
       partitioned into ``dev`` and ``main`` according to ``dev_ratio``.
    3. Every split list is sorted lexicographically in the manifest so the
       resulting ``SplitManifest`` and its ``content_hash`` are 100% reproducible
       regardless of input ordering.
    """
    if not 0.0 <= dev_ratio <= 1.0:
        raise ValueError(f"dev_ratio must be between 0.0 and 1.0, got {dev_ratio}")

    cutoff_dt = (
        normalize_utc(cutoff_date) if cutoff_date is not None else get_cutoff_for_model(model_name)
    )

    seen_ids: set[str] = set()
    normalized: list[tuple[datetime, str]] = []
    task_dates: dict[str, str] = {}

    for task in tasks:
        if task.task_id in seen_ids:
            raise ValueError(f"Duplicate task_id encountered: '{task.task_id}'")
        seen_ids.add(task.task_id)
        dt_utc = normalize_utc(task.created_at)
        normalized.append((dt_utc, task.task_id))
        task_dates[task.task_id] = dt_utc.isoformat()

    # Sort deterministically before partitioning so input order never affects outcome
    normalized.sort(key=lambda item: (item[0], item[1]))

    training_ids: list[str] = []
    post_cutoff_ids: list[str] = []

    for dt_utc, tid in normalized:
        if dt_utc < cutoff_dt:
            training_ids.append(tid)
        else:
            post_cutoff_ids.append(tid)

    # Deterministic shuffle of post-cutoff tasks
    rng = random.Random(seed)
    shuffled_post = list(post_cutoff_ids)
    rng.shuffle(shuffled_post)

    n_post = len(shuffled_post)
    if n_post == 0 or dev_ratio == 0.0:
        n_dev = 0
    elif dev_ratio == 1.0:
        n_dev = n_post
    else:
        n_dev = round(n_post * dev_ratio)
        if n_post >= 2 and n_dev == 0 and dev_ratio > 0.0:
            n_dev = 1
        if n_dev >= n_post:
            n_dev = n_post - 1

    dev_ids = sorted(shuffled_post[:n_dev])
    main_ids = sorted(shuffled_post[n_dev:])
    training_ids = sorted(training_ids)

    splits: dict[SplitName, list[str]] = {
        SplitName.training: training_ids,
        SplitName.dev: dev_ids,
        SplitName.main: main_ids,
    }
    counts: dict[SplitName, int] = {
        SplitName.training: len(training_ids),
        SplitName.dev: len(dev_ids),
        SplitName.main: len(main_ids),
    }

    sorted_task_dates = {k: task_dates[k] for k in sorted(task_dates)}

    manifest = SplitManifest(
        manifest_id="pending",
        model_name=model_name,
        cutoff_date=cutoff_dt.isoformat(),
        seed=seed,
        dev_ratio=dev_ratio,
        splits=splits,
        task_dates=sorted_task_dates,
        counts=counts,
        content_hash="",
    )
    digest = manifest.compute_hash()
    return manifest.model_copy(
        update={
            "content_hash": digest,
            "manifest_id": f"split-{digest[:12]}",
        }
    )
