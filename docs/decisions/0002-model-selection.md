# ADR 0002: Primary Model Selection and Serving Engine

- **Status:** Accepted
- **Date:** 2026-11-23
- **Deciders:** Coding-Agent Runtime Team
- **Technical Story:** ISS-007 (#15)

---

## Context

The Coding-Agent Runtime requires an open-weights, high-throughput large language model for local inference and reproducible evaluation. The runtime's prefix-caching context manager and tool-execution state machine impose strict operational criteria:

1. **Licence:** Permissive, commercially viable open-source licence (Apache 2.0 or MIT preferred) with zero downstream restrictions or telemetry mandates.
2. **Context Length:** Minimum 32,768 tokens native context length to support multi-file repository context, AST tool outputs, and episode execution histories without premature compaction.
3. **Baseline Resolve Rate:** High baseline pass rate on code benchmark standards (SWE-bench Lite/Verified, HumanEval, and RepoBench) in single-model autonomous mode.
4. **Tool-Call Quality:** High fidelity in structured function calling and JSON Schema adherence, minimizing malformed tool invocations across multi-step episodes.
5. **Prefix-Cache Efficiency:** Predictable KV-cache footprint enabling 80%+ cache hit rates on system prompts and conversation prefixes using vLLM PagedAttention or SGLang RadixAttention.

---

## Options Considered

### 1. Qwen/Qwen2.5-Coder-7B-Instruct (Selected)
- **Licence:** Apache 2.0 (fully permissive open source).
- **Context Length:** 32,768 native tokens with YaRN support up to 128k tokens.
- **Baseline Resolve Rate:** State-of-the-art coding performance in the 7B class (SWE-bench Verified baseline resolve rate exceeding 37% with standard scaffolds; HumanEval 88.4%).
- **Tool-Call Quality:** Native support for function calling and structured JSON tool invocations with low syntax failure rates.
- **Serving Compatibility:** Full first-class support in vLLM (PagedAttention with prefix caching) and SGLang (RadixAttention).
- **Pros:**
  - Standard dense architecture (28 layers, 28 query heads, 4 KV heads via GQA).
  - Compact footprint (~15 GB in FP16 / ~8 GB in AWQ/GPTQ INT4), fitting easily on single consumer or enterprise GPUs (RTX 4090, A10G, A100).
  - Excellent prefix stability across multi-turn trajectories.
- **Cons:**
  - 7B capacity limit on extremely complex multi-file architectural refactoring compared to 70B+ frontier models.

### 2. DeepSeek-Coder-V2-Lite-Instruct (Rejected)
- **Licence:** DeepSeek License Agreement (custom non-standard licence imposing specific commercial restrictions and liability terms).
- **Context Length:** 128,000 tokens.
- **Baseline Resolve Rate:** Strong benchmark metrics comparable to GPT-4-Turbo on coding tasks.
- **Tool-Call Quality:** Good tool-use capability, though occasional hallucinated argument structures on complex multi-argument tools.
- **Reason for Rejection:**
  - **Licence Restrictions:** The custom licence creates deployment barriers for commercial and enterprise redistribution.
  - **Serving & KV-Cache Overheads:** The 16B total / 2.4B active MoE (Mixture-of-Experts) architecture requires loading all 16B parameters into VRAM (requiring >= 32 GB VRAM for unquantized serving), and dynamic expert routing causes non-uniform latency and higher prefix-cache management complexity in commodity environments.

### 3. Meta-Llama/Llama-3.1-8B-Instruct (Rejected)
- **Licence:** Llama 3.1 Community License (conditional licence restricting commercial use above 700M monthly active users and requiring specific attribution).
- **Context Length:** 128,000 tokens.
- **Baseline Resolve Rate:** General-purpose performance; baseline SWE-bench resolve rate significantly lower than code-specialized models (e.g. ~20-25% without extensive specialized prompting).
- **Tool-Call Quality:** Moderate tool-call accuracy; higher syntax failure rate when generating repository diffs and search-and-replace blocks without fine-tuning.
- **Reason for Rejection:**
  - **Lower Coding Resolve Rate:** Generalist model trailing code-specialized 7B/14B checkpoints on real-world repository debugging tasks.
  - **Licence Constraints:** Non-permissive community license with user-count limitations and derivative restrictions.

---

## Decision

We select **Qwen/Qwen2.5-Coder-7B-Instruct** as the default primary model for Coding-Agent Runtime, served via **vLLM** with automatic fallback to **SGLang** and an offline mock server for CI/development.

### Technical Rationale:
1. **Permissive Apache 2.0 Licence:** Allows unconstrained distribution, benchmarking, and commercial deployment.
2. **Superior Coding Capabilities:** Best-in-class resolve rate among open-weight models that fit on single 24GB GPUs.
3. **Native 32k Context Window:** Ample capacity for whole-file context windows and test execution logs.
4. **First-Class Prefix Caching:** Dense GQA architecture maps cleanly to vLLM's PagedAttention prefix caching, achieving >80% prompt token reuse in iterative agent loops.

---

## Consequences

### Positive
- Fully reproducible open-source evaluation with zero proprietary API fees.
- Fits on single commodity GPUs (24 GB VRAM) with room for large batch KV caches.
- Deterministic behavior with reproducible sampling seeds and offline mock server support.

### Negative
- Local inference requires dedicated GPU hardware or external vLLM instance in production compute runs.
- 7B parameter scale requires disciplined context management and accurate tool output formatting.

### Neutral
- System configuration defaults to `Qwen/Qwen2.5-Coder-7B-Instruct` across `scripts/serve.sh` and CLI defaults while retaining configurable model overrides.
