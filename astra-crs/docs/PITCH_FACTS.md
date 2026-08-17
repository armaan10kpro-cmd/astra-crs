# ASTRA-CRS Pitch Facts

*Only demonstrably supported claims — no invented benchmarks.*

## Architecture facts

- Full pipeline: DISCOVER → LOCALIZE → REASON → REPAIR → VERIFY → ADVERSARIAL TEST → PROTECT → REPORT
- Deterministic patch judge; LLM output is never final authority
- Proof-carrying reports under `reports/<finding_id>/`
- Bounded repair loop: max 3 attempts
- Model providers: Mock (default), Local (Ollama-compatible), OpenAI-compatible

## Demo target

- Synthetic C app: stack buffer overflow via unchecked `memcpy`
- AddressSanitizer-detectable, reproducible locally
- No external network communication

## Test counts (from implementation)

- Unit tests: localizer, patcher, symbolic, regression, adversarial, patch_judge, proof_report, reasoning
- End-to-end test: full pipeline → FIX_VERIFIED
- Target regression script: 5 mandatory valid-input cases
- Adversarial suite: up to 64 bounded deterministic cases per run
- Discovery fuzz fallback: ~100+ deterministic inputs

## Supported components

| Component | Status |
|-----------|--------|
| clang + ASan/UBSan | Real (when installed) |
| Deterministic discovery | Real |
| MockProvider patch reasoning | Real |
| Isolated patch workspace | Real |
| Z3 symbolic check | Real when z3-solver installed; else labelled fallback |
| Adversarial validator | Real |
| eBPF BPF source | Real |
| eBPF runtime attach | Mock/dry-run default; full attach needs libbpf/bpftool |
| React dashboard | Real |

## eBPF limitations (explicit)

- Observation/telemetry via uprobes — not arbitrary binary rewriting
- MOCK mode labelled **DEMO / MOCK MODE**
- Permanent fix is always source patch + rebuild + verify

## Novelty claim (exact)

**Proof-carrying patch**: every accepted repair ships a deterministic evidence bundle (finding, diff, compiler log, symbolic result, adversarial metrics, regression results, judge verdict) that explains *why* the patch was accepted — independent of LLM self-assessment.

## Measured demo latency

Run `make benchmark` on your host to record wall-clock seconds. Initial dev environment measurement: *run benchmark locally — do not cite placeholder numbers.*

## Resource optimization

- MockProvider default (no GPU/API required)
- Bounded fuzz inputs and adversarial cases
- Scoped reasoning context (function slice only)
- Optional tracemalloc peak RSS in run report
