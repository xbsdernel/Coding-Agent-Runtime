"""Tests for task environment definitions, image metrics, and authoritative grader."""

from __future__ import annotations

import csv
from pathlib import Path

from codeagent.grader import (
    GradingResult,
    generate_task_images_report,
    grade_instance,
    patch_modifies_test_files,
    strip_test_modifications,
)
from codeagent.schemas import ResultRow, StopReason
from codeagent.task import (
    BENCHMARK_TASKS,
    TASK_CALC,
    TASK_FORMATTER,
    TASK_GRAPH,
)

ROOT = Path(__file__).resolve().parent.parent


def test_benchmark_instances_completeness():
    """Verify all 3 canonical benchmark instances are defined with required attributes."""
    assert len(BENCHMARK_TASKS) == 3
    for task_id in ["calc_001_div_zero", "formatter_002_truncate", "graph_003_cycle"]:
        assert task_id in BENCHMARK_TASKS
        task = BENCHMARK_TASKS[task_id]
        assert task.problem_statement
        assert task.base_files
        assert task.test_files
        assert task.test_patch
        assert task.gold_patch
        assert task.dockerfile
        assert task.image_name


def test_gold_patches_pass_on_all_instances():
    """Acceptance criterion: Gold patch passes on all three instances."""
    for task_id, task in BENCHMARK_TASKS.items():
        res = grade_instance(task, task.gold_patch)
        assert res.passed is True, f"Gold patch failed on {task_id}: {res.output}"
        assert res.verdict == "PASS"
        assert res.tamper_flag is False
        assert res.duration_s > 0.0


def test_empty_patches_fail_on_all_instances():
    """Acceptance criterion: Empty patch fails on all three instances."""
    for task_id, task in BENCHMARK_TASKS.items():
        res = grade_instance(task, "")
        assert res.passed is False, f"Empty patch unexpectedly passed on {task_id}"
        assert res.verdict == "FAIL"
        assert res.tamper_flag is False


def test_grader_idempotence_and_reproducibility():
    """Acceptance criterion: Re-running the grader gives identical verdicts."""
    for _ in range(2):
        res_calc = grade_instance(TASK_CALC, TASK_CALC.gold_patch)
        assert res_calc.passed is True
        assert res_calc.verdict == "PASS"

        res_calc_empty = grade_instance(TASK_CALC, "")
        assert res_calc_empty.passed is False
        assert res_calc_empty.verdict == "FAIL"

        res_fmt = grade_instance(TASK_FORMATTER, TASK_FORMATTER.gold_patch)
        assert res_fmt.passed is True
        assert res_fmt.verdict == "PASS"

        res_graph = grade_instance(TASK_GRAPH, TASK_GRAPH.gold_patch)
        assert res_graph.passed is True
        assert res_graph.verdict == "PASS"


def test_tamper_defense_ignores_test_edits():
    """Verify grader copies in authoritative tests and ignores candidate edits to test files."""
    # Tampering patch: replaces authoritative tests with a trivial passing test
    malicious_patch = (
        "diff --git a/tests/test_calc.py b/tests/test_calc.py\n"
        "--- a/tests/test_calc.py\n"
        "+++ b/tests/test_calc.py\n"
        "@@ -1,5 +1,2 @@\n"
        "-import pytest\n"
        "+def test_trivial():\n"
        "+    assert True\n"
    )

    # 1. Tamper check detects test file modification
    assert patch_modifies_test_files(malicious_patch, TASK_CALC.test_files) is True

    # 2. Stripping test modifications empties the patch
    stripped = strip_test_modifications(malicious_patch, TASK_CALC.test_files)
    assert "tests/test_calc.py" not in stripped

    # 3. Grader marks tamper_flag=True, ignores the cheat, runs real tests, and fails
    res = grade_instance(TASK_CALC, malicious_patch)
    assert res.tamper_flag is True
    assert res.passed is False
    assert res.verdict == "FAIL"


def test_task_images_report_generation(tmp_path: Path):
    """Acceptance criterion: Build time and image size logged to reports/task_images.csv."""
    test_csv = tmp_path / "task_images.csv"
    metrics = generate_task_images_report(test_csv)

    assert len(metrics) == 3
    assert test_csv.is_file()

    with test_csv.open("r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 3
        headers = list(reader[0].keys())
        expected_headers = ["task_id", "image_name", "build_time_s", "image_size_mb", "created_at"]
        assert headers == expected_headers

        for row in reader:
            assert row["task_id"] in BENCHMARK_TASKS
            assert float(row["build_time_s"]) > 0.0
            assert float(row["image_size_mb"]) > 100.0


def test_reports_task_images_csv_committed_file():
    """Verify repository reports/task_images.csv exists and contains valid rows."""
    repo_csv = ROOT / "reports" / "task_images.csv"
    assert repo_csv.is_file(), "reports/task_images.csv was not generated"

    with repo_csv.open("r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 3
        task_ids = {r["task_id"] for r in reader}
        assert task_ids == set(BENCHMARK_TASKS.keys())


def test_grading_result_schema_compatibility():
    """Verify GradingResult maps cleanly to standard ResultRow schema."""
    res = GradingResult(
        task_id=TASK_CALC.task_id,
        passed=True,
        verdict="PASS",
        duration_s=1.23,
        tamper_flag=False,
        output="1 passed",
    )
    row = ResultRow(
        task_id=res.task_id,
        arm="baseline",
        seed=42,
        outcome="pass" if res.passed else "fail",
        stop_reason=StopReason.submitted,
        tamper_flag=res.tamper_flag,
        manifest_id="manifest-v1",
        wallclock_s=res.duration_s,
    )
    assert row.outcome == "pass"
    assert row.tamper_flag is False
    assert row.task_id == "calc_001_div_zero"
