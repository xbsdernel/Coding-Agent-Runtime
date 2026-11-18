# ADR 0001: Record Architecture Decisions

- **Status:** Accepted
- **Date:** 2026-11-18
- **Deciders:** Member A, Member B
- **Technical Story:** ISS-003 / Topic T1

---

## Context

As the Coding-Agent Runtime project scales across multiple sub-systems (model serving, sandboxing, context policies, statistical evaluation), architectural and engineering choices must be documented transparently. Informal verbal agreements or scattered notes lead to architecture drift, unstated assumptions, and forgotten trade-offs.

A standard mechanism is required to record architectural decisions with their alternatives and consequences.

---

## Options Considered

1. **Option 1: Informal markdown notes in pull requests**
   - Pros: Low overhead.
   - Cons: Buried in git history; difficult to locate and cross-reference; no standard structure.

2. **Option 2: Architecture Decision Records (ADRs) in `docs/decisions/`**
   - Pros: Lightweight, version-controlled alongside code, searchable, well-established industry standard (Michael Nygard format).
   - Cons: Requires engineering discipline to maintain.

3. **Option 3: External wiki / issue tracker documentation**
   - Pros: Accessible outside the repository.
   - Cons: Diverges quickly from repository commit state; lacks cryptographic linking to code versions.

---

## Decision

We adopt **Architecture Decision Records (ADRs)** stored in `docs/decisions/` using sequential four-digit numbering (`0001-record-decisions.md`, `0002-model-selection.md`, etc.). Every frozen artefact, engine selection, context policy interface, and security posture change must have an accompanying ADR.

Each record must adhere to the standard four-part structure:
1. **Context:** The problem, constraints, and driving forces.
2. **Options Considered:** Viable options evaluated with pros and cons.
3. **Decision:** The chosen path and rationale.
4. **Consequences:** The positive, negative, and neutral trade-offs resulting from the decision.

---

## Consequences

### Positive
- Decisions are explicit, searchable, and version-controlled.
- New contributors can immediately understand historical context and rejected alternatives.
- Changes to architectural contracts require conscious review and updates.

### Negative
- Minor documentation overhead before landing major structural changes.

### Neutral
- An ADR template (`docs/decisions/_template.md`) must be maintained.
