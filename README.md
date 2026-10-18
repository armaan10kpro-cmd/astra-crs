# ASTRA-CRS

**Autonomous Cyber-Reasoning & Verified Repair System**

> DISCOVER → LOCALIZE → REASON → REPAIR → VERIFY → ADVERSARIAL TEST → PROTECT → REPORT

ASTRA-CRS is a defensive research prototype for a **controlled local laboratory**. It combines deterministic security tooling (sanitizers, property checks, adversarial testing, regression suites) with an optional LLM reasoning layer and a Linux eBPF runtime-observation module.

**The LLM is never the final authority on patch correctness.** Every accepted repair requires independent deterministic verification and produces a proof-carrying evidence bundle.

## What it does

1. Builds a deliberately vulnerable synthetic C target
2. Discovers memory-safety flaws via sanitizer-guided fuzzing (with deterministic fallback)
3. Localizes root cause from stack traces
4. Proposes candidate patches via Mock/Local/API model providers
5. Verifies patches in an isolated workspace (compile, symbolic property, adversarial, regression)
6. Judges patches deterministically → `FIX_VERIFIED` or `REJECTED`
7. Generates proof-carrying reports under `reports/<finding_id>/`
8. Demonstrates runtime observation via eBPF (or labelled MOCK mode)

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Installation

**Requirements:** Linux (WSL OK), Python 3.10+, clang with ASan/UBSan

```bash
git clone <repo>
cd astra-crs
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make build
```

Optional: `z3-solver` for Z3 symbolic engine, Node.js for dashboard.

Check environment:

```bash
python3 scripts/check_env.py
```

## Quick start

```bash
make demo
```

This runs the full pipeline and writes reports to `reports/`.

## Demo command

```bash
bash scripts/demo.sh
# or
make demo
```

See [docs/DEMO.md](docs/DEMO.md) for competition walkthrough.

## Dashboard

```bash
make demo
make dashboard-export
cd dashboard && npm install && npm run dev
```

Dark tactical mission-control UI at http://localhost:5173

## eBPF requirements

Real eBPF mode requires Linux, clang BPF target, and optionally libbpf/bpftool. See [docs/EBPF.md](docs/EBPF.md).

**Fallback:** `--mode mock` uses **DEMO / MOCK MODE** — visibly labelled, never pretends to be kernel enforcement.

## Verification philosophy

See [docs/VERIFICATION.md](docs/VERIFICATION.md).

- Deterministic judge aggregates all verification stages
- Symbolic engine checks explicit properties (not universal security proof)
- Adversarial suite attempts to break the repair
- Failed repair attempts preserved (max 3 iterations)

## Project limitations

- Demo patcher handles the controlled buffer-overflow pattern
- eBPF layer is observation/policy signaling, not live binary patching
- AFL++ used only when installed; otherwise deterministic fuzz fallback
- No scanning of external systems — synthetic target only

## Testing

```bash
make test
```

## Documentation

| Doc | Description |
|-----|-------------|
| [BUILD_STATUS.md](docs/BUILD_STATUS.md) | Initial assessment |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design |
| [DEMO.md](docs/DEMO.md) | Demo guide |
| [EBPF.md](docs/EBPF.md) | Runtime layer |
| [VERIFICATION.md](docs/VERIFICATION.md) | Verification philosophy |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues |
| [PITCH_FACTS.md](docs/PITCH_FACTS.md) | Demonstrable claims only |
| [FINAL_STATUS.md](docs/FINAL_STATUS.md) | Build completion report |

## Safety boundary

Controlled defensive lab only. No exploit payloads against external infrastructure. No credential theft. No false claims of universal eBPF memory rewriting.
