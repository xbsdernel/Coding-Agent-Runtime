# Learning Roadmap — Project B: Coding-Agent Runtime

Oct 29, 2026 · @ahmed osama

## How to use this roadmap

Work through the 46 topics in the order of the next section: each needs only topics above it, and each is due before the first build stage that uses it, directly or through a later topic. Stage IDs (S1–S35) are the ones in the implementation workflow.

Assumed background: Python, and PyTorch from your computer-vision work. No prior agent, LLM-serving or sandboxing knowledge. If you have already done the Project A roadmap, skip every card whose 'Ready when' you can pass cold. The likeliest overlaps are Python craft (T2), Git and CI (T3), tracing (T5), LLM inference and serving (T6–T7), structured output (T14), the statistics basics (T27–T29) and prompt injection (T38).

Order is checked: a script confirmed that none of the 46 topics appears before a prerequisite, and that every topic lands before the first stage that needs it.

Effort: about 293 h in total (278 h core and 15 h for the two optional topics), of which 221 h fall due before S18, the K-B check. These are my estimates for reading plus the practice task. Skip any topic whose 'Ready when' check you can pass cold.

Two passes: pass 1 (Learn, Practice) happens just before the stage. Pass 2 happens after that stage's experiment is written up: answer the 'Ready when' check, and the deep-understanding list at the end, with your own numbers.

Practice tasks are the first spike of the stage's real code, so keep them in the repo, not in throwaway notebooks.

Card fields: Needs = prerequisite topics · Due before = the earliest stage that uses the topic, directly or through a later topic · h = estimated hours.

## Learning order at a glance

Study top to bottom. Every prerequisite sits above the topic that needs it, and each topic is due before the stage named in its row. Hours include the practice spike. Phases: P0 foundations before S1 · P1 tasks, sandbox and model server (S2–S7) · P2 runtime core (S8–S13) · P3 measurement machinery (S14–S17) · P4 pilot, hardening and pre-registration (S18–S21) · P5 experiments and cost validation (S22–S27) · P6 analysis (S28–S30) · P7 reporting and the optional stretches (S31–S35).

| # | Topic | Phase | Needs | Due before | h |
| --- | --- | --- | --- | --- | --- |
| T1 | Research habits: papers, decision records, pre-registration notes | P0 | none | S1 scaffold | 4 |
| T2 | Python project craft: packaging, tests, typed schemas | P0 | none | S1 scaffold | 6 |
| T3 | Git, tags and a first CI workflow | P0 | T2 | S1 scaffold | 5 |
| T4 | ReAct loops and their failure modes | P0 | T1 | S1 scaffold | 8 |
| T5 | Tracing and observability: spans, JSONL, metrics | P0 | T2 | S1 scaffold | 5 |
| T6 | LLM inference basics: tokens, prefill and decode, KV cache | P1 | none | S2 model server | 8 |
| T7 | Serving open models with vLLM or SGLang, and choosing a model | P1 | T6 | S2 model server | 8 |
| T8 | Chat templates, tool-call parsers and tokenizer details | P1 | T7 | S2 model server | 8 |
| T9 | Issue-resolution benchmarks, graders and contamination | P1 | T1 | S3 task layer | 8 |
| T10 | Linux processes, signals and resource limits | P1 | none | S4 sandbox | 6 |
| T11 | Docker for experiments: images, exec, snapshots, limits | P1 | T2, T10 | S4 sandbox | 8 |
| T12 | Async Python, HTTP clients, timeouts and retries | P1 | T2 | S5 adapter | 8 |
| T13 | Sampling and decoding: temperature, seeds, non-determinism | P1 | T7 | S5 adapter | 4 |
| T14 | Tool calling and structured output: JSON Schema, guided decoding | P1 | T2, T8 | S5 adapter | 6 |
| T15 | Agent-computer interface design and edit formats | P1 | T4 | S6 tool layer | 8 |
| T16 | Code search, patches and syntax checks | P1 | T15 | S6 tool layer | 5 |
| T17 | Designing micro-repositories and test traps | P1 | T4, T9 | S7 micro-suite | 4 |
| T18 | Budgets, stall detection and state machines for agent loops | P2 | T4, T12 | S8 agent loop | 5 |
| T19 | Deterministic replay and golden-trace testing | P2 | T5, T18 | S10 replay | 5 |
| T20 | Trace viewers with Streamlit or FastAPI, and token charts | P2 | T5 | S11 viewer v0 | 4 |
| T21 | Reading mini-SWE-agent and SWE-agent after your first loop | P2 | T15, T18 | S12 context policies | 4 |
| T22 | Context economics and prefix-cache mechanics | P2 | T6, T8 | S12 context policies | 10 |
| T23 | Engine metrics: Prometheus and cached-token counters | P2 | T5, T7 | S12 context policies | 4 |
| T24 | Context policies: masking, summarisation, notes files | P2 | T4, T22 | S12 context policies | 8 |
| T25 | Test-time compute: planning, reflection, verifiers, best-of-n | P2 | T4, T18 | S13 hooks | 10 |
| T26 | Reward hacking, test tampering and clean graders | P2 | T4, T9 | S13 hooks | 4 |
| T27 | Estimation, resampling and paired designs | P3 | T1 | S14 statistics | 8 |
| T28 | Reliability metrics: `pass@k`, `pass^k`, variance components | P3 | T27 | S14 statistics | 8 |
| T29 | Paired tests, non-inferiority and multiple comparisons | P3 | T27 | S14 statistics | 8 |
| T30 | Property-based and parity testing for statistical code | P3 | T2, T27 | S14 statistics | 4 |
| T31 | Cost modelling: cached versus uncached tokens | P3 | T22, T24 | S15 cost model | 6 |
| T32 | Result stores: Parquet, DuckDB and pandas | P3 | T2 | S16 platform | 6 |
| T33 | Job scheduling, concurrency limits and spend caps | P3 | T12, T18 | S16 platform | 6 |
| T34 | CI for sandboxed and replay-based tests | P3 | T3, T11, T19 | S17 CI gate | 4 |
| T35 | Pilot studies, calibration and power analysis | P4 | T28, T29 | S18 pilot | 8 |
| T36 | Sandbox hardening and threat modelling | P4 | T10, T11 | S19 hardening | 8 |
| T37 | Fault injection and resilience testing | P4 | T18, T19, T33 | S19 hardening | 5 |
| T38 | Prompt injection through repository content | P4 | T4 | S19 hardening | 6 |
| T39 | Pre-registration and confirmatory design | P4 | T1, T35 | S21 pre-registration | 6 |
| T40 | Successive halving and budgeted screening | P5 | T29, T39 | S22 interface screen | 5 |
| T41 | Validating a cost model against engine counters | P5 | T23, T31 | S25 cost validation | 5 |
| T42 | Failure analysis: taxonomies, LLM-assisted labelling, agreement | P6 | T4, T14, T27 | S28 taxonomy | 8 |
| T43 | Reading results: intervals, margins and honest verdicts | P6 | T29, T39 | S29 analysis | 6 |
| T44 | Reporting: write-up, demo, negative results, reproduction | P7 | T1, T43 | S31 annotated cases | 8 |
| T45 | Evaluating injection defences: attack success versus utility (optional) | P7 | T38, T39 | S34 security slice | 5 |
| T46 | Rejection-sampling fine-tuning and reward hacking in training (optional) | P7 | T25, T26 | S35 fine-tuning | 10 |

Total 293 h: P0 28 · P1 81 · P2 54 · P3 50 · P4 33 · P5 10 · P6 14 · P7 23. Of these, 221 h are due before S18 (K-B), and 15 h (T45 and T46) are optional.

## Phase 0 · Foundations before S1 · 28 h

Finish all five before you write scaffold code, but skim what you already know (most of T2, the Git half of T3). The new parts are the decision-record and pre-registration habit (T1), the failure modes of agent loops (T4) and how to design a trace (T5).

### T1 · Research habits: papers, decision records, pre-registration notes · \~4 h

**Needs** none · **Due before** S1 scaffold

**Learn**

- Three-pass paper reading (skim, grasp, reconstruct). For each paper keep four lines: the claim, the setup, the baseline it beat, and the number you would try to reproduce.
- Decision records: one page per frozen artifact (context, options, decision, consequences). Your records for the model, the tool format and the task splits are a deliverable, so start the habit now.
- Experiment notes written in this order: hypothesis, stop rule, config hash, result, decision. The hypothesis and the stop rule come before the run. This is the small version of the pre-registration you freeze at S21.

**Practice** S1: in the repo, add `docs/decisions/0001-record-decisions.md` and `experiments/_template.md` with those five fields.

**Ready when** you can fill the decision template for a past choice in ten minutes, and your first experiment note has its stop rule written before any run.

**Resources** [How to Read a Paper](https://web.stanford.edu/class/ee384m/Handouts/HowtoReadPaper.pdf) · [ADR site](https://adr.github.io/) · [A Recipe for Training Neural Networks](https://karpathy.github.io/2019/04/25/recipe/)

### T2 · Python project craft: packaging, tests, typed schemas · \~6 h

**Needs** none · **Due before** S1 scaffold

**Learn**

- A `src/` layout package with `pyproject.toml`, an editable install and a CLI entry point for the harness.
- pytest fixtures, parametrization, marks (`slow`, `docker`, `gpu`) and golden-file tests. The replay tests (S10) and the statistics parity tests (S14) are built on these.
- Typed models (Pydantic or validated dataclasses) for every frozen interface: trace event, config, result row, budget. Validate at the boundary, fail loudly, and carry a schema version in each record.
- Deterministic runs: seeded RNGs, sorted iteration, stable content hashes in file names.

**Practice** S1: the package, a CLI stub, the four schemas (trace, config, result, budget) as typed models, and a round-trip test for each.

**Ready when** `pip install -e . && pytest -q` passes from a clean clone, and renaming a schema field breaks a test instead of passing silently.

**Resources** [Python Packaging User Guide](https://packaging.python.org/en/latest/) · [pytest](https://docs.pytest.org/en/stable/) · [Pydantic](https://pydantic.dev/docs/validation/latest/get-started/) · [Understanding JSON Schema](https://json-schema.org/understanding-json-schema)

### T3 · Git, tags and a first CI workflow · \~5 h

**Needs** T2 · **Due before** S1 scaffold

**Learn**

- Single-author Git hygiene: small commits, an annotated tag for every frozen artifact (for example `schemas-v1`), and a hash manifest so that 'frozen' is checkable.
- Pin what the code runs on: a lockfile, a base-image digest, and `git describe` stamped into every run record.
- A first GitHub Actions workflow: lint, type check and fast tests on every push. S17 adds the replay and sandbox jobs.
- Clean-tree discipline: a run is tied to a commit, so the launcher should refuse to start on a dirty tree.

**Practice** S1: put the repo under Git, add the workflow, tag `v0-scaffold`, and make the CLI stub print the commit hash and exit non-zero on a dirty tree.

**Ready when** a failing test turns the workflow red, and a fresh clone at the tag gives the same test result.

**Resources** [Pro Git](https://git-scm.com/book/en/v2) · [GitHub Actions](https://docs.github.com/en/actions/about-github-actions/understanding-github-actions)

### T4 · ReAct loops and their failure modes · \~8 h

**Needs** T1 · **Due before** S1 scaffold

**Learn**

- The thought, action, observation loop and what each message in it carries. Read ReAct first, then the SWE-agent paper for what a repair loop adds: an interface designed for the model rather than for a human.
- The workflow versus agent distinction, and the smallest loop that works: one model, a few tools, a step budget, a stop condition.
- The failure modes you will meet again and again: repeated identical actions, context blow-up from long outputs, edits that fail to apply, premature submission, ignored tool errors, runaway cost. They seed the error taxonomy at S8 and the labelled taxonomy at S28.
- What a step budget, a token budget and a stall rule each protect against, so the budget spec you freeze at S1 has the right fields.

**Practice** S1 prep: run one loop by hand. Paste an issue and a file listing into a chat model, play the tool layer yourself for ten steps, and note every observation size and every failure. Use the notes to settle the trace event and budget fields at S1.

**Ready when** you can name each failure mode above with one example from your hand run, and your budget spec states step, token and wall-clock limits with a reason for each.

**Resources** [ReAct](https://arxiv.org/abs/2210.03629) · [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) · [SWE-agent](https://arxiv.org/abs/2405.15793)

### T5 · Tracing and observability: spans, JSONL, metrics · \~5 h

**Needs** T2 · **Due before** S1 scaffold

**Learn**

- A trace as an append-only JSONL event log: one event per model call, tool call and state change, each with run id, step number, timestamps, token counts and a content hash. The trace schema you freeze at S1 is this.
- Span thinking from OpenTelemetry (parent and child, attributes, events) without adopting the whole stack. Borrow the GenAI attribute names where they fit.
- Latency and token counts as distributions, not averages: histograms, percentiles, and why a mean hides the tail.
- What must be logged so a failure can be replayed: the exact request payload, the raw response, and the tool arguments before and after parsing.

**Practice** S1: the trace event schema, a writer that appends validated events, and a reader that rebuilds a run's token totals from the file.

**Ready when** a hand-written 20-event trace validates and round-trips, and its token totals are recomputed from the file alone.

**Resources** [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/) · [OTel GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/) · [Prometheus histograms](https://prometheus.io/docs/practices/histograms/) · [Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)

## Phase 1 · Tasks, sandbox and model server (S2–S7) · 81 h

The model-server topics (T6–T8) gate G0 at S2, and the task and sandbox topics (T9–T11) gate the K-A check at S4. The two tracks do not depend on each other, so read them in the order you will build; the pacing section says which to put first. T12–T17 can wait until you reach S5, S6 and S7.

### T6 · LLM inference basics: tokens, prefill and decode, KV cache · \~8 h

**Needs** none · **Due before** S2 model server

**Learn**

- Tokens versus characters, and the decoder-only forward pass at the level needed to count work: attention over the whole prefix, one new token per decode step.
- Prefill versus decode: why prefill is compute-bound and batches well, why decode is memory-bandwidth-bound, and what time to first token and inter-token latency measure.
- The KV cache: what is stored per layer and per token, how to compute its size from layers, KV heads, head dimension and dtype, and why long agent contexts exhaust memory before they exhaust compute.
- Back-of-envelope arithmetic: model weights in memory, cache bytes per token, and a rough tokens-per-second ceiling on your GPU. You reuse these numbers in the cost model (S15).

**Practice** S2 prep: for the model you plan to serve, work out weights memory, KV bytes per token and the maximum cached tokens at your batch size on paper, then compare with the server's startup log.

**Ready when** your paper numbers for KV bytes per token and maximum cached tokens are within about 20% of the server's own log.

**Resources** [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) · [Transformer Inference Arithmetic](https://kipp.ly/blog/transformer-inference-arithmetic) · [Hugging Face LLM course, chapter 1](https://huggingface.co/learn/llm-course/chapter1/1)

### T7 · Serving open models with vLLM or SGLang, and choosing a model · \~8 h

**Needs** T6 · **Due before** S2 model server

**Learn**

- Launching an OpenAI-compatible server and the flags that matter: maximum model length, GPU memory fraction, tensor-parallel size, quantisation, prefix caching. Know which startup log lines confirm each one.
- Reading the fit: which model sizes run on your GPU with room left for the cache at a long context, and what quantisation costs in quality and speed.
- Choosing a model for an issue-resolution agent: trained for tool use, holds up at long context, a licence you can live with, and a base resolve rate that is neither near zero nor near the ceiling. The floor and ceiling check at S18 sends you back here when it is not.
- Pick one engine and one model for S2 and record the choice with two rejected alternatives. The choice is a decision record, not a commitment.

**Practice** S2: serve the candidate model, send one chat request and one streamed request with curl, and save the startup log and both request and response pairs as the first entries of the probe report.

**Ready when** a curl call returns a completion, the log shows the context length and cache size you expected, and the decision record names two alternatives with a reason for rejecting each.

**Resources** [vLLM docs](https://docs.vllm.ai/en/latest/) · [SGLang docs](https://docs.sglang.io/) · [SWE-rebench: a continuously updated benchmark for SWE LLMs](https://nebius.com/blog/posts/introducing-swe-rebench)

### T8 · Chat templates, tool-call parsers and tokenizer details · \~8 h

**Needs** T7 · **Due before** S2 model server

**Learn**

- How a chat template turns a message list into one token string: special tokens, roles, where the system prompt sits, and how tool definitions and tool results are rendered.
- What breaks prefix reuse: anything that changes earlier tokens when a new message is appended, such as timestamps, re-rendered tool lists, stripped reasoning from earlier turns, or trailing whitespace. You test this at S2 and again at S12.
- Tool-call parsers: the server turns model text into structured tool calls with a parser chosen per model family. Know what each accepts, what happens on malformed output, and how to bypass it and parse the text yourself.
- Tokenizer details that matter: byte-level BPE, token boundaries across a concatenation, and why tokenising a string in two pieces can differ from tokenising it whole.

**Practice** S2: render one conversation with `apply_chat_template`, tokenise it, append one turn and check that the new token list starts with the old one. Then send a request with one tool schema and record whether the parser returns a valid call.

**Ready when** you can show one prefix-stable conversation and one deliberately broken one (change a single early token), with the server's cached-token counter confirming both.

**Resources** [Chat templates](https://huggingface.co/docs/transformers/chat_templating) · [Tool use](https://huggingface.co/docs/transformers/chat_extras) · [vLLM tool calling](https://docs.vllm.ai/en/stable/features/tool_calling/) · [Tokenizer summary](https://huggingface.co/docs/transformers/tokenizer_summary) · [Let's build the GPT Tokenizer](https://www.youtube.com/watch?v=zduSFxRajkE)

### T9 · Issue-resolution benchmarks, graders and contamination · \~8 h

**Needs** T1 · **Due before** S3 task layer

**Learn**

- What an instance contains: repository, base commit, issue text, the tests that must go from failing to passing, and the tests that must keep passing. How a grader applies the model patch plus the held-out tests in a clean container.
- Known grader weaknesses: weak tests that accept wrong patches, and patches that pass by editing tests. Your grader copies in its own tests and ignores any edits the agent made to test files.
- Contamination: why tasks created before a model's training cutoff overstate its ability, and how continuously collected sets date every task so that you can split by creation date.
- Terminal-style tasks as an out-of-distribution check (S27), and how a task set is stratified by difficulty.

**Practice** S3: take three instances, build each environment image, run the gold patch (must pass) and an empty patch (must fail) through your own grader, and record build time and image size for each.

**Ready when** the gold patch passes and the empty patch fails on all three, and rerunning the grader gives the same verdicts.

**Resources** [SWE-bench](https://arxiv.org/abs/2310.06770) · [SWE-rebench](https://arxiv.org/abs/2505.20411) · [SWE-bench-Live](https://arxiv.org/abs/2505.23419) · [Terminal-Bench](https://arxiv.org/abs/2601.11868)

### T10 · Linux processes, signals and resource limits · \~6 h

**Needs** none · **Due before** S4 sandbox

**Learn**

- Process groups and sessions, and how to kill a whole tree: SIGTERM, a grace period, then SIGKILL. Killing only the parent leaves orphaned children still running tests.
- Timeouts at three levels (command, step, run), and the difference between wall-clock and CPU time.
- cgroup v2 limits for memory, CPU and process count, and how an out-of-memory kill shows up in the exit status.
- Capturing stdout and stderr without deadlocking on a full pipe, and capping an observation at a byte limit while saying that it was cut.

**Practice** S4 prep: a function that runs a shell command with a timeout, kills its whole process tree, caps captured output at a byte limit, and returns exit status, duration and a truncated flag. Test it with a script that spawns 50 sleeping children and one that prints 100 MB.

**Ready when** no child survives a timed-out command, and the 100 MB test returns in under a second with the truncated flag set.

**Resources** [signal(7)](https://man7.org/linux/man-pages/man7/signal.7.html) · [Control Group v2](https://docs.kernel.org/admin-guide/cgroup-v2.html) · [Python subprocess](https://docs.python.org/3/library/subprocess.html)

### T11 · Docker for experiments: images, exec, snapshots, limits · \~8 h

**Needs** T2, T10 · **Due before** S4 sandbox

**Learn**

- Images and layers: one image per repository environment, built once and cached (the images you built at S3).
- Run versus exec: one long-lived container per episode with `exec` for each tool call, versus one container per command. The cost of each is the reset cost you measure at S4.
- Resetting state between episodes: a fresh container from the cached image, a committed snapshot, or a copy-on-write layer. Know what each preserves and what each costs.
- Limits and isolation flags: memory, CPUs, process count, read-only root, network off, non-root user, no new privileges. T36 hardens these later; set sensible defaults now.
- The Docker SDK for Python instead of shelling out: streaming output, exit codes, timeouts.

**Practice** S4: start a container from a cached task image, run three commands through exec with limits, reset it two ways, and time start, exec and reset for each.

**Ready when** you have start, exec and reset times for each reset method on your machine, and a container that exceeds its memory or process limit is killed without touching the host.

**Resources** [Docker: get started](https://docs.docker.com/get-started/) · [Docker SDK for Python](https://docker-py.readthedocs.io/en/stable/) · [Running containers](https://docs.docker.com/engine/containers/run/) · [docker container commit](https://docs.docker.com/reference/cli/docker/container/commit/)

### T12 · Async Python, HTTP clients, timeouts and retries · \~8 h

**Needs** T2 · **Due before** S5 adapter

**Learn**

- asyncio tasks, task groups, semaphores for concurrency limits, cancellation, and how one blocking call stalls the whole loop.
- An HTTP client with separate connect, read, write and pool timeouts, an overall deadline around each call, streamed responses and connection pooling (httpx).
- Retries with exponential backoff and jitter: which errors are safe to retry (timeouts, 429, 5xx) and which are not (malformed requests), and why a retried call is a new sample whose attempts all go in the trace.
- Cancellation and cleanup, so that a killed run does not leak containers or sockets.

**Practice** S5: an async client for your server's chat endpoint with those timeouts and the retry policy, and a fake server that injects delays, 429 responses and dropped connections for tests.

**Ready when** the fake-server tests pass with each fault injected, and the trace records every attempt, including the failed ones.

**Resources** [asyncio: coroutines and tasks](https://docs.python.org/3/library/asyncio-task.html) · [HTTPX timeouts](https://www.python-httpx.org/advanced/timeouts/) · [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)

### T13 · Sampling and decoding: temperature, seeds, non-determinism · \~4 h

**Needs** T7 · **Due before** S5 adapter

**Learn**

- Temperature, top-p and top-k: what each changes, why agents often run at a low but non-zero temperature, and why the sampling settings belong in the experiment config.
- Seeds: the per-request seed in your server and what it does and does not guarantee.
- Sources of non-determinism even at temperature 0: batch composition, floating-point reduction order, kernel choice. Read the nondeterminism write-up and the server's reproducibility page.
- What follows for you: a run is a sample, not a fact, so each task needs several repeats, and a replay stores recorded responses instead of regenerating them (S10).

**Practice** S5: send the same prompt 20 times at temperature 0 and at your chosen temperature, count the distinct outputs, and find the first token where each pair diverges.

**Ready when** you can state, from your own counts, how often temperature 0 still diverges on your server and what that implies for the number of repeats per task.

**Resources** [The Curious Case of Neural Text Degeneration](https://arxiv.org/abs/1904.09751) · [Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference) · [vLLM reproducibility](https://docs.vllm.ai/en/latest/usage/reproducibility/)

### T14 · Tool calling and structured output: JSON Schema, guided decoding · \~6 h

**Needs** T2, T8 · **Due before** S5 adapter

**Learn**

- JSON Schema for tool definitions: types, required fields, enums, and the descriptions the model reads.
- Native tool calling versus a plain-text action format you parse yourself: when each is more reliable on open models, and how you measure it (the malformed-call rate).
- Guided decoding: constrained generation against a schema or grammar, what it guarantees (syntax) and what it does not (correct arguments), and its latency cost.
- A recovery policy for a malformed call: reject with a short message, retry once, count it. The counts become the malformed counters at S5.

**Practice** S5: define two tools as JSON Schema and call the model 50 times on a fixed prompt set in three modes (native tool calling, a text format, guided decoding). Record the malformed-call rate and median latency for each.

**Ready when** you have that three-row table and a one-paragraph decision on which mode S6 starts with.

**Resources** [vLLM structured outputs](https://docs.vllm.ai/en/latest/features/structured_outputs/) · [XGrammar](https://arxiv.org/abs/2411.15100) · [Outlines](https://arxiv.org/abs/2307.09702) · [Understanding JSON Schema](https://json-schema.org/understanding-json-schema)

### T15 · Agent-computer interface design and edit formats · \~8 h

**Needs** T4 · **Due before** S6 tool layer

**Learn**

- Why the interface is an experimental variable: SWE-agent's ablations of search tools, windowed file viewing and lint-checked edits. Read the interface sections of the paper twice.
- The core tool set for a repair agent: view (windowed, with line numbers), search, edit, run, submit. For each, what it returns, its size cap and its error messages.
- Edit formats: whole-file rewrite, search and replace blocks, unified diff, line-range edit. Read Aider's findings on which formats make models lazy or fail to apply, and what a failed apply should say back.
- Tool descriptions and error messages are prompts: short, with an example, and telling the model what to do next. Anthropic's essay on writing tools is the checklist.
- Tool variants are configuration, not code branches. They become the arms of the S22 screen.

**Practice** S6: implement view, search, edit (two formats behind one flag), run and submit against a scratch repository in the sandbox, with one test per tool for its normal output and one for its error output.

**Ready when** every tool has a size cap and a tested error message, and switching the edit format is one config value.

**Resources** [SWE-agent](https://arxiv.org/abs/2405.15793) · [Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents) · [Aider edit formats](https://aider.chat/docs/more/edit-formats.html) · [Aider unified diffs](https://aider.chat/docs/unified-diffs.html)

### T16 · Code search, patches and syntax checks · \~5 h

**Needs** T15 · **Due before** S6 tool layer

**Learn**

- Fast search with ripgrep: ignore rules, file-type filters, context lines, and capping the output so one search cannot flood the context.
- Applying a patch safely: `git apply --check` first, whitespace handling, and reporting a failed hunk in a form the model can fix.
- Cheap syntax checks after an edit (compile the file or parse it with tree-sitter), returning the first error with its line, so a broken edit is rejected before it costs a test run.
- Structure-aware views: a file's functions and classes with line ranges, as a cheaper alternative to viewing the whole file.

**Practice** S6: add the syntax check to your edit tool and a symbol-outline view, then measure observation size for outline versus full view on three real files.

**Ready when** an edit that breaks syntax is rejected with the line number and leaves the file unchanged, and you can quote the outline-to-full size ratio for your three files.

**Resources** [ripgrep user guide](https://github.com/BurntSushi/ripgrep/blob/master/GUIDE.md) · [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) · [git apply](https://git-scm.com/docs/git-apply)

### T17 · Designing micro-repositories and test traps · \~4 h

**Needs** T4, T9 · **Due before** S7 micro-suite

**Learn**

- A micro-suite is a fast, cheap test bed: small repositories with a known, hand-checked fix, each runnable in under a minute. It serves smoke runs, regression tests and CI, not results.
- Seeding difficulty on purpose: a one-line fix, a two-file fix, a fix that needs a search, a flaky test, an unrelated failing test, an issue with a misleading hint.
- Test traps for reward hacking and grader flaws: tests that can be passed by deleting them, by special-casing the test input, or by editing the test file. Each trap has a known expected verdict.
- Invariance checks in the CheckList spirit: renaming files or rewording the issue should not change the grade, which exposes grader and harness bugs.

**Practice** S7: write eight micro-repositories, each with a gold patch and a trap patch, and a script that grades both inside the sandbox.

**Ready when** every gold patch passes, every trap patch is caught by the grader, and the whole suite runs in a few minutes.

**Resources** [pytest](https://docs.pytest.org/en/stable/) · [CheckList](https://arxiv.org/abs/2005.04118) · [SWE-bench](https://arxiv.org/abs/2310.06770)

## Phase 2 · Runtime core: loop, tools, context, hooks (S8–S13) · 54 h

T18 to T21 are small and arrive as the loop starts to run. The heavy ones are T22 (context economics), T24 (context policies) and T25 (test-time compute); schedule them while the smoke run is producing traces you can measure. If K-B is close, T25 is the first thing to cut down to a single planning variant.

### T18 · Budgets, stall detection and state machines for agent loops · \~5 h

**Needs** T4, T12 · **Due before** S8 agent loop

**Learn**

- The loop as an explicit state machine: states (awaiting the model, executing a tool, submitted, budget exhausted, errored), the events that move between them, and one place where termination is decided.
- Budgets that terminate an episode: steps, tokens, wall-clock time and cost, each with its own stop reason in the trace.
- Stall detection: the same action repeated, no file changes across several steps, oscillating edits. Choose the rule and what it does when it fires (warn once, then stop).
- Failure containment: tool exceptions become observations, model errors are retried by the adapter, and no episode ends without a recorded stop reason. The stop reasons are the first draft of the error taxonomy.

**Practice** S8: write the state machine, its budget checks and one stall rule, and unit-test every transition with a scripted fake model and fake tools. No GPU is needed.

**Ready when** a table-driven test reaches each stop reason once, and a run killed halfway leaves a trace that still parses and that the reader reports as unfinished.

**Resources** [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) · [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/) · [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)

### T19 · Deterministic replay and golden-trace testing · \~5 h

**Needs** T5, T18 · **Due before** S10 replay

**Learn**

- Record and replay: store every model response and tool result, then re-run the loop against the recording to test everything except the model. VCR-style cassettes are the pattern.
- What must be pinned for a replay to match: tool-call order, argument canonicalisation, timestamps, random ids, environment variables. What cannot be replayed: the live model and wall-clock timing.
- Golden traces: a few recorded runs that CI replays, comparing the event sequence and the final verdict, with a deliberate procedure for updating them when behaviour changes on purpose.
- Divergence reports: when a replay differs, show the first differing event, not a wall of diff.
- Honesty about non-determinism: a replay tests your code, not the model's variability (T13).

**Practice** S10: record a smoke-run trace, replay it through the loop with the model stubbed from the recording, and make one deliberate change that the replay detects.

**Ready when** the replay reproduces the recorded trace event for event, and a one-line change to a tool's output format fails the golden test with a readable divergence message.

**Resources** [VCR.py](https://vcrpy.readthedocs.io/) · [Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference) · [vLLM reproducibility](https://docs.vllm.ai/en/latest/usage/reproducibility/)

### T20 · Trace viewers with Streamlit or FastAPI, and token charts · \~4 h

**Needs** T5 · **Due before** S11 viewer v0

**Learn**

- A read-only viewer over JSONL traces: a run list, a step timeline, collapsible tool outputs and the verdict.
- Token charts: context length per step, split into cached and uncached when the server reports it, plus cumulative cost. These charts show a context policy working or failing.
- Designing for scanning: truncate long outputs with an expand control, highlight stop reasons and errors, and link each step to its raw event.
- Streamlit for a quick local app, or FastAPI with a small page if you want something deployable. Pick one; either is enough.

**Practice** S11: a viewer that loads one smoke trace and shows the timeline, a context-length chart and the stop reason.

**Ready when** you can open any smoke trace and find the step where the context first passed half the window in under a minute.

**Resources** [Streamlit](https://docs.streamlit.io/) · [FastAPI](https://fastapi.tiangolo.com/) · [Fundamentals of Data Visualization](https://clauswilke.com/dataviz/)

### T21 · Reading mini-SWE-agent and SWE-agent after your first loop · \~4 h

**Needs** T15, T18 · **Due before** S12 context policies

**Learn**

- Read them after you have written your own loop, so that the differences stand out: how mini-SWE-agent keeps its loop to a short file with a shell as the only tool, and how SWE-agent structures its tool configuration and history.
- How each reference handles history: full append, history processors that elide older observations, summarisation hooks. These are the baselines for S12.
- Where your loop makes a different choice, and whether you can say why. Record each difference as a one-line decision.
- What each logs, and what you would need to add to reproduce their numbers.

**Practice** S12 prep: write a one-page table comparing your loop with both references on loop structure, tools, history handling and stop rules.

**Ready when** the table names at least three deliberate differences, each with a reason.

**Resources** [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent) · [SWE-agent repository](https://github.com/princeton-nlp/SWE-agent) · [SWE-agent paper](https://arxiv.org/abs/2405.15793)

### T22 · Context economics and prefix-cache mechanics · \~10 h

**Needs** T6, T8 · **Due before** S12 context policies

**Learn**

- The cost of a step with and without prefix caching: an append-only history re-sends every earlier token at each step, so uncached work grows with the square of the number of steps while cached work grows linearly. Derive both formulas yourself.
- How the cache works: matching on exact token prefixes (vLLM hashes fixed-size blocks, SGLang keeps a radix tree), eviction under memory pressure, and the cached-token counters in responses or metrics.
- Which context edits keep a prefix and which destroy it: appending keeps it, masking an old observation changes everything after the first masked token, summarising rewrites the middle. This is the ranking you test at S12.
- Pricing on hosted APIs (cache reads much cheaper than uncached input, writes sometimes dearer) as the reason the effect matters, and where hosted caching differs from a local engine: explicit breakpoints and a time to live.
- Long-context position effects: where an observation sits changes whether the model uses it.

**Practice** S12 prep: write the cost of one 40-step episode under append-only history with and without a cache, using your measured prompt and observation sizes, then check it against the cached-token counter from one real smoke run.

**Ready when** you can derive both cost formulas on a blank page, say which of the three edit types keep the prefix, and your predicted cached-token count for one real run is within about 10% of the engine's counter.

**Resources** [PagedAttention](https://arxiv.org/abs/2309.06180) · [SGLang and RadixAttention](https://arxiv.org/abs/2312.07104) · [vLLM prefix caching](https://docs.vllm.ai/en/stable/design/prefix_caching/) · [Lost in the Middle](https://arxiv.org/abs/2307.03172) · [Context Engineering for AI Agents: Lessons from Building Manus](https://manus.im/en/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) · [Anthropic prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

### T23 · Engine metrics: Prometheus and cached-token counters · \~4 h

**Needs** T5, T7 · **Due before** S12 context policies

**Learn**

- Scraping an engine's `/metrics` endpoint: counters versus gauges versus histograms, and how to read deltas and rates.
- The metrics that matter here: prompt tokens processed, cached (prefix hit) tokens, generated tokens, queue time and cache usage. Names differ by engine and version, so find yours in its docs.
- Reading counters as deltas around an episode: snapshot before and after, and what breaks attribution when other requests run at the same time (validate with a single stream).
- Per-request usage fields in the response, when the server returns them, as a cross-check.

**Practice** S12: a small scraper that snapshots the counters before and after one episode and writes the deltas beside the trace, as the start of the cache impact log.

**Ready when** for one single-stream episode the prompt-token delta equals the prompt tokens summed from the trace, and the cached-token delta is above zero and below it.

**Resources** [vLLM metrics](https://docs.vllm.ai/en/stable/design/metrics/) · [Prometheus overview](https://prometheus.io/docs/introduction/overview/) · [Prometheus histograms](https://prometheus.io/docs/practices/histograms/)

### T24 · Context policies: masking, summarisation, notes files · \~8 h

**Needs** T4, T22 · **Due before** S12 context policies

**Learn**

- The policy menu: full history, rolling observation masking (keep the last k observations and replace older ones with a short placeholder), chunked masking (mask in blocks of N steps so the prefix is stable between mask events), LLM summarisation, and a notes file the agent writes and rereads.
- What the literature says. The Complexity Trap compares observation masking with LLM summarisation on software-engineering agents and finds masking competitive at lower cost; ACON learns compression guidelines for history and observations; MemGPT frames memory as paging. For each paper note the model, the benchmark and the limits of the claim. Your fresh-task results test them.
- Placeholders must be deterministic and short, and must say what was removed so that the agent can fetch it again.
- The parameters you will sweep: k, N and the placeholder text. The sweep is the S23 screen.
- The link to caching: rolling masking edits the oldest visible observation at every step, so roughly the last k observations are uncached each time; chunked masking edits only every N steps, so the prefix stays valid in between. You model this at S15.

**Practice** S12: full history, rolling masking and chunked masking behind one interface (a single function from history to message list), with a test that each one keeps or breaks the token prefix as predicted.

**Ready when** for a recorded 40-step history you can print the longest common token prefix between consecutive steps for each policy, and it matches your T22 prediction.

**Resources** [The Complexity Trap](https://arxiv.org/abs/2508.21433) · [ACON](https://arxiv.org/abs/2510.00615) · [MemGPT](https://arxiv.org/abs/2310.08560) · [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

### T25 · Test-time compute: planning, reflection, verifiers, best-of-n · \~10 h

**Needs** T4, T18 · **Due before** S13 hooks

**Learn**

- Repeated sampling: coverage rises with the number of samples (Large Language Monkeys), but choosing the right sample needs a verifier. Verifier options for code: run the tests the issue implies, run a reproduction script the agent wrote, or use a model as judge.
- Planning, verification and reflection as hooks: a plan written before acting and reread at checkpoints; a check before submitting (run the reproduction and the existing tests); a reflection step after a failed test. Each is a small piece of loop code behind a switch.
- Why reflection helps less than hoped on weak signals: its gains depend on reliable feedback.
- Comparison points: test generation for ranking candidates (CodeT) and the Agentless pipeline of localisation, repair and validation without an agent loop.
- Budget matching: a variant that spends more tokens is not comparable with one that spends fewer unless you match the budget or report cost per resolved task.

**Practice** S13: a pre-submit verification hook (run the reproduction script and the targeted tests, return the result to the agent) and a planning hook, each behind a config switch, tested on the micro-suite.

**Ready when** each hook can be switched off with one config value and leaves the trace otherwise unchanged, and you can state the extra tokens each hook costs on the micro-suite.

**Resources** [Large Language Monkeys](https://arxiv.org/abs/2407.21787) · [Training Verifiers](https://arxiv.org/abs/2110.14168) · [Reflexion](https://arxiv.org/abs/2303.11366) · [CodeT](https://arxiv.org/abs/2207.10397) · [Agentless](https://arxiv.org/abs/2407.01489) · [Scaling Test-Time Compute Optimally](https://arxiv.org/abs/2408.03314)

### T26 · Reward hacking, test tampering and clean graders · \~4 h

**Needs** T4, T9 · **Due before** S13 hooks

**Learn**

- Documented behaviour under test pressure: editing or deleting tests, special-casing test inputs, reading the grader's files, exiting early with a success code, patching the test runner, and exploiting the scoring code itself.
- Defences you can build: grade in a separate container with its own copy of the tests; hash the protected files and fail any episode that changed them; deny writes to those paths in the sandbox; scan diffs for deleted assertions and new skip markers.
- Detection beyond hashes: read a sample of passing trajectories, not only failing ones.
- Monitoring a model's reasoning has uses and limits; penalising bad thoughts can teach concealment.
- Report tamper-flag counts per arm. A variant that passes more because it tampers more has failed, not won.

**Practice** S13: the tamper guard (a protected-path hash check plus a diff scan for deleted assertions and new skip markers), run on the eight trap patches from the micro-suite.

**Ready when** every trap patch is flagged, no gold patch is flagged, and a flagged episode is marked as a tamper in its result row.

**Resources** [Recent Frontier Models Are Reward Hacking](https://metr.org/blog/2025-06-05-recent-reward-hacking/) · [Reward Hacking in Reinforcement Learning](https://lilianweng.github.io/posts/2024-11-28-reward-hacking/) · [Monitoring Reasoning Models for Misbehavior](https://arxiv.org/abs/2503.11926)

## Phase 3 · Measurement machinery (S14–S17) · 50 h

T27 to T30 gate the statistics module (S14). S14 needs only the result schema, so it can run beside the runtime work whenever you want a change of pace; the table places these topics here because nothing in S8 to S13 needs them. T31 to T34 follow the runtime topics they build on.

### T27 · Estimation, resampling and paired designs · \~8 h

**Needs** T1 · **Due before** S14 statistics

**Learn**

- The unit of analysis is the task, not the episode. Repeated runs of one task are correlated, so the effective sample size is the number of tasks.
- Bootstrap confidence intervals for a pass rate and for the difference between two configurations on the same tasks (paired). Percentile versus BCa, how many resamples, and why resampling episodes instead of tasks gives intervals that are too narrow.
- The cluster bootstrap: resample tasks, then episodes within each task. Compare it with the naive interval on your own data.
- Paired designs: same tasks and same seeds across arms, so task difficulty cancels. Why pairing often removes more variance than extra seeds do.
- Standard errors for evals in the sampling-theory style: clustered standard errors and variance reduction from repeated answers.
- Coverage checking: simulate data with a known pass rate and confirm that 95% intervals cover it about 95% of the time.

**Practice** S14: a bootstrap module with paired and cluster modes, and a coverage simulation that runs in under a minute.

**Ready when** on synthetic data with strong task effects your cluster interval is visibly wider than the naive episode interval, and coverage is close to 95%.

**Resources** [Adding Error Bars to Evals](https://arxiv.org/abs/2411.00640) · [SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) · [Dror et al., Testing Statistical Significance in NLP](https://aclanthology.org/P18-1128/) · [statsmodels statistics](https://www.statsmodels.org/stable/stats.html)

### T28 · Reliability metrics: pass@k, pass^k, variance components · \~8 h

**Needs** T27 · **Due before** S14 statistics

**Learn**

- `pass@k` (at least one of k attempts succeeds) and `pass^k` (all k succeed), estimated from n recorded attempts per task with the unbiased estimators built on binomial coefficients, computed per task and then averaged over tasks. Derive both from the probability of drawing k of the n attempts.
- What each measures: `pass@k` is capability with retries and a perfect verifier; `pass^k` is reliability when every run counts. A configuration can win on one and lose on the other.
- The tau-bench argument for `pass^k` and the Codex paper's definition of `pass@k`.
- Variance components: how much outcome variance is task, how much is configuration, how much is seed noise, and what that implies for how many seeds buy what (a mixed-effects model or a simple decomposition).
- Reporting the whole curve over k with intervals, not a single k.

**Practice** S14: functions for both metrics from raw per-attempt results, validated against brute-force enumeration on small cases.

**Ready when** your estimators match brute-force enumeration for n up to 8, and you can explain why `pass^k` falls with k while `pass@k` rises.

**Resources** [Evaluating Large Language Models Trained on Code](https://arxiv.org/abs/2107.03374) · [tau-bench](https://arxiv.org/abs/2406.12045) · [statsmodels mixed models](https://www.statsmodels.org/stable/mixed_linear.html) · [Adding Error Bars to Evals](https://arxiv.org/abs/2411.00640)

### T29 · Paired tests, non-inferiority and multiple comparisons · \~8 h

**Needs** T27 · **Due before** S14 statistics

**Learn**

- McNemar's test for paired binary outcomes: only the discordant pairs matter (A passes and B fails, A fails and B passes). Exact versus asymptotic versions.
- The paired bootstrap on the difference as the default interval, and what to do when the test and the interval seem to disagree.
- Non-inferiority: to claim that a cheaper configuration is not worse, fix a margin before running and show that the lower confidence bound stays above the negative margin. Without a margin the claim cannot be tested. Equivalence testing (two one-sided tests) is the two-sided version.
- Multiple comparisons: with six hypotheses, adjust (Holm, Benjamini-Hochberg) or declare one primary, and decide the family before the data arrive.
- Effect sizes in plain units: points of resolve rate and tokens per resolved task, each with an interval. A significant difference of one point is not a finding you can act on.

**Practice** S14: a paired difference with bootstrap interval, an exact McNemar test, a non-inferiority check with a stated margin, and a Holm adjustment, each with a unit test on a hand-computed example.

**Ready when** you can compute a McNemar p-value and a Holm adjustment by hand for a table of your own, and your code agrees.

**Resources** [statsmodels McNemar](https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html) · [Understanding Equivalence and Noninferiority Testing](https://pmc.ncbi.nlm.nih.gov/articles/PMC3019319) · [Equivalence Tests: A Practical Primer](https://pmc.ncbi.nlm.nih.gov/articles/PMC5502906) · [statsmodels multipletests](https://www.statsmodels.org/dev/generated/statsmodels.stats.multitest.multipletests.html)

### T30 · Property-based and parity testing for statistical code · \~4 h

**Needs** T2, T27 · **Due before** S14 statistics

**Learn**

- Parity tests: compare your estimators with a reference implementation on the same inputs (SciPy for the bootstrap, statsmodels for McNemar and Holm) and fail beyond a tolerance. This is the parity result that G2 checks at S14.
- Property tests with Hypothesis: `pass^k` never exceeds `pass@k`, both metrics stay between 0 and 1, an interval contains its point estimate, the difference of an arm with itself is exactly zero, and permuting the tasks leaves results unchanged.
- Seeded determinism so that stochastic tests do not flake, and how to choose tolerances for resampling estimators.
- Where the tests live: fast parity and property tests run on every push.

**Practice** S14: a parity suite against SciPy and statsmodels plus five Hypothesis properties. Break one estimator on purpose and watch the suite fail.

**Ready when** the parity suite passes, and a one-character change to an estimator fails at least one test.

**Resources** [Hypothesis](https://hypothesis.readthedocs.io/) · [SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) · [statsmodels statistics](https://www.statsmodels.org/stable/stats.html)

### T31 · Cost modelling: cached versus uncached tokens · \~6 h

**Needs** T22, T24 · **Due before** S15 cost model

**Learn**

- Turning a token trace into a cost estimate: uncached prompt tokens, cached prompt tokens and generated tokens, each at its own price, with GPU-seconds as the alternative unit for a local engine.
- Closed forms for each policy: append-only without a cache, append-only with an ideal cache, rolling masking, chunked masking. Derive them for your own step sizes and see where each assumption can fail: block-granular caching, attention cost growing with context, placeholder tokens.
- The chunk-size trade-off: a larger N keeps the prefix longer but carries more stale context. The optimum the formula gives is a hypothesis to test, not a result.
- Calibration: fit prices from pilot data (S18), then compare predicted with measured on held-out episodes.
- Cost per resolved task as a headline metric next to resolve rate, with its interval.

**Practice** S15: a cost function that takes a trace, a policy and a price table and returns uncached, cached and generated tokens per step, with a unit test for each closed form.

**Ready when** for each policy your function reproduces the closed-form uncached-token count on a synthetic 40-step trace exactly, and prices come from a table, not from code.

**Resources** [vLLM prefix caching](https://docs.vllm.ai/en/stable/design/prefix_caching/) · [Anthropic prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [SGLang and RadixAttention](https://arxiv.org/abs/2312.07104)

### T32 · Result stores: Parquet, DuckDB and pandas · \~6 h

**Needs** T2 · **Due before** S16 platform

**Learn**

- A results table with one row per episode and a stable schema: task id, arm, seed, outcome, tokens by kind, cost, wall-clock time, stop reason, tamper flag, manifest id. Append-only: never edit a row, add a corrective one.
- Parquet for storage: columnar, typed, compressed, partitioned by experiment. Why not CSV for results.
- DuckDB for analysis: SQL over Parquet files, window functions for per-task aggregation, joins to the task index.
- pandas for the last mile (groupby, merge, pivot), keeping heavy aggregation in SQL.
- Provenance: every row carries the manifest id, git commit and config hash, so any number can be traced back.

**Practice** S16: write 1,000 synthetic episode rows to Parquet through the result schema, then compute per-arm pass rate and per-task pass counts in DuckDB.

**Ready when** the same aggregate computed in DuckDB and in pandas agrees, and a row without a manifest id is rejected on write.

**Resources** [DuckDB: Parquet](https://duckdb.org/docs/current/data/parquet/overview) · [DuckDB Python client](https://duckdb.org/docs/current/clients/python/reference/) · [Apache Parquet](https://parquet.apache.org/docs/) · [pandas groupby](https://pandas.pydata.org/docs/user_guide/groupby.html)

### T33 · Job scheduling, concurrency limits and spend caps · \~6 h

**Needs** T12, T18 · **Due before** S16 platform

**Learn**

- A work queue of (task, arm, seed) jobs with idempotent keys, so that a rerun skips finished jobs and resumes unfinished ones.
- Concurrency limits per resource: requests in flight to the model server, containers on the host, API rate limits. Semaphores and backpressure.
- Spend caps: a running cost estimate checked before each launch, a hard stop and a clear record when the cap is reached, and pre-flight estimates from the cost model.
- Circuit breakers: stop launching when the failure rate jumps (server down, image build failing) instead of burning budget on doomed jobs.
- Overload and retry storms, from the SRE chapters on handling overload.

**Practice** S16: a runner that executes 200 fake jobs with a concurrency limit, a simulated failure burst and a spend cap, and that resumes correctly after being killed and restarted.

**Ready when** killing the runner midway and restarting it executes each job exactly once overall, and the cap stops launches within one job of the limit.

**Resources** [Handling Overload](https://sre.google/sre-book/handling-overload/) · [Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html) · [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) · [asyncio: coroutines and tasks](https://docs.python.org/3/library/asyncio-task.html)

### T34 · CI for sandboxed and replay-based tests · \~4 h

**Needs** T3, T11, T19 · **Due before** S17 CI gate

**Learn**

- What belongs in CI: fast unit tests, the replay and golden-trace tests (no GPU, no network), the parity tests, and the micro-suite run against a stubbed model.
- Docker inside CI: running the sandbox on a hosted runner, caching image layers between runs, and keeping the job to a few minutes.
- The gate as a merge rule: a change that alters replay output or a golden trace must say so explicitly, by updating the trace in the same commit.
- The ML Test Score rubric as a checklist, not a score: tests for data, model development, infrastructure and monitoring.
- Keeping CI honest: flaky tests are quarantined with a note, never retried silently.

**Practice** S17: a workflow that runs lint, unit, parity, replay and the stubbed micro-suite on each push, with the image layer cache enabled.

**Ready when** a change that alters a golden trace fails CI until the trace is updated deliberately, and the workflow finishes in under ten minutes.

**Resources** [GitHub Actions](https://docs.github.com/en/actions/about-github-actions/understanding-github-actions) · [The ML Test Score](https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/) · [Continuous Integration](https://martinfowler.com/articles/continuousIntegration.html) · [pytest](https://docs.pytest.org/en/stable/)

## Phase 4 · Pilot, hardening and pre-registration (S18–S21) · 33 h

T35 is due before the pilot (S18) and is the last topic before the K-B check. T36 to T38 serve hardening (S19), which runs beside the pilot, and T39 gates pre-registration (S21), the freeze point for the confirmatory study.

### T35 · Pilot studies, calibration and power analysis · \~8 h

**Needs** T28, T29 · **Due before** S18 pilot

**Learn**

- What a pilot is for: estimating the base resolve rate, the discordance rate between arms, tokens per step, cost per episode and failure rates. It sets feasibility and parameters; it does not test hypotheses.
- Floor and ceiling: a base rate under 10% or over 80% leaves no room to see effects, so you change the model or the difficulty stratum and rerun. This is the S18 loop.
- Power for paired binary outcomes: the standard error of a paired difference is about the square root of the discordance rate divided by the number of tasks, and the smallest effect you can detect at 80% power is about 2.8 standard errors. Work it out for your own discordance estimate.
- Calibration: using pilot data to set prices for cached and uncached tokens, expected tokens per step and the budgets for the main runs.
- Small-sample honesty: 20 tasks give wide intervals. Keep pilot tasks out of the main split, and do not pick hypotheses by peeking at pilot effects.

**Practice** S18 prep: use the power tool from S14 to tabulate the smallest detectable effect for N from 100 to 500 and discordance from 0.1 to 0.3, and write the pilot report template listing what the pilot must estimate.

**Ready when** your table shows about 8 points at N = 250 and about 5.6 points at N = 500 for a discordance rate of 0.2, and the template states a stop-or-go rule for floor and ceiling.

**Resources** [Adding Error Bars to Evals](https://arxiv.org/abs/2411.00640) · [Sample Size Justification](https://lakens.github.io/statistical_inferences/08-samplesizejustification.html) · [Dror et al., Testing Statistical Significance in NLP](https://aclanthology.org/P18-1128/)

### T36 · Sandbox hardening and threat modelling · \~8 h

**Needs** T10, T11 · **Due before** S19 hardening

**Learn**

- A threat model for an agent that runs untrusted code: the agent itself (misbehaviour, tampering), repository content (prompt injection, malicious build scripts) and the tools (network, filesystem, processes). List assets (host, model server, API keys, grader, other episodes), actors and entry points; give each threat a mitigation and a test.
- The limits of container isolation: a shared kernel makes a container a boundary against accidents more than against a determined attacker. Rootless mode, user namespaces, seccomp profiles, dropped capabilities, no privileged flag, no Docker socket mount.
- Stronger isolation options (a user-space kernel such as gVisor, or microVMs) and their cost in speed and compatibility. Decide with the reset-cost numbers from S4.
- Network policy: default deny, an allowlist for package mirrors only if tasks need one, and no route from the container to the model server or to metadata endpoints.
- Secrets: nothing the agent could read or exfiltrate belongs inside the container.
- Escape tests as unit tests, each of which must be blocked.

**Practice** S19: write the threat table and ten escape tests (write outside the workspace, read host paths, connect out, exceed memory, exceed process count, fill the disk, read grader files, run as root, reach the Docker socket, signal host processes), run them against sandbox v0 and fix what fails.

**Ready when** all ten escape tests pass on the hardened sandbox, and each row of the threat table points to the test or setting that covers it.

**Resources** [Docker Engine security](https://docs.docker.com/engine/security/) · [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html) · [gVisor](https://gvisor.dev/docs/) · [capabilities(7)](https://www.man7.org/linux/man-pages/man7/capabilities.7.html)

### T37 · Fault injection and resilience testing · \~5 h

**Needs** T18, T19, T33 · **Due before** S19 hardening

**Learn**

- Faults to inject: model-server timeouts, 5xx responses, partial streams and slow responses; container start failure; a full disk; a killed runner; corrupted trace lines.
- Hypothesis-driven fault tests in the chaos-engineering style: define the steady state (every job ends in a recorded outcome), inject a fault, check that the state holds.
- Resume semantics: a killed run restarts from its last durable step or is cleanly marked failed, with no duplicate rows and no half-written trace files.
- Cascading failure: retries multiply load, and budgets and breakers are what stop it.
- Running faults deterministically in CI with the fake server from T12 and the replay harness.

**Practice** S19: tests that inject each fault above using the fake server, a failing container start and a kill signal, and that assert the final state.

**Ready when** every injected fault ends in either a clean recorded outcome or a clean resume, with no orphaned containers left behind.

**Resources** [Principles of Chaos Engineering](https://principlesofchaos.org/) · [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/) · [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)

### T38 · Prompt injection through repository content · \~6 h

**Needs** T4 · **Due before** S19 hardening

**Learn**

- The agent reads untrusted text constantly: issue bodies, code comments, READMEs, test output, dependency files. Any of it can carry instructions (indirect prompt injection).
- What an injected instruction can make a coding agent do: run commands, leak environment variables, edit the grader or the tests, fetch from the network.
- Why the model alone is not a defence, and the layers around it: least-privilege tools, no secrets in the environment, network deny, filtering of observations, delimiting untrusted text (spotlighting), and instruction-hierarchy training in the model.
- Measuring attack success separately from task success, and the benchmarks that exist for it (BIPIA here, AgentDojo and InjecAgent in T45).
- A practical threat model from Willison's series on prompt injection.

**Practice** S19: plant five injected instructions in small scratch repositories (README, code comment, test output, issue text, config file) that ask the agent to leak a canary string or edit a protected file, and record whether the sandbox and the tamper guard stop each one.

**Ready when** for each planted instruction you can say whether the model complied, whether the sandbox stopped the effect, and which layer would have caught it.

**Resources** [Greshake et al., indirect prompt injection](https://arxiv.org/abs/2302.12173) · [OWASP LLM01](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) · [BIPIA](https://arxiv.org/abs/2312.14197) · [The Instruction Hierarchy](https://arxiv.org/abs/2404.13208) · [Spotlighting](https://arxiv.org/abs/2403.14720) · [Willison on prompt injection](https://simonwillison.net/series/prompt-injection/)

### T39 · Pre-registration and confirmatory design · \~6 h

**Needs** T1, T35 · **Due before** S21 pre-registration

**Learn**

- What a pre-registration contains: hypotheses, primary metric, comparisons, analysis method, exclusion rules, sample size and stopping rule, multiplicity handling, and what counts as inconclusive.
- Confirmatory versus exploratory: the dev set explores and screens, and the main set confirms only what you specified in advance. Anything else is labelled exploratory.
- Researcher degrees of freedom: why flexible analysis inflates false positives, and the habits that stop it (freeze the task-set hash, the code tag and the config before the first main run).
- Declaring primary and secondary hypotheses and the family for multiplicity, and deciding in advance what you will conclude if an interval spans the margin.
- Where to keep it: a dated file in the repo with a tag and a hash, optionally copied to a public registry.

**Practice** S21: start the pre-registration file from a template and write two of your hypotheses in full, each with primary metric, test, margin and decision rule. Tag the repo.

**Ready when** someone else could run your analysis from the file without asking you a question, and each hypothesis states what you will conclude for effect, no effect and inconclusive.

**Resources** [Preregistration (Center for Open Science)](https://www.cos.io/initiatives/prereg) · [The preregistration revolution](https://pmc.ncbi.nlm.nih.gov/articles/PMC5856500) · False-Positive Psychology (Simmons, Nelson and Simonsohn, 2011; search by title)

## Phase 5 · Experiments and cost validation (S22–S27) · 10 h

Only two new topics here. The experiments reuse what you have built, so most of this phase is running jobs and reading results. Use the spare hours for pass 2 of earlier topics: answer their 'Ready when' checks with your own numbers.

### T40 · Successive halving and budgeted screening · \~5 h

**Needs** T29, T39 · **Due before** S22 interface screen

**Learn**

- Successive halving: give many candidates a small budget, keep the best fraction, and rerun the survivors with more budget. Why it suits a dev set of about 60 tasks and a handful of expensive variants.
- The danger: at 60 tasks differences are noisy, and early rounds can eliminate the best variant by luck. Use paired comparisons on the same tasks, and keep ties instead of forcing a winner.
- Screening rules that belong in the pre-registration: the number of rounds, the fraction kept, the ranking metric (resolve rate and cost) and the tie-break.
- One factor at a time against the base, then a few interaction checks on the combinations that matter.
- Everything selected on the dev set is a hypothesis for the main set, not a result.

**Practice** S22 prep: simulate a two-round screen on synthetic outcomes with known effects, and measure how often the truly best variant survives at 60 tasks.

**Ready when** you can quote the probability that the best variant survives two rounds at 60 tasks, and your tie rule follows from it.

**Resources** [Non-stochastic Best Arm Identification (successive halving)](https://arxiv.org/abs/1502.07943) · [Hyperband](https://arxiv.org/abs/1603.06560)

### T41 · Validating a cost model against engine counters · \~5 h

**Needs** T23, T31 · **Due before** S25 cost validation

**Learn**

- Predicted versus measured: for each policy, compare the modelled uncached, cached and generated tokens per episode with the engine's counters from single-stream runs.
- Residual analysis: where the model is wrong (block granularity, eviction under load, placeholder tokens, template changes) and by how much, summarised as relative error per policy with intervals.
- Recalibration without overfitting: fit price or overhead parameters on some episodes, test on others, and report the error on the held-out part.
- Knowing the regime where the model should not be trusted: very long contexts, concurrent load, a different engine version.
- Reporting the outcome as a finding even when the model is wrong. Wrong but understood is a result.

**Practice** S25: per-policy tables of predicted versus measured tokens from the engine counter logs, with a held-out split for any parameter you refit.

**Ready when** you can quote the relative error of the model for each policy on held-out episodes, and explain the largest residual.

**Resources** [scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) · [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html) · [vLLM metrics](https://docs.vllm.ai/en/stable/design/metrics/)

## Phase 6 · Analysis (S28–S30) · 14 h

Two topics, both due once results exist. Both are about reading data honestly: how failures are classified and how a verdict is worded.

### T42 · Failure analysis: taxonomies, LLM-assisted labelling, agreement · \~8 h

**Needs** T4, T14, T27 · **Due before** S28 taxonomy

**Learn**

- Building a taxonomy from the data: read trajectories, group failures bottom-up, merge and split until the labels are mutually exclusive with clear decision rules, then label top-down. MAST is a worked example: a taxonomy grown from traces, with an LLM annotator validated against human labels.
- LLM-assisted labelling: a rubric prompt with class definitions and examples, structured output (T14) so that labels parse, and a validation set that you label yourself.
- Judge biases: position, verbosity and self-preference. Use a judge from a different model family than the agent, randomise the order, and check against your own labels.
- Agreement statistics: Cohen's kappa between you and the judge and between you at two different times, a per-class confusion table, and the level of agreement at which you will still report a class share.
- Reporting failure classes per arm with intervals (T27). A policy that shifts the mix of failures is a finding.

**Practice** S28: label 50 failed trajectories yourself against the draft taxonomy, run the LLM labeller on the same 50, and compute kappa and a confusion table.

**Ready when** kappa is reported with an interval, the largest confusion cell is explained, and any class with weak agreement is merged or marked unreliable.

**Resources** [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) · [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685) · [Large Language Models are not Fair Evaluators](https://arxiv.org/abs/2305.17926) · [LLM Evaluators Recognize and Favor Their Own Generations](https://arxiv.org/abs/2404.13076) · [Interrater reliability: the kappa statistic](https://www.biochemia-medica.com/en/journal/22/3/10.11613/BM.2012.031) · [scikit-learn cohen\_kappa\_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html)

### T43 · Reading results: intervals, margins and honest verdicts · \~6 h

**Needs** T29, T39 · **Due before** S29 analysis

**Learn**

- Reading an interval against a margin: three outcomes only (supports, refutes, inconclusive), decided by where the interval sits relative to zero and to the margin. Write the rule down before the data arrive.
- What p-values do and do not say, and why a non-significant result is not evidence of no effect when the interval is wide.
- Reporting negative and inconclusive results as prominently as positive ones. The negative-results file is a deliverable.
- Placebo and sanity checks: a no-op arm, a rerun of the base configuration, a comparison with shuffled labels. If the placebo shows an effect, the noise is larger than you think.
- Keeping confirmatory and exploratory results, and dev and main results, in separate tables with no pooling across splits.
- Comparing with the literature: when your fresh-task result disagrees with a published claim, list the differences (model, benchmark, scaffold, budget) before concluding anything.

**Practice** S29: draft the verdict table from a synthetic results file: each hypothesis, its interval, its margin and the rule-derived verdict, plus a placebo row.

**Ready when** every verdict follows from its rule without a judgement call, and you can show a synthetic case for each of the three outcomes.

**Resources** [The ASA statement on p-values](https://doi.org/10.1080/00031305.2016.1154108) · [Equivalence Tests: A Practical Primer](https://pmc.ncbi.nlm.nih.gov/articles/PMC5502906) · [Adding Error Bars to Evals](https://arxiv.org/abs/2411.00640) · [Dror et al., Testing Statistical Significance in NLP](https://aclanthology.org/P18-1128/)

## Phase 7 · Reporting and optional stretches (S31–S35) · 23 h

T44 is the only core topic here (8 h). T45 and T46 (15 h together) are optional and start only after the definition-of-done audit at S33.

### T44 · Reporting: write-up, demo, negative results, reproduction · \~8 h

**Needs** T1, T43 · **Due before** S31 annotated cases

**Learn**

- The structure of the write-up: question, setup, pre-registered hypotheses with verdicts, exploratory findings, failure analysis, cost results, threats to validity and limitations. Negative results get the same prominence as positive ones.
- Documentation that makes results trustworthy: a model-card-style description of the runtime and the models, a datasheet-style description of the task sets and splits, and a limitations section.
- Annotated cases: choose trajectories that illustrate each failure class and each verdict, name the step where it went wrong, and link each case to the viewer.
- Charts that carry one message each: intervals rather than bars alone, one colour per arm throughout, and axes that start at zero when rates are compared.
- A reproduction command that rebuilds the main tables from the result store, and a demo script for a three-minute path from task to trace to verdict.

**Practice** S31: pick three failed and two successful trajectories from the main traces, annotate each in one paragraph with the step number, and open each in the viewer.

**Ready when** a colleague can follow one annotated case from the viewer to the verdict without your help, and your write-up outline has a heading for every hypothesis, including the negative ones.

**Resources** [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993) · [Datasheets for Datasets](https://arxiv.org/abs/1803.09010) · [Fundamentals of Data Visualization](https://clauswilke.com/dataviz/) · [Architectural Decision Records](https://adr.github.io/) · [The Turing Way](https://book.the-turing-way.org/)

### T45 · Evaluating injection defences: attack success versus utility (optional) · \~5 h

**Needs** T38, T39 · **Due before** S34 security slice

**Learn**

- The metrics: attack success rate, utility under attack and utility without attack. A defence that blocks everything has zero attack success and zero utility.
- The benchmarks: AgentDojo (dynamic tasks with attacks and defences) and InjecAgent (indirect injection against tool-using agents). Adapt their attack styles to repository content such as READMEs, comments and test output.
- Defence families to compare: delimiting untrusted text, a tool allowlist, a confirm-before-write rule for protected paths, a detector on observations, and the model's own instruction hierarchy. Record each one's cost in tokens and in utility.
- Pre-registration applies here too: fix the attack set and the success rule before running.
- A paired design: the same tasks with and without injection.

**Practice** S34: a small injection set derived from your T38 planted examples, run as defended and undefended arms on the same tasks, with attack success and utility tabulated with intervals.

**Ready when** your table has attack success and utility for every arm with intervals, and the best defence is chosen by a rule you stated in advance.

**Resources** [AgentDojo](https://arxiv.org/abs/2406.13352) · [InjecAgent](https://arxiv.org/abs/2403.02691) · [BIPIA](https://arxiv.org/abs/2312.14197) · [The Instruction Hierarchy](https://arxiv.org/abs/2404.13208) · [Spotlighting](https://arxiv.org/abs/2403.14720)

### T46 · Rejection-sampling fine-tuning and reward hacking in training (optional) · \~10 h

**Needs** T25, T26 · **Due before** S35 fine-tuning

**Learn**

- Turning verified trajectories into training data: keep only episodes that the clean grader passed and the tamper guard did not flag, format them as messages in the exact template the model is served with, and deduplicate and balance by task.
- Rejection-sampling fine-tuning and its relatives (STaR, RFT, and the SWE-Gym and SWE-smith pipelines): what each filters on, how many samples per task, and how much data helped.
- LoRA through PEFT as the low-cost way to adapt a model on your own GPU: which weights to adapt, rank, learning rate and epochs. Evaluate on held-out tasks, never on tasks you trained on.
- Where reward hacking enters: if the grader can be gamed, training on gamed successes amplifies the hack. Filter with the tamper guard, read samples by hand, and evaluate on tasks created after your training data.
- The evaluation: compare the tuned model with the base on held-out tasks under the same pre-registered rules. Negative results count.
- Compute realism: this is an optional stretch, so cap its time and cost up front.

**Practice** S35: build the training file from the main traces (clean and unflagged, only the tasks the split file allows for training), run a small LoRA fine-tune on one GPU, and evaluate it on the held-out tasks.

**Ready when** the training file has counts of included and excluded episodes with reasons, and the tuned model is compared with the base on held-out tasks with an interval.

**Resources** [STaR](https://arxiv.org/abs/2203.14465) · [Scaling Relationship on Learning Mathematical Reasoning](https://arxiv.org/abs/2308.01825) · [SWE-Gym](https://arxiv.org/abs/2412.21139) · [SWE-smith](https://arxiv.org/abs/2504.21798) · [LoRA](https://arxiv.org/abs/2106.09685) · [PEFT quicktour](https://huggingface.co/docs/peft/quicktour)

## Stage gates

This is the pass 1 gate: before a stage starts, you should be able to do the thing in the last column. It is the minimum, not the full check. After the stage's write-up, run each card's 'Ready when' (pass 2).

| Before | Topics due | Entry gate: you can |
| --- | --- | --- |
| S1 scaffold | T1–T5 | install from a clean clone and run the tests, write a decision record, name the failure modes of an agent loop, and sketch a trace event with its fields |
| S2 model server | T6–T8 | work out KV bytes per token for your model, serve it, and show that a chat template keeps an earlier prefix when a turn is appended |
| S3 task layer | T9 | say what a grader runs, and why a gold patch must pass and an empty patch must fail |
| S4 sandbox | T10–T11 | kill a whole process tree on timeout, cap an output, and run one command in a limited container from a cached image |
| S5 adapter | T12–T14 | call a fake server with timeouts and retries, say why temperature 0 can still diverge, and get one valid tool call back from the server |
| S6 tool layer | T15–T16 | list the tools an agent needs with a size cap and an error message for each, and check a patch with `git apply --check` |
| S7 micro-suite | T17 | write a gold patch and a trap patch for one small repository and say which check catches the trap |
| S8 agent loop | T18 | draw the state machine with its stop reasons and say what the stall rule checks |
| S10 replay | T19 | say what a replay pins and what it cannot test, and why a golden trace needs an update procedure |
| S11 viewer v0 | T20 | load a JSONL trace into a step list and plot context length per step |
| S12 context policies | T21–T24 | derive the cost of an append-only history with and without a cache, say which edits break a prefix, and read the engine's cached-token counter |
| S13 hooks | T25–T26 | say what a verification hook costs in tokens, and name four ways an agent can pass tests without fixing the bug |
| S14 statistics | T27–T30 | compute `pass@k` and `pass^k` by hand for a small table, and explain why resampling episodes makes intervals too narrow |
| S15 cost model | T31 | write the uncached-token count for rolling and chunked masking over a 40-step trace |
| S16 platform | T32–T33 | write rows to Parquet through the schema, query them in DuckDB, and say what makes a job safe to rerun |
| S17 CI gate | T34 | say which tests run without a GPU or a network, and how CI reacts to a changed golden trace |
| S18 pilot | T35 | state the floor and ceiling rule, and the smallest detectable effect for 250 tasks at your discordance rate |
| S19 hardening | T36–T38 | list the assets and entry points of your sandbox, name five escape attempts, and show how a README can carry an injected instruction |
| S21 pre-registration | T39 | write one hypothesis with metric, test, margin and the conclusion for an interval that spans the margin |
| S22 interface screen | T40 | state the screen's rounds, fraction kept and tie rule, and what a screening result may claim |
| S25 cost validation | T41 | name the held-out episodes and the error measure you will report |
| S28 taxonomy | T42 | label ten failed trajectories against a draft taxonomy and compute kappa against a second labelling |
| S29 analysis | T43 | turn an interval and a margin into a verdict by rule, with a case for each of the three outcomes |
| S31 annotated cases | T44 | outline the write-up and annotate one trajectory down to the failing step |
| S34 security slice | T45 | explain attack success versus utility, and why blocking everything is not a defence |
| S35 fine-tuning | T46 | list the filters that keep tampered or leaked episodes out of the training file |

S9, S20, S23, S24, S26, S27, S30, S32 and S33 introduce no new topics. S9 reuses T7, T17 and T18, S20 reuses T9 and T35, S23 reuses T23, T24 and T40, S24 reuses T25 and T40, S26 reuses T29 and T39, S27 reuses T9 and T33, S30 reuses T36 and T43, S32 reuses T43 and T44, and S33 is checked against the mastery map (next section).

## Can you explain it? The B13 mastery map

B13 in the project file lists ten things you should be able to do without notes. Each row names the topics that teach it, the stage after which you have your own numbers to explain it with, and the evidence to have ready. Run this table in pass 2, not before.

| # | B13: you can… | Topics | After stage | Evidence to have ready |
| --- | --- | --- | --- | --- |
| 1 | Derive the token and cost profile with and without prefix caching, say which context policies preserve the cache, and compare your model with engine counters | T22, T24, T31, T41 | S12, S15, S25 | the predicted-versus-measured table, the cache impact log and the H2 verdict |
| 2 | Explain what in a chat template or serialisation breaks prefix reuse | T8, T22 | S12, S25 | the probe report and the cache findings with the measured token loss |
| 3 | Explain `pass@k` versus `pass^k` and compute both from raw results | T28 | S14, S29 | both metrics from the main results with intervals, and the H6 verdict |
| 4 | Do a power calculation and say which claims the data can and cannot support | T29, T35, T39 | S21, S29 | the power table, and verdicts marked inconclusive wherever the smallest detectable effect exceeds the effect |
| 5 | Explain the paired cluster bootstrap and why resampling episodes overstates certainty | T27, T29 | S14, S29 | the coverage simulation, and cluster versus naive interval widths on your own data |
| 6 | Describe the sandbox threats and mitigations, including prompt injection through repository text | T10, T11, T36, T38 | S19 | the threat model, the escape tests and the planted-injection results |
| 7 | Explain why interface design matters, with your ablation as evidence | T14, T15, T16 | S22, S26 | the dev screen of interface variants and the H3 verdict |
| 8 | Summarise the observation-masking literature, its limits, and what fresh-task results add | T21, T24 | S26, S29 | a one-page literature summary and the H1 verdict |
| 9 | Walk through three taxonomy failures and what you changed | T4, T20, T42 | S28, S31 | the three annotated failures and their change-log entries |
| 10 | Explain how to turn verified trajectories into training data and where reward hacking enters | T26, T46 (optional) | S32, S35 | a short note on the pipeline, and tamper-flag counts per arm |

If you cannot answer a row aloud in two minutes, go back to the named topic card, then to the experiment note. H1 to H6 are the project file's default hypotheses; if you replaced one, use your own.

## Pacing and the K-B risk

K-B asks for a working runtime, a sandbox and a believable pilot by the end of week 5, and K-A asks for reliable containers by the end of week 2. The hours that fall due before those checks are the schedule risk of this roadmap.

&#91;embedded content: from the learning-order table above · 46 topics, 293 h · ruler at 40 h a week\]

At a full-time 40 h a week, five weeks hold 200 h, yet 221 h of topics fall due before S18, and the build needs the same weeks. P0 and P1 alone are 109 h against the 80 h of weeks 1 and 2. Study cannot simply come first. Plan it like this:

- Run P0 as a ramp before week 1 (28 h). It covers the loop shape, the trace and the schemas that S1 freezes.
- Learn P1 just in time (81 h), one topic ahead of its stage, and let each practice spike be the stage's own code.
- Put the K-A path first: T1 to T3 and T9 to T11 (37 h). S3 and S4 do not read the trace, config or budget schemas, so the sandbox can start once the repo, the interfaces and the result schema exist. T4 to T8 (also 37 h) follow, and T4 and T5 must land before you freeze the trace and budget schemas. Everything due before S4 is 74 h.
- Skim what you know. T2 and T3 alone are 11 h of the estimate, and your Python background likely covers much of both. If you can pass a card's 'Ready when' check cold, move on.
- Cut resources before practice tasks. If the front runs over, read only the first one or two links on each card and keep every practice spike. Do not cut T22, T27 to T29 or T35: the study stands on them.
- Respect K-B. If it is missed, the file says to cut scope to three context policies and one planning variant and carry that into S21. T24 then needs only those three policies and T25 only one variant, and T45 and T46 stay optional.
- Use unattended jobs. Model downloads, image builds (S3), the pilot (S18) and the later screening and main runs (S22 to S27) run without you, so read the next cards while they finish.
- Keep pass 2 cheap. If each experiment note was written as T1 describes, the 'Ready when' and mastery checks are an hour of reading your own results, not a second study session.
