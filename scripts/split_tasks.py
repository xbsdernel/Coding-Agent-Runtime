#!/usr/bin/env python3
"""Generate a contamination-aware task split manifest.

Splits benchmark tasks into training (pre-cutoff), dev, and main (post-cutoff)
buckets relative to the primary model's training cutoff and writes a
content-hashed manifest to disk.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from codeagent.splitter import DEFAULT_MODEL_NAME, split_tasks
from codeagent.task import BENCHMARK_TASKS


def main() -> None:
    parser = argparse.ArgumentParser(description="Contamination-aware task splitter")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_NAME,
        help="Target model name for training cutoff lookup",
    )
    parser.add_argument(
        "--dev-ratio",
        type=float,
        default=0.5,
        help="Fraction of post-cutoff tasks assigned to dev split",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic RNG seed",
    )
    parser.add_argument(
        "--output",
        default="reports/task_split_manifest.json",
        help="Output manifest JSON path",
    )
    args = parser.parse_args()

    manifest = split_tasks(
        list(BENCHMARK_TASKS.values()),
        dev_ratio=args.dev_ratio,
        seed=args.seed,
        model_name=args.model,
    )
    out_path = Path(args.output)
    manifest.save(out_path)

    print(f"Manifest ID:   {manifest.manifest_id}")
    print(f"Model:         {manifest.model_name}")
    print(f"Cutoff Date:   {manifest.cutoff_date}")
    print(f"Content Hash:  {manifest.content_hash}")
    print(f"Split Counts:  { {k.value: v for k, v in manifest.counts.items()} }")
    print(f"Saved to:      {out_path}")


if __name__ == "__main__":
    main()
