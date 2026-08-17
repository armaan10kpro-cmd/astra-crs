# ASTRA-CRS Upgrade Status & Roadmap

**Date:** 2026-08-13  
**Status:** Autonomous Upgrade In Progress  
**Baseline Test Result:** 17/17 pytest unit/e2e tests PASSED (9.62s)  
**Dashboard Build Result:** `npm run build` PASSED (0.8s)  
**Local LLM Status:** Ollama running `qwen2.5-coder:7b` at `http://127.0.0.1:11434` (Windows host accessible via host IP / localhost)

---

## 1. Initial System Baseline

| Component | Status | Detail |
| :--- | :--- | :--- |
| **Python Environment** | Active (`.venv`) | Python 3.14.4, pytest 9.1.1, z3-solver 4.12+ |
| **Compiler & Target Toolchain** | Active | Ubuntu Clang 21.1.8 with `-fsanitize=address,undefined` |
| **Dashboard** | Active | React 18 + TS + Vite 5 (`dist/` build verified) |
| **Model Integration** | Active | `MockProvider`, `LocalProvider` (Ollama `qwen2.5-coder:7b`), `OpenAICompatibleProvider` |
| **eBPF Layer** | Dry-run / Mock | BPF C compilation (`clang -target bpf`) works; real attach falls back to labelled `MOCK` mode when `bpftool` is missing |
| **Verification Suite** | 100% Pass | Z3 property check, ASan exploit elimination, 64-variant adversarial suite, mandatory regression suite, deterministic judge |

---

## 2. Dependencies & Tool Availability

| Tool | Status | Note |
| :--- | :--- | :--- |
| `clang` | YES | `/usr/bin/clang` (v21.1.8) |
| `llc` | YES | `/usr/bin/llc` |
| `z3` | YES | `z3-solver` Python package |
| `node` / `npm` | YES | Node v22.22.1 / npm 9.2.0 |
| `ollama` | YES | Host service active (`qwen2.5-coder:7b`) |
| `bpftool` | NO | Fallback to labelled `MOCK` mode |
| `afl-fuzz` | NO | Fallback to deterministic fuzz corpus |
| `patch` | YES | Linux unified diff `patch` tool |

---

## 3. Known Baseline Limitations & Planned Upgrades

1. **Target Coupling:** Hardcoded path assumptions (`targets/demo_app/demo_vuln.c`) -> **Upgrading to YAML/JSON target manifest (`astra.yaml`).**
2. **Patch Application:** Regex-based replacement -> **Upgrading to standard unified diff patcher with fallback cascade.**
3. **Formal Verification:** Single property function -> **Upgrading to extensible formal property framework (`BufferBounds`, `IntegerRange`, `NullSafety`, `AllocationSize`).**
4. **eBPF Runtime Layer:** Simulated attach -> **Upgrading to real eBPF uprobe/usdt events transport with ring-buffer user-space receiver & policy engine.**
5. **Dashboard Interaction:** Static exported JSON -> **Upgrading to live Python SSE/HTTP server API streaming real-time pipeline events to UI.**
6. **Patch Quality Scoring:** Binary pass/fail -> **Adding multi-metric Patch Quality Scoring engine.**
7. **Benchmarks & Evidence:** Manual data export -> **Adding automated benchmarking (`reports/benchmark.json`, `docs/BENCHMARK.md`) and proof-carrying evidence bundles.**

---

## 4. Phase Execution Progress

- [x] Phase 1: Baseline & Safety Verification
- [ ] Phase 2: Generic Target System (`astra.yaml`)
- [ ] Phase 3: Robust Patch Application (Unified diff + AST/source transform fallback)
- [ ] Phase 4: Reasoning Engine Upgrade (Local Ollama qwen2.5-coder:7b tuning & schema enforcement)
- [ ] Phase 5: Better SAST (Tree-sitter/AST hint adapter + Semgrep detector fallback)
- [ ] Phase 6: Fuzzing (AFL++ detection & deterministic fallback reporting)
- [ ] Phase 7: Root-Cause Localization (Multi-file stack trace parser)
- [ ] Phase 8: Formal / Symbolic Verification Framework
- [ ] Phase 9: Adversarial Patch Validation Upgrade
- [ ] Phase 10: Patch Quality Scoring System
- [ ] Phase 11: Real eBPF Runtime Layer & User-Space Event Receiver
- [ ] Phase 12: eBPF Demonstration
- [ ] Phase 13: Runtime Policy Engine (ALLOW, OBSERVE, ALERT, BLOCK)
- [ ] Phase 14: Live Dashboard (Python SSE/HTTP API Server)
- [ ] Phase 15: Dashboard UI Enhancements
- [ ] Phase 16: Resource Benchmarking
- [ ] Phase 17: One-Command Demo Script (`bash scripts/demo.sh`)
- [ ] Phase 18: Model Modes (MOCK, LOCAL, REMOTE)
- [ ] Phase 19: Test Expansion Suite
- [ ] Phase 20: Security & Fail-Safe Controls
- [ ] Phase 21: Comprehensive Documentation & `FINAL_STATUS.md`
- [ ] Phase 22: Proof-Carrying Competition Evidence Bundle
- [ ] Phase 23: Judge-Facing Language Alignment
- [ ] Phase 24: Competition Demonstration Mode
- [ ] Phase 25: Git Checkpoints
- [ ] Phase 26: Final Verification & Acceptance
