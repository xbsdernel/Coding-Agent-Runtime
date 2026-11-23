"""Tests validating KV-cache memory calculations and documentation."""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts directory to sys.path so kv_cache_calc can be imported
scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from kv_cache_calc import (  # noqa: E402
    QWEN_2_5_CODER_7B,
    calculate_kv_cache_bytes_per_token,
    calculate_max_cached_tokens,
    calculate_weights_memory_bytes,
)

ROOT = Path(__file__).resolve().parent.parent


def test_kv_cache_report_exists_and_contains_specs():
    """Verify reports/kv_cache_analysis.md exists and includes required architectural fields."""
    report = ROOT / "reports" / "kv_cache_analysis.md"
    assert report.is_file(), f"Report not found at {report}"

    text = report.read_text(encoding="utf-8")
    text_lower = text.lower()

    # Required fields per acceptance criteria
    assert "layer" in text_lower
    assert "kv head" in text_lower or "kv_head" in text_lower
    assert "head dimension" in text_lower or "head_dim" in text_lower
    assert "dtype" in text_lower or "precision" in text_lower

    # Verify quantitative calculations
    assert "57,344" in text or "56.0" in text  # KV bytes per token
    assert "110,948" in text or "108,992" in text  # token capacity
    assert "20%" in text or "20\\%" in text or "±20%" in text


def test_kv_cache_bytes_per_token_exact():
    """Verify analytical formula for KV bytes per token."""
    # 2 (Key + Value) * 28 layers * 4 KV heads * 128 head_dim * 2 bytes = 57,344 bytes
    bytes_per_tok = calculate_kv_cache_bytes_per_token(QWEN_2_5_CODER_7B)
    assert bytes_per_tok == 57_344
    assert bytes_per_tok / 1024 == 56.0  # exactly 56 KiB


def test_weights_memory_calculation():
    """Verify model weights memory footprint calculation."""
    weights_bytes = calculate_weights_memory_bytes(QWEN_2_5_CODER_7B)
    weights_gib = weights_bytes / (1024**3)
    # 7.61B * 2 bytes ~= 14.17 GiB
    assert 14.0 < weights_gib < 15.0


def test_paper_vs_server_log_within_20_percent():
    """Verify that paper calculations deviate by less than 20% from server logs."""
    paper_weights_gib = calculate_weights_memory_bytes(QWEN_2_5_CODER_7B) / (1024**3)
    server_weights_gib = 14.85  # empirical vLLM allocated weights with overhead

    weight_deviation = abs(paper_weights_gib - server_weights_gib) / server_weights_gib
    assert weight_deviation < 0.20, f"Weight deviation {weight_deviation:.2%} exceeds 20%"

    paper_max_tokens = calculate_max_cached_tokens(24.0, QWEN_2_5_CODER_7B)
    server_max_tokens = 108_992  # empirical vLLM startup log on 24 GB GPU

    token_deviation = abs(paper_max_tokens - server_max_tokens) / server_max_tokens
    assert token_deviation < 0.20, f"Token capacity deviation {token_deviation:.2%} exceeds 20%"
