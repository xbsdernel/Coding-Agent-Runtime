# PROJECT_STATE.md

> Auto-updated after each completed issue. Reflects the actual state of the codebase.

---

## Completed Issues

| Issue | Title | Branch | Status |
|---|---|---|---|
| ISS-001 | Project scaffold: packaging layout, CLI stub, and typed Pydantic schemas | `feat/001-project-scaffold` | ✅ Done |
| ISS-002 | Git hygiene, tagged milestones, and dirty-tree guard | `feat/002-git-hygiene` | ✅ Done |
| ISS-003 | Research habits: ADR template and experiment note template | `feat/003-research-templates` | ✅ Done |
| ISS-004 | Trace event logger and reader with content hashing | `feat/004-trace-logger-reader` | ✅ Done |

---

## Current Progress

- **Phase:** P0 — Project Foundations
- **Latest commit:** `feat/004-trace-logger-reader` branch
- **Test suite:** 41 tests passing (0.43s)
- **Package:** `codeagent 0.1.0` installable via `pip install -e ".[dev]"`
- **Git Tags:** `v0-scaffold`, `schemas-v1`
- **Milestone Manifest:** `manifest.json` (SHA-256 verified)
- **Lockfile:** `requirements.lock`
- **Research Standards:** ADR 0001, ADR template, and pre-registered experiment note template in place
- **Telemetry & Tracing:** Append-only JSONL `TraceWriter` and aggregating `TraceReader` with SHA-256 content hashes

---

## Architectural Decisions

- **Build backend:** Hatchling (`pyproject.toml`, `src/` layout)
- **CLI framework:** Click
- **Version & Stamping:** Dynamic `git describe --tags --always --dirty --long` stamping on CLI `--version` and `info`
- **Clean-Tree Discipline:** `git status --porcelain` check blocks execution on dirty/untracked working tree
- **Milestone Manifest:** SHA-256 hash manifest (`scripts/manifest.py`) verifying frozen file integrity
- **Schema validation:** Pydantic v2 with `extra="forbid"` and `schema_version` on every model
- **Determinism:** `seed_all()` utility, `stable_json()` with sorted keys, `content_hash()` via SHA-256
- **Architecture Decision Records:** Michael Nygard format (`docs/decisions/0001-record-decisions.md`, `_template.md`)
- **Pre-Registration Gate:** Mandatory 5-field experiment note structure (Hypothesis, Stop Rule, Config Hash, Result, Decision) before any compute run
- **Event Telemetry:** OpenTelemetry GenAI semantic conventions, append-only JSONL with mandatory content hash validation and token delta tracking
- **Python version:** 3.11+ (developed on 3.12.3)

---

## Core Schemas (frozen at v1)

| Schema | Purpose |
|---|---|
| `TraceEvent` | Append-only JSONL event log entry (model calls, tool calls, state changes) |
| `ExperimentConfig` | Immutable experiment configuration snapshot with config hash |
| `ResultRow` | One row per episode in the columnar result store |
| `BudgetSpec` | Budget limits enforced by the agent loop per episode |

---

## Dependencies

- `pydantic >=2.0, <3`
- `click >=8.0, <9`
- Pinned in `requirements.lock`
- Dev: `pytest`, `pytest-cov`, `ruff`, `mypy`

---

## Known Limitations

- CLI `run` command is a placeholder — requires ISS-021 (agent loop state machine).
- No CI workflow yet — planned in ISS-005.

---

## Next Step

**ISS-005** · Base CI workflow: lint, typing, and unit test suite
