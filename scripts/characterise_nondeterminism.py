#!/usr/bin/env python3
"""scripts/characterise_nondeterminism.py – Sampling nondeterminism characterisation tool.

Sends the same prompt ``N`` times at ``temperature=0`` (greedy) and at a chosen
``temperature`` (sampled), counts distinct outputs, and finds the index of the first
diverging token across all pairs.  Writes a summary to ``reports/nondeterminism.md``.

Usage
-----
    python scripts/characterise_nondeterminism.py \\
        --base-url http://127.0.0.1:8000 \\
        --temperature 0.8 \\
        --n 20 \\
        --prompt "Write a Python function that returns the nth Fibonacci number."

The script works against the mock server for offline testing.  When ``temperature``
is forwarded to the mock server it has no effect (the mock is deterministic), so
both conditions will show 0 divergence — which is the expected result for a
deterministic reference implementation.

Exit codes
----------
0   – report written successfully
1   – connection or other fatal error
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import textwrap
import time
from pathlib import Path
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPORTS_DIR = Path(__file__).parent.parent / "reports"


def _extract_text(response_data: dict[str, Any]) -> str:
    """Pull the assistant text from a /v1/chat/completions JSON response."""
    try:
        return str(response_data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError):
        return ""


def _tokenise(text: str) -> list[str]:
    """Split on whitespace as a cheap token approximation."""
    return text.split()


def _first_diverging_token(responses: list[str]) -> int | None:
    """Return the index of the first token position where any two responses differ.

    Returns ``None`` if all responses are identical at every position.
    """
    if not responses:
        return None
    tokenised = [_tokenise(r) for r in responses]
    max_len = max(len(t) for t in tokenised)
    for idx in range(max_len):
        values_at_idx = {t[idx] if idx < len(t) else "<END>" for t in tokenised}
        if len(values_at_idx) > 1:
            return idx
    return None


async def _send_once(
    client: httpx.AsyncClient,
    base_url: str,
    messages: list[dict[str, str]],
    model: str,
    temperature: float,
    seed: int | None,
) -> str:
    """Send one chat-completion request and return the assistant text."""
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if seed is not None:
        payload["seed"] = seed

    resp = await client.post(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        json=payload,
        timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
    )
    resp.raise_for_status()
    return _extract_text(resp.json())


async def run_characterisation(
    base_url: str,
    prompt: str,
    model: str,
    n: int,
    chosen_temperature: float,
    seed: int | None,
) -> dict[str, Any]:
    """Run the two-condition sampling experiment and return a results dict."""
    messages = [{"role": "user", "content": prompt}]

    async with httpx.AsyncClient() as client:
        # Condition A: temperature = 0 (greedy / deterministic reference)
        print(f"[*] Condition A — temperature=0.0 ({n} requests) …", flush=True)
        t0 = time.monotonic()
        greedy_responses: list[str] = []
        for i in range(n):
            text = await _send_once(client, base_url, messages, model, 0.0, seed)
            greedy_responses.append(text)
            print(f"    [{i + 1:02d}/{n}] ok  ({len(text)} chars)", flush=True)
        greedy_elapsed = time.monotonic() - t0

        # Condition B: temperature = chosen_temperature
        print(
            f"[*] Condition B — temperature={chosen_temperature} ({n} requests) …",
            flush=True,
        )
        t0 = time.monotonic()
        sampled_responses: list[str] = []
        for i in range(n):
            text = await _send_once(client, base_url, messages, model, chosen_temperature, seed)
            sampled_responses.append(text)
            print(f"    [{i + 1:02d}/{n}] ok  ({len(text)} chars)", flush=True)
        sampled_elapsed = time.monotonic() - t0

    greedy_distinct = len(set(greedy_responses))
    sampled_distinct = len(set(sampled_responses))
    greedy_diverge_idx = _first_diverging_token(greedy_responses)
    sampled_diverge_idx = _first_diverging_token(sampled_responses)

    return {
        "prompt": prompt,
        "model": model,
        "n": n,
        "seed": seed,
        "conditions": {
            "greedy": {
                "temperature": 0.0,
                "responses": greedy_responses,
                "distinct_count": greedy_distinct,
                "first_diverging_token_idx": greedy_diverge_idx,
                "elapsed_s": round(greedy_elapsed, 2),
            },
            "sampled": {
                "temperature": chosen_temperature,
                "responses": sampled_responses,
                "distinct_count": sampled_distinct,
                "first_diverging_token_idx": sampled_diverge_idx,
                "elapsed_s": round(sampled_elapsed, 2),
            },
        },
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def _build_report(results: dict[str, Any]) -> str:
    """Render a Markdown report from the results dict."""
    n = results["n"]
    prompt = results["prompt"]
    model = results["model"]
    seed = results["seed"]
    greedy = results["conditions"]["greedy"]
    sampled = results["conditions"]["sampled"]

    def _diverge(idx: int | None) -> str:
        return str(idx) if idx is not None else "none (all identical)"

    def _pct_distinct(distinct: int, total: int) -> str:
        return f"{distinct}/{total} ({100 * distinct / total:.0f}%)"

    # Collect unique responses for the sampled condition
    sampled_unique = sorted(set(sampled["responses"]))
    greedy_unique = sorted(set(greedy["responses"]))

    # Build representative sample section
    def _response_bullets(unique: list[str], limit: int = 3) -> str:
        shown = unique[:limit]
        lines = []
        for i, r in enumerate(shown, 1):
            snippet = r[:120].replace("\n", " ")
            if len(r) > 120:
                snippet += "…"
            lines.append(f"{i}. `{snippet}`")
        if len(unique) > limit:
            lines.append(f"*(… and {len(unique) - limit} more)*")
        return "\n".join(lines)

    # Build table rows separately to stay within 100-char line limit
    _seed_str = str(seed) if seed is not None else "none (not sent)"
    _greedy_distinct = _pct_distinct(greedy["distinct_count"], n)
    _sampled_distinct = _pct_distinct(sampled["distinct_count"], n)
    _greedy_div = _diverge(greedy["first_diverging_token_idx"])
    _sampled_div = _diverge(sampled["first_diverging_token_idx"])
    _greedy_temp = greedy["temperature"]
    _sampled_temp = sampled["temperature"]
    _greedy_elapsed = greedy["elapsed_s"]
    _sampled_elapsed = sampled["elapsed_s"]
    _greedy_verdict = (
        "✅ fully deterministic"
        if greedy["distinct_count"] == 1
        else "⚠️ non-deterministic even at temperature 0"
    )

    report = textwrap.dedent(f"""\
    # Nondeterminism Characterisation Report

    > **Generated by** `scripts/characterise_nondeterminism.py`

    ## Experiment Setup

    | Parameter        | Value                |
    |------------------|----------------------|
    | Model            | `{model}`            |
    | Prompt           | *see below*          |
    | Repeats (N)      | {n}                  |
    | Seed             | {_seed_str}          |
    | Greedy temp      | {_greedy_temp}       |
    | Sampled temp     | {_sampled_temp}      |

    **Prompt:**

    > {prompt}

    ---

    ## Results

    | Condition     | Temp | Distinct | First div. tok | Elapsed (s) |
    |---------------|------|----------|----------------|-------------|
    | Greedy (ref.) | 0.0  | {_greedy_distinct} | {_greedy_div} | {_greedy_elapsed} |
    | Sampled       | {_sampled_temp} | {_sampled_distinct} | {_sampled_div} | {_sampled_elapsed} |

    ### Greedy condition — unique responses

    {_response_bullets(greedy_unique)}

    ### Sampled condition — unique responses

    {_response_bullets(sampled_unique)}

    ---

    ## Analysis

    ### Greedy (temperature = 0)

    With `temperature=0` the model uses greedy decoding — it always selects the
    highest-probability next token.  A fully deterministic implementation should
    produce **1 distinct output** across all {n} runs (i.e. divergence count = 0).

    If `seed` is not supported or the runtime is non-deterministic (e.g. different
    GPU kernel launch orders), small variations may still appear.  Observing >1
    distinct output at temperature 0 is a signal that the backend is not fully
    reproducible and that **per-task seeds are required**.

    ### Sampled (temperature = {_sampled_temp})

    At `temperature={_sampled_temp}` the model samples from the top-k/p
    distribution.  Nondeterminism is **expected and desired** — it allows the agent
    to explore different reasoning paths across runs.

    The *first diverging token index* tells us at which position outputs start to
    differ.  A low index (e.g. ≤ 5) means responses fork almost immediately,
    producing high diversity.  A high index indicates responses share a long common
    prefix before diverging.

    ### Recommended repeats per task

    For statistical significance in pass-rate estimates the required number of
    independent runs depends on the expected pass rate `p` and the desired margin
    of error `ε`:

    ```
    n ≈ z² · p(1 - p) / ε²
    ```

    With `p ≈ 0.5` (worst case), `z = 1.96` (95 % CI), and `ε = 0.1`:

    ```
    n ≈ 1.96² × 0.25 / 0.01 ≈ 96
    ```

    However, in practice **20 runs** (as used in this experiment) provide a
    reasonable budget-aware baseline.  The key guidance is:

    - **If temperature = 0 and seed is set**: 1 run is sufficient (fully
      reproducible), but 3 runs are recommended to guard against
      infrastructure flakiness.
    - **If temperature > 0 and seed is unset**: ≥ 20 runs for coarse estimates;
      ≥ 50 runs for publication-quality pass@k estimates.
    - **If diversity of reasoning matters** (e.g. for best-of-N selection):
      match N to the first-diverging-token index; a low index means fewer
      runs are needed to cover the response space.

    ---

    ## Conclusions

    1. **Greedy distinct outputs**: {greedy["distinct_count"]} / {n} — {_greedy_verdict}
    2. **Sampled distinct**: {sampled["distinct_count"]} / {n} at temperature {_sampled_temp}
    3. **First diverging token (greedy)**: {_greedy_div}
    4. **First diverging token (sampled)**: {_sampled_div}
    5. **Recommended repeats**: 20 runs for pass-rate estimation; 3 runs for
       greedy/seeded configurations; ≥ 50 runs for high-confidence pass@k.

    > [!NOTE]
    > These results were collected against the **mock server**, which always returns
    > a deterministic canned response regardless of `temperature`.  On a real GPU
    > backend the sampled condition will show significantly higher divergence.
    > Re-run this script against a live vLLM/Ollama instance to obtain production
    > numbers.
    """)
    return report


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Characterise LLM sampling nondeterminism",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the OpenAI-compatible server (default: %(default)s)",
    )
    parser.add_argument(
        "--model",
        default="Qwen/Qwen2.5-Coder-7B-Instruct",
        help="Model identifier to pass in requests (default: %(default)s)",
    )
    parser.add_argument(
        "--prompt",
        default="Write a Python function that returns the nth Fibonacci number.",
        help="Prompt to send repeatedly (default: %(default)s)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.8,
        help="Sampled temperature for condition B (default: %(default)s)",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=20,
        help="Number of repeats per condition (default: %(default)s)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed to include in every request (default: not sent)",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional path to write raw results as JSON",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=REPORTS_DIR / "nondeterminism.md",
        help="Markdown report output path (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    # Validate temperature in [0, 2]
    if not (0.0 <= args.temperature <= 2.0):
        print(
            f"ERROR: --temperature must be in [0.0, 2.0], got {args.temperature}", file=sys.stderr
        )
        return 1

    if args.n < 1:
        print(f"ERROR: --n must be >= 1, got {args.n}", file=sys.stderr)
        return 1

    print("[*] Starting nondeterminism characterisation")
    print(f"    Server  : {args.base_url}")
    print(f"    Model   : {args.model}")
    print(f"    Prompt  : {args.prompt[:60]}{'…' if len(args.prompt) > 60 else ''}")
    print(f"    N       : {args.n}")
    print(f"    Seed    : {args.seed}")
    print(f"    Temp B  : {args.temperature}")
    print()

    try:
        results = asyncio.run(
            run_characterisation(
                base_url=args.base_url,
                prompt=args.prompt,
                model=args.model,
                n=args.n,
                chosen_temperature=args.temperature,
                seed=args.seed,
            )
        )
    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
        print(f"\nERROR: Cannot reach server at {args.base_url}: {exc}", file=sys.stderr)
        print("Is the mock server running?  Try: python scripts/mock_server.py", file=sys.stderr)
        return 1

    # Write JSON if requested
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        # Exclude raw response lists from the JSON (too large) but keep stats
        summary = {k: v for k, v in results.items() if k != "conditions"}
        summary["conditions"] = {
            cond: {k: v for k, v in data.items() if k != "responses"}
            for cond, data in results["conditions"].items()
        }
        args.output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\n[*] JSON results written to {args.output_json}")

    # Write Markdown report
    report_md = _build_report(results)
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(report_md, encoding="utf-8")
    print(f"\n[*] Report written to {args.report_path}")

    # Print summary table to stdout
    greedy = results["conditions"]["greedy"]
    sampled = results["conditions"]["sampled"]
    n = results["n"]
    print("\n── Summary ─────────────────────────────────────────────────")
    print(
        f"  Greedy  (T=0.0): {greedy['distinct_count']}/{n} distinct | "
        f"first diverge @ token {greedy['first_diverging_token_idx']}"
    )
    print(
        f"  Sampled (T={sampled['temperature']}): {sampled['distinct_count']}/{n} distinct | "
        f"first diverge @ token {sampled['first_diverging_token_idx']}"
    )
    print("────────────────────────────────────────────────────────────")

    return 0


if __name__ == "__main__":
    sys.exit(main())
