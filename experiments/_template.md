# Experiment Note: [EXPERIMENT-ID / TITLE]

- **Date:** [YYYY-MM-DD]
- **Author:** [Member Name]
- **Target Stage / Issue:** [e.g. S18 / ISS-041]

> **Pre-Execution Gate:** The **Hypothesis** and **Stop Rule** sections must be written, reviewed, and committed *before* launching any computational run.

---

## 1. Hypothesis

[State the primary hypothesis in precise, falsifiable terms. Specify the primary evaluation metric (e.g., resolve rate, pass@k, tokens per task), the baseline condition, and the expected direction or magnitude of effect.]

---

## 2. Stop Rule

[Define the pre-declared termination and resource-limit conditions.
- Maximum tasks / samples: [e.g., N = 60]
- Early stopping criteria / circuit breaker thresholds: [e.g., abort if infrastructure failure rate > 10%]
- Cost / token ceiling: [e.g., cap at $15.00 or 2,000,000 tokens]
- Floor / ceiling boundaries: [e.g., abort if baseline resolve rate < 10% or > 80%]]

---

## 3. Config Hash

- **Experiment Config Hash:** `[SHA-256 hash computed via ExperimentConfig.compute_hash()]`
- **Git Commit SHA:** `[git rev-parse HEAD]`
- **Active Task Split / Manifest ID:** `[e.g. split-dev-v1 / manifest.json]`
- **Key Parameters:**
  - `model_name`: `...`
  - `temperature`: `...`
  - `context_policy`: `...`
  - `max_steps`: `...`

---

## 4. Result

[Fill this section ONLY after the run has completed or terminated according to the Stop Rule.
- Completed tasks: [M of N]
- Primary metric value with confidence interval: [e.g., resolve rate = 28.3% [22.1%, 35.0%]]
- Token consumption (prompt / cached / generated): [...]
- Financial / GPU-time cost: [...]
- Failure distribution summary: [...]]

---

## 5. Decision

[State the actionable engineering or research decision resulting from the data:
- Was the hypothesis supported, refuted, or inconclusive?
- Does this arm advance to the next screening stage or main confirmatory run?
- What configuration adjustments or fixes are required?]
