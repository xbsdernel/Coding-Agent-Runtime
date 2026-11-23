# Tool-Call Parser: Mode Comparison and Selection

- **Author:** Coding-Agent Runtime Team
- **Issue:** ISS-010 (#18)
- **Target Model:** `Qwen/Qwen2.5-Coder-7B-Instruct`
- **Evaluation Samples:** 50 fixed prompt scenarios per mode
- **Date:** 2026-11-24

---

## 1. Tool Definitions (JSON Schema)

We evaluate model performance against two canonical repository manipulation tools:

### Tool 1: `view_file`
```json
{
  "name": "view_file",
  "description": "Read file contents or specific line ranges within working directory.",
  "parameters": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "Relative path to file."
      },
      "start_line": {
        "type": "integer",
        "description": "1-based starting line number (optional)."
      },
      "end_line": {
        "type": "integer",
        "description": "1-based ending line number (optional)."
      }
    },
    "required": [
      "path"
    ]
  }
}
```

### Tool 2: `edit_file`
```json
{
  "name": "edit_file",
  "description": "Perform precise search-and-replace modification on an existing file.",
  "parameters": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "Relative path to file to modify."
      },
      "old_str": {
        "type": "string",
        "description": "Target string to replace (must match exactly)."
      },
      "new_str": {
        "type": "string",
        "description": "Replacement string."
      }
    },
    "required": [
      "path",
      "old_str",
      "new_str"
    ]
  }
}
```

---

## 2. Experimental Benchmark Results (50 Calls per Mode)

| Mode | Malformed Rate | Median Latency (ms) |
|---|---|---|
| **Native Tool Calling** | 4.0% | 118.0 ms |
| **Plain-Text Action Format** | 14.0% | 142.0 ms |
| **Guided Decoding** | 0.0% | 214.0 ms |

---

## 3. Analysis of Failure Modes & Latency Dynamics

1. **Native Tool Calling (ChatML `<tool_call>`):**
   - High structural reliability with a low malformed rate of **4.0%** (2/50).
     Failures occur primarily on rare unterminated JSON brackets in multi-line code diffs.
   - Lowest median latency (**118.0 ms**) because Qwen2.5-Coder was instruction-tuned
     specifically on `<tool_call>` tokens without runtime grammar overhead.
   - 100% prefix-cache compatible with vLLM PagedAttention.

2. **Plain-Text Action Format (ReAct Style):**
   - Highest malformed rate of **14.0%** (7/50). Frequent failure modes include
     hallucinated tool names, missing `Action Input:` prefixes, and invalid unescaped string
     delimiters when passing code blocks containing quotes.
   - Median latency is **142.0 ms**, suffering from lengthier preamble thought generation.

3. **Guided Decoding (Grammar-Constrained Schema):**
   - Completely eliminates structural malformed calls (**0.0%** error rate) by masking invalid
     next-token logits at each step.
   - Severe latency degradation (**214.0 ms**, an 80%+ increase over Native). Logit masking
     across large vocabularies introduces significant synchronization barriers and partially
     disrupts prefix caching in current vLLM/Outlines implementations.

---

## 4. Decision for Stage 6 (Agent Episode Loop)

We decide that Stage 6 (S6) will start with **Native Tool Calling** as the primary interaction
mode, supplemented by runtime schema validation and an automated retry-with-error feedback
mechanism on malformed calls. Native tool calling provides the optimal balance of ultra-low
latency (118.0 ms), high structural accuracy (96.0% valid), and native
prefix-cache alignment in vLLM. While Guided Decoding achieves zero malformed calls, its 80%+
latency penalty and prefix-cache synchronization overhead make it cost-prohibitive as a
default; guided decoding will instead serve as an opt-in fallback mode when an episode
encounters consecutive validation failures.
