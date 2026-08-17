# eBPF Runtime Layer

## Scope (honest)

ASTRA-CRS uses eBPF for **supported** runtime observation and policy signaling:

- uprobes/uretprobes on `parse_message()`
- ring-buffer telemetry events
- user-space policy decisions at application boundary

It does **not** claim:

- arbitrary user-space machine code rewriting
- universal live memory patching
- kernel-enforced source repair

Permanent remediation is always a **source-level patch** rebuilt and independently verified.

## Files

| File | Purpose |
|------|---------|
| `runtime/ebpf/astra_uprobe.bpf.c` | BPF program — uprobe entry probe |
| `runtime/ebpf/controller.py` | attach/detach/events/policy/mock |

## Modes

| Mode | Flag | Behaviour |
|------|------|-----------|
| MOCK | `--mode mock` | Labelled **DEMO / MOCK MODE** — simulated events |
| dry-run | `--mode dry-run` | Compiles BPF object only |
| real | `--mode ebpf` | BPF compile + observer attach when toolchain available |

## Requirements (real mode)

- Linux with BPF support
- `clang` with `-target bpf`
- libbpf + bpftool (optional for full attach)
- Target binary with symbol `parse_message` (not stripped)

## Build BPF object

```bash
clang -O2 -g -target bpf -c runtime/ebpf/astra_uprobe.bpf.c -o runtime/ebpf/astra_uprobe.bpf.o
```

## API

```python
from runtime.ebpf.controller import create_shield

shield = create_shield(root, mode="mock")
shield.attach("/path/to/demo_vuln")
shield.simulate_suspicious_call(64)
print(shield.event_stream())
```

## Fallback

When `bpftool`/libbpf unavailable, controller falls back to MOCK mode automatically and labels output accordingly.

See also: `docs/EBPF_SETUP.md` (legacy scaffold notes).
