#!/usr/bin/env python3
"""Build task-environment images and validate grading on benchmark instances.

Executes gold patches and empty patches across all benchmark instances, verifies
verdicts, and logs environment image metrics to reports/task_images.csv.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from codeagent.grader import generate_task_images_report, grade_instance
from codeagent.task import BENCHMARK_TASKS


def main() -> None:
    parser = argparse.ArgumentParser(description="Build task images and validate grading")
    parser.add_argument(
        "--report-csv",
        default="reports/task_images.csv",
        help="Path to output CSV report for task images",
    )
    args = parser.parse_args()

    csv_path = Path(args.report_csv)
    print("=" * 70)
    print("1. Building Task Environment Images")
    print("=" * 70)
    metrics = generate_task_images_report(csv_path)
    for m in metrics:
        print(
            f"  - [{m.task_id}] {m.image_name}: "
            f"build_time={m.build_time_s}s, size={m.image_size_mb}MB"
        )
    print(f"\nTask images report written to {csv_path}\n")

    print("=" * 70)
    print("2. Validating Grading Engine (Gold vs Empty Patch)")
    print("=" * 70)

    all_passed = True
    for task_id, task in BENCHMARK_TASKS.items():
        print(f"\nEvaluating Task: {task_id} ({task.repo_name})")

        # 1. Run Gold Patch (must PASS)
        gold_res = grade_instance(task, task.gold_patch)
        print(f"  * Gold Patch  -> Verdict: {gold_res.verdict} (passed={gold_res.passed})")
        if not gold_res.passed:
            print(f"    ERROR: Gold patch failed! Output:\n{gold_res.output}")
            all_passed = False

        # 2. Run Empty Patch (must FAIL)
        empty_res = grade_instance(task, "")
        print(f"  * Empty Patch -> Verdict: {empty_res.verdict} (passed={empty_res.passed})")
        if empty_res.passed:
            print(f"    ERROR: Empty patch unexpectedly passed! Output:\n{empty_res.output}")
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("ALL VERDICTS VERIFIED: Gold passes and Empty fails across all instances.")
    else:
        print("VALIDATION FAILED: At least one instance verdict did not match expectation.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
