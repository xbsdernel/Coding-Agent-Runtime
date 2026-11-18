# Coding-Agent Runtime

> A modular, reproducible execution runtime and statistical evaluation harness for autonomous software-engineering agents.

---

## Overview

**Coding-Agent Runtime** is an infrastructure framework designed to run, trace, and rigorously evaluate LLM-based autonomous coding agents on issue-resolution benchmarks. The platform provides a hardened execution sandbox, cache-aware context management, deterministic golden-trace replay, and a statistically sound evaluation pipeline.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                 Evaluation & Batch Runner                       │
│     (Idempotent Queue, Concurrency Caps, Spend Guard)          │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                          Agent Loop Core                                   │
│                                                                            │
│  ┌────────────────────┐  ┌───────────────────────┐  ┌───────────────────┐  │
│  │  State Machine     │  │  Context Policy Engine │  │  Hooks (Plan,    │  │
│  │  (Step/Token/Cost  │◄►│  (Full / Rolling /    │◄►│  Verify, Tamper) │  │
│  │   Budgets)         │  │   Chunked Masking)    │  │                  │  │
│  └────────┬───────────┘  └───────────────────────┘  └──────────────────┘  │
└───────────┼───────────────────────────────────────────────┬────────────────┘
            │                                               │
            ▼                                               ▼
┌───────────────────────┐                     ┌───────────────────────────┐
│   Inference Adapter   │                     │    Sandboxed Runtime      │
│  • Async HTTP + Retry │                     │  • Docker SDK Containers  │
│  • Guided Decoding    │                     │  • Process Tree Signals   │
│  • Prefix Cache Track │                     │  • cgroup v2 Limits       │
└───────────┬───────────┘                     └─────────────┬─────────────┘
            │                                               │
            ▼                                               ▼
┌───────────────────────┐                     ┌───────────────────────────┐
│   Local Model Server  │                     │  Isolated Repo Workspace  │
│  (vLLM / SGLang)      │                     │  (Tests, Patches, Diffs)  │
└───────────────────────┘                     └───────────────────────────┘
            │                                               │
            └───────────────────┬───────────────────────────┘
                                │ Emits Events
                                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                      Observability & Persistence                           │
│  • Append-Only JSONL Traces  • Prometheus Scraping  • Parquet / DuckDB    │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### Agent Loop & Budgets
- Finite state machine with explicit states: `awaiting_model`, `executing_tool`, `submitted`, `budget_exhausted`, `errored`.
- Multi-dimensional budgets: step count, total tokens, wall-clock time, estimated cost.
- Stall detection for repeated actions, oscillating edits, and no-op steps.

### Prefix-Cache-Aware Context Policies
- **Full History:** Complete context retention.
- **Rolling Masking:** Retains last *k* observations, replaces older ones with deterministic placeholders.
- **Chunked Masking:** Masks in blocks of *N* steps to preserve prefix cache between boundaries.
- Real-time cache-hit verification via Prometheus engine counters.

### Hardened Sandbox
- Process-group management with SIGTERM → grace → SIGKILL escalation.
- Docker containers with default-deny networking, cgroup v2 limits, read-only mounts.
- Automated escape tests and prompt injection evaluation.

### Deterministic Replay
- VCR-style cassette recording of model and tool responses.
- Zero-GPU CI regression testing against golden traces.
- Step-level divergence reporting.

### Tamper Defense
- SHA-256 integrity checks on protected test files.
- AST diff scanning for deleted assertions and injected skip markers.

### Statistical Evaluation
- Unbiased `pass@k` and `pass^k` estimators with cluster-bootstrapped confidence intervals.
- Paired McNemar tests, non-inferiority margins, and Holm-Bonferroni corrections.
- Pre-registration specification frozen before confirmatory runs.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Language** | Python 3.11+, Pydantic v2, asyncio |
| **Inference** | vLLM / SGLang (OpenAI-compatible), HF Tokenizers |
| **Sandbox** | Docker SDK for Python, Linux cgroup v2, subprocess signals |
| **Tools** | ripgrep, tree-sitter, `git apply --check` |
| **Storage** | Apache Parquet (pyarrow), DuckDB, pandas |
| **Observability** | JSONL tracing, Prometheus `/metrics`, Streamlit |
| **Testing** | pytest, Hypothesis, SciPy, statsmodels, GitHub Actions |

---

## Project Structure

```
├── docs/
│   └── decisions/           # Architecture Decision Records
├── experiments/             # Experiment notes (hypothesis → result)
├── reports/                 # Benchmark outputs and analysis
├── scripts/                 # Server launch, reproduction, demo
├── src/
│   └── codeagent/
│       ├── __init__.py      # Package version
│       ├── cli.py           # Click CLI entry point
│       └── schemas.py       # Frozen Pydantic schemas
├── tests/
│   ├── test_cli.py
│   └── test_schemas.py
└── pyproject.toml
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Docker Engine 24.0+ (for sandbox)
- NVIDIA GPU with 16GB+ VRAM (for model serving)

### Installation

```bash
git clone https://github.com/your-org/coding-agent-runtime.git
cd coding-agent-runtime
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### Verify

```bash
codeagent --version
pytest -q
```

---

## Experimental Workflow & Research Standards

1. **Architecture Decision Records (ADRs):** Significant design decisions and frozen interfaces are documented in [`docs/decisions/`](docs/decisions/), initiated with [ADR 0001](docs/decisions/0001-record-decisions.md) and templated via [`docs/decisions/_template.md`](docs/decisions/_template.md).
2. **Pre-Registered Experiment Notes:** All experimental runs require pre-declared hypotheses and stop rules authored in [`experiments/_template.md`](experiments/_template.md) prior to execution, capturing exact configuration hashes and empirical results.
3. **Screening & Confirmatory Phases:** Dev-set successive halving is followed by pre-registered evaluation on held-out benchmark splits.

---

## Roadmap

Development follows a staged 7-phase plan across 58 implementation issues:

| Phase | Focus | Status |
|---|---|---|
| P0 | Project scaffold, schemas, CI | 🟡 In progress |
| P1 | Model server, sandbox, tools, micro-suite | ⬜ Planned |
| P2 | Agent loop, replay, context policies, hooks | ⬜ Planned |
| P3 | Statistics, cost model, result store, CI gate | ⬜ Planned |
| P4 | Pilot, hardening, pre-registration | ⬜ Planned |
| P5 | Screening, main experiments, cost validation | ⬜ Planned |
| P6–P7 | Analysis, reporting, optional stretches | ⬜ Planned |

---

## License

Apache 2.0
