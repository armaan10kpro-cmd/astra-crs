# ASTRA-CRS Build Status — Initial Assessment

**Date:** 2026-08-12  
**Assessor:** Autonomous build agent  
**Repository state:** Minimal prototype → full competition build in progress

## Repository inventory (initial)

| Area | Status | Notes |
|------|--------|-------|
| `targets/demo_app/demo_vuln.c` | Working | Stack buffer overflow via unchecked `memcpy` |
| `agent/orchestrator.py` | Partial | Inline discovery + patch; no full pipeline |
| `verification/patcher.py` | Working | Regex-based demo patcher only |
| `verification/symbolic.py` | Partial | Z3 optional; fallback always PASS |
| `verification/regression.py` | Partial | Adversarial mixed into regression |
| `verification/report.py` | Partial | Single `reports/run.md` only |
| `runtime/ebpf/astra_uprobe.bpf.c` | Scaffold | BPF object only; no loader/controller |
| `tests/test_smoke.py` | Working | 2 smoke tests against built binary |
| `scripts/check_env.py` | Working | Tool availability probe |
| `dashboard/` | Missing | Not present |
| `discovery/` | Missing | Not present |
| `reasoning/` | Missing | Not present |
| `verification/adversarial.py` | Missing | Not present |
| `verification/patch_judge.py` | Missing | Not present |
| `scripts/demo.sh` | Missing | Not present |

## Environment probe (WSL Ubuntu)

| Tool | Available | Path / detail |
|------|-----------|---------------|
| `clang` | YES | `/usr/bin/clang` |
| `gcc` / `cc` | YES | `/usr/bin/cc` |
| ASan/UBSan | YES | Via `-fsanitize=address,undefined` |
| `llc` | YES | `/usr/bin/llc` |
| `clang-bpf` target | YES | BPF compile target present |
| `bpftool` | NO | Real eBPF attach requires install |
| `libbpf` loader | NO | User-space controller not yet built |
| `afl-fuzz` | NO | Deterministic fuzz fallback required |
| `z3` (Python) | NO | Install via venv; fallback checker exists |
| `pytest` | NO | Install via venv |
| `docker` | NO | Not required |
| `node` / `npm` | TBD | Required for dashboard build |

## Architecture (initial)

```
demo_vuln.c → orchestrator.py (monolithic)
                 ├─ discover (inline)
                 ├─ patcher.generate_candidate
                 ├─ symbolic.verify_buffer_property
                 └─ regression.verify
reports/run.json + run.md
```

**Gaps vs target architecture:**

- No structured `finding` JSON schema
- No separate DISCOVER / REASON / ADVERSARIAL / JUDGE stages
- No proof-carrying patch directory per finding
- No model abstraction layer
- No bounded repair iteration (N=3)
- No eBPF user-space controller or mock runtime API
- No dashboard

## Test status (initial)

```
make build          → PASS (clang + ASan)
pytest tests/       → BLOCKED (pytest not installed system-wide)
make demo           → Previously produced FIX_VERIFIED in reports/run.json
```

## eBPF support status

- **BPF source:** Present (`runtime/ebpf/astra_uprobe.bpf.c`)
- **Compile test:** clang BPF target available
- **Attach/runtime:** Not implemented; mock mode only
- **Claim boundary:** Observation/telemetry only — no arbitrary memory rewriting

## Model availability

- No local LLM wired in initial prototype
- Patch plan is hard-coded in orchestrator
- `MockProvider` will supply deterministic patches for offline demo

## Implementation plan

1. Create `discovery/` pipeline with structured findings
2. Create `reasoning/` with Local/OpenAI/Mock providers
3. Split verification: adversarial, patch_judge, proof reports
4. Enhance target with regression suite + fuzz entry point
5. Implement eBPF controller + labelled mock mode
6. Build React dashboard (Vite/TS)
7. Add `scripts/demo.sh` one-click demo
8. Comprehensive unit + e2e tests
9. Complete documentation set

## Build progress

This file will be updated at completion in `docs/FINAL_STATUS.md`.
