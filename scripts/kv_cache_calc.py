#!/usr/bin/env python3
"""scripts/kv_cache_calc.py — Back-of-envelope KV-cache and VRAM calculator.

Computes theoretical weights memory, KV-cache bytes per token, block sizes,
and maximum token capacity across GPU memory configurations.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelArchitecture:
    name: str
    num_layers: int
    num_kv_heads: int
    num_query_heads: int
    head_dim: int
    dtype_bytes: int = 2  # FP16 / BF16 = 2 bytes, FP8 = 1 byte
    param_count_billions: float = 7.61


QWEN_2_5_CODER_7B = ModelArchitecture(
    name="Qwen/Qwen2.5-Coder-7B-Instruct",
    num_layers=28,
    num_kv_heads=4,
    num_query_heads=28,
    head_dim=128,
    dtype_bytes=2,
    param_count_billions=7.61,
)


def calculate_kv_cache_bytes_per_token(arch: ModelArchitecture) -> int:
    """Calculate exact bytes required for Key + Value tensors per token.

    Formula: 2 (Key + Value) * num_layers * num_kv_heads * head_dim * dtype_bytes
    """
    return 2 * arch.num_layers * arch.num_kv_heads * arch.head_dim * arch.dtype_bytes


def calculate_weights_memory_bytes(arch: ModelArchitecture) -> int:
    """Calculate unquantized weights memory in bytes."""
    return int(arch.param_count_billions * 1e9 * arch.dtype_bytes)


def calculate_max_cached_tokens(
    total_gpu_vram_gb: float,
    arch: ModelArchitecture,
    activation_overhead_gb: float = 1.5,
    gpu_memory_utilization: float = 0.90,
) -> int:
    """Calculate maximum cached token capacity for a GPU configuration."""
    available_vram_bytes = int(total_gpu_vram_gb * (1024**3) * gpu_memory_utilization)
    weights_bytes = calculate_weights_memory_bytes(arch)
    overhead_bytes = int(activation_overhead_gb * (1024**3))

    kv_available_bytes = max(0, available_vram_bytes - weights_bytes - overhead_bytes)
    bytes_per_token = calculate_kv_cache_bytes_per_token(arch)

    return kv_available_bytes // bytes_per_token


def main() -> None:
    parser = argparse.ArgumentParser(description="KV-cache memory calculator")
    parser.add_argument("--vram-gb", type=float, default=24.0, help="Total GPU VRAM in GB")
    parser.add_argument(
        "--utilization",
        type=float,
        default=0.90,
        help="GPU memory utilization fraction",
    )
    args = parser.parse_args()

    arch = QWEN_2_5_CODER_7B
    bytes_per_tok = calculate_kv_cache_bytes_per_token(arch)
    weights_bytes = calculate_weights_memory_bytes(arch)
    weights_gib = weights_bytes / (1024**3)
    max_tokens = calculate_max_cached_tokens(
        args.vram_gb, arch, gpu_memory_utilization=args.utilization
    )
    gqa_ratio = arch.num_query_heads // arch.num_kv_heads
    paged_block_bytes = bytes_per_tok * 16

    print(f"Model Architecture: {arch.name}")
    print(f"  Layers:              {arch.num_layers}")
    print(f"  KV Heads:            {arch.num_kv_heads} (GQA ratio {gqa_ratio}:1)")
    print(f"  Head Dimension:      {arch.head_dim}")
    print(f"  Dtype:               {arch.dtype_bytes * 8}-bit ({arch.dtype_bytes} bytes/element)")
    print(f"  Weights Memory:      {weights_gib:.2f} GiB ({weights_bytes:,} bytes)")
    print(f"  KV Bytes per Token:  {bytes_per_tok:,} bytes ({bytes_per_tok / 1024:.1f} KiB/token)")
    print(
        f"  Paged Block (16 tok): {paged_block_bytes:,} bytes "
        f"({paged_block_bytes / 1024:.1f} KiB/block)"
    )
    print(
        f"  Max Cached Tokens ({args.vram_gb:.0f} GB @ {args.utilization:.0%}): "
        f"{max_tokens:,} tokens"
    )


if __name__ == "__main__":
    main()
