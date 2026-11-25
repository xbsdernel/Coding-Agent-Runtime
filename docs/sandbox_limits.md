# Sandbox Resource Limits

This document describes the cgroup v2 resource limits applied to every Docker
sandbox spawned by the Coding-Agent Runtime.  All limits have safe defaults
that prevent a runaway agent from destabilising the host, and each one can be
overridden per-experiment through the `sandbox_limits` field of
`ExperimentConfig`.

---

## Default Limits

| Limit | Default | cgroup v2 knob | Rationale |
|---|---|---|---|
| `memory_limit_mb` | 256 MiB | `memory.max` | Enough for single-file Python tasks; prevents host OOM from agent leaks |
| `cpu_quota_us` | 50 000 µs | `cpu.max` numerator | 50 % of one core per 100 ms period; keeps host responsive under many parallel containers |
| `pids_limit` | 64 | `pids.max` | Generous for a single agent but blocks fork-bomb exploits |
| `network_disabled` | `true` | Docker `--network none` | Prevents data exfiltration and uncontrolled package installs |
| `no_new_privileges` | `true` | `no_new_privs` seccomp flag | Disallows setuid/setgid privilege escalation inside the container |

---

## Per-Experiment Override

Add a `sandbox_limits` block to your experiment YAML / JSON config:

```yaml
experiment_id: my-experiment
model_name: gpt-4o-mini
sandbox_limits:
  memory_limit_mb: 512     # Allow 512 MiB for a larger task
  cpu_quota_us: 100000     # Allow a full core
  pids_limit: 128
  network_disabled: true
  no_new_privileges: true
```

In Python:

```python
from codeagent import ExperimentConfig, SandboxLimits

cfg = ExperimentConfig(
    experiment_id="my-experiment",
    model_name="gpt-4o-mini",
    sandbox_limits=SandboxLimits(memory_limit_mb=512, cpu_quota_us=100_000),
)
```

> **Important**: always keep `network_disabled=True` and `no_new_privileges=True`
> in production runs.  Disabling them weakens the security boundary between the
> agent and the host.

---

## Mapping to Docker SDK Arguments

| `SandboxLimits` field | Docker SDK kwarg | Notes |
|---|---|---|
| `memory_limit_mb` | `mem_limit="256m"` | String accepted by docker-py |
| `cpu_quota_us` | `cpu_quota=50000` | Period is always 100 000 µs |
| `pids_limit` | `pids_limit=64` | Requires cgroup v2 on the host |
| `network_disabled` | `network_disabled=True` | Equivalent to `--network none` |
| `no_new_privileges` | `security_opt=["no-new-privileges"]` | Requires Docker ≥ 1.11 |

---

## Relationship Between `SandboxLimits` and `SandboxConfig`

`SandboxLimits` lives in `ExperimentConfig` (experiment-level, serialisable,
hashed into `config_hash`).  `SandboxConfig` is the runtime object passed to
`DockerSandbox`; it may carry additional transient settings (image name, user).

The recommended pattern is to construct a `SandboxConfig` from `SandboxLimits`
at run time:

```python
from codeagent.sandbox import DockerSandbox, SandboxConfig
from codeagent.schemas import SandboxLimits

limits: SandboxLimits = cfg.sandbox_limits  # from ExperimentConfig
sandbox_cfg = SandboxConfig(
    image="python:3.12-slim",
    memory_limit_mb=limits.memory_limit_mb,
    cpu_quota=limits.cpu_quota_us,
    pids_limit=limits.pids_limit,
    network_disabled=limits.network_disabled,
    no_new_privileges=limits.no_new_privileges,
)
with DockerSandbox(sandbox_cfg) as sb:
    result = sb.exec(["python", "solution.py"])
```
