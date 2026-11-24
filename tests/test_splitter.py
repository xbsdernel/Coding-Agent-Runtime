"""Tests for contamination-aware task splitting and split manifest integrity."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from codeagent.splitter import (
    SplitManifest,
    SplitName,
    TaskRecord,
    get_cutoff_for_model,
    split_tasks,
)
from codeagent.task import BENCHMARK_TASKS

ROOT = Path(__file__).resolve().parent.parent


def _make_sample_dataset() -> list[TaskRecord]:
    """Create a mixed pre-cutoff and post-cutoff dataset (cutoff = 2024-09-01)."""
    return [
        TaskRecord(task_id="pre_1", created_at=datetime(2023, 5, 1, tzinfo=UTC)),
        TaskRecord(task_id="pre_2", created_at=datetime(2024, 1, 15, tzinfo=UTC)),
        TaskRecord(task_id="pre_3", created_at=datetime(2024, 8, 31, 23, 59, tzinfo=UTC)),
        TaskRecord(task_id="post_1", created_at=datetime(2024, 9, 1, 0, 0, tzinfo=UTC)),
        TaskRecord(task_id="post_2", created_at=datetime(2024, 10, 12, tzinfo=UTC)),
        TaskRecord(task_id="post_3", created_at=datetime(2024, 11, 20, tzinfo=UTC)),
        TaskRecord(task_id="post_4", created_at=datetime(2025, 1, 5, tzinfo=UTC)),
        TaskRecord(task_id="post_5", created_at=datetime(2025, 2, 18, tzinfo=UTC)),
        TaskRecord(task_id="post_6", created_at=datetime(2025, 3, 22, tzinfo=UTC)),
        TaskRecord(task_id="post_7", created_at=datetime(2025, 4, 10, tzinfo=UTC)),
        TaskRecord(task_id="post_8", created_at=datetime(2025, 5, 1, tzinfo=UTC)),
    ]


def test_split_manifest_reproducible():
    """Acceptance criterion: Split manifest is reproducible (same hash on re-run)."""
    tasks = _make_sample_dataset()
    m1 = split_tasks(tasks, cutoff_date=date(2024, 9, 1), dev_ratio=0.25, seed=42)
    m2 = split_tasks(list(reversed(tasks)), cutoff_date=date(2024, 9, 1), dev_ratio=0.25, seed=42)

    assert m1.verify_hash() is True
    assert m1.content_hash == m2.content_hash
    assert m1.manifest_id == m2.manifest_id
    assert m1.splits == m2.splits


def test_splits_are_strictly_disjoint():
    """Acceptance criterion: No task appears in more than one split."""
    tasks = _make_sample_dataset()
    manifest = split_tasks(tasks, cutoff_date=date(2024, 9, 1), dev_ratio=0.25, seed=42)

    train_set = set(manifest.splits[SplitName.training])
    dev_set = set(manifest.splits[SplitName.dev])
    main_set = set(manifest.splits[SplitName.main])

    assert train_set.isdisjoint(dev_set)
    assert train_set.isdisjoint(main_set)
    assert dev_set.isdisjoint(main_set)

    all_assigned = train_set | dev_set | main_set
    assert all_assigned == {t.task_id for t in tasks}
    assert sum(manifest.counts.values()) == len(tasks)


def test_pre_cutoff_tasks_excluded_from_main_and_dev():
    """Acceptance criterion: Tasks before cutoff are excluded from the main split."""
    tasks = _make_sample_dataset()
    cutoff = datetime(2024, 9, 1, tzinfo=UTC)
    manifest = split_tasks(tasks, cutoff_date=cutoff, dev_ratio=0.25, seed=42)

    assert set(manifest.splits[SplitName.training]) == {"pre_1", "pre_2", "pre_3"}
    for pre_id in ("pre_1", "pre_2", "pre_3"):
        assert pre_id not in manifest.splits[SplitName.main]
        assert pre_id not in manifest.splits[SplitName.dev]

    # Post-cutoff tasks (including exact cutoff boundary) must not be in training
    for post_id in [f"post_{i}" for i in range(1, 9)]:
        assert post_id not in manifest.splits[SplitName.training]


def test_manifest_save_load_and_tamper_detection(tmp_path: Path):
    """Verify manifest round-trip persistence and SHA-256 tamper detection."""
    tasks = _make_sample_dataset()
    manifest = split_tasks(tasks, dev_ratio=0.25, seed=42)
    out_file = tmp_path / "split_manifest.json"
    manifest.save(out_file)

    loaded = SplitManifest.load(out_file)
    assert loaded == manifest
    assert loaded.verify_hash() is True

    # Tamper with split assignment without updating hash
    raw = json.loads(out_file.read_text(encoding="utf-8"))
    raw["splits"]["main"].append("pre_1")
    out_file.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(ValueError, match="hash mismatch"):
        SplitManifest.load(out_file)


def test_validation_errors():
    """Verify duplicate task IDs and out-of-range dev_ratio are rejected."""
    dup_tasks = [
        TaskRecord(task_id="t1", created_at=datetime(2025, 1, 1, tzinfo=UTC)),
        TaskRecord(task_id="t1", created_at=datetime(2025, 1, 2, tzinfo=UTC)),
    ]
    with pytest.raises(ValueError, match="Duplicate task_id"):
        split_tasks(dup_tasks)

    with pytest.raises(ValueError, match="dev_ratio"):
        split_tasks([], dev_ratio=1.5)


def test_model_cutoff_lookup():
    """Verify default model cutoff lookup matches ADR 0002 selection."""
    cutoff = get_cutoff_for_model("Qwen/Qwen2.5-Coder-7B-Instruct")
    assert cutoff == datetime(2024, 9, 1, tzinfo=UTC)


def test_committed_split_manifest_valid():
    """Verify reports/task_split_manifest.json exists, is valid, and covers benchmark tasks."""
    manifest_path = ROOT / "reports" / "task_split_manifest.json"
    assert manifest_path.is_file()

    manifest = SplitManifest.load(manifest_path)
    assert manifest.verify_hash() is True
    all_ids = (
        set(manifest.splits[SplitName.training])
        | set(manifest.splits[SplitName.dev])
        | set(manifest.splits[SplitName.main])
    )
    assert all_ids == set(BENCHMARK_TASKS.keys())
    assert "calc_001_div_zero" in manifest.splits[SplitName.training]
    assert "calc_001_div_zero" not in manifest.splits[SplitName.main]
