# ASTRA-CRS Architecture

**Autonomous Cyber-Reasoning & Verified Repair System**

## Lifecycle

```
DISCOVER → LOCALIZE → REASON → REPAIR → VERIFY → ADVERSARIAL TEST → PROTECT → REPORT
```

## Components

| Module | Path | Role |
|--------|------|------|
| Discovery | `discovery/` | SAST hints, sanitizer fuzzing, crash collection/minimization, localization |
| Reasoning | `reasoning/` | Scoped LLM context, structured patch proposals (Mock/Local/API) |
| Patch | `verification/patcher.py` | Isolated workspace, apply/compile/revert |
| Symbolic | `verification/symbolic.py` | Z3 or labelled arithmetic fallback |
| Adversarial | `verification/adversarial.py` | Mutation/boundary attacks against patched binary |
| Regression | `verification/regression.py` | Mandatory legitimate-behaviour tests |
| Judge | `verification/patch_judge.py` | Deterministic FIX_VERIFIED / REJECTED |
| Proof | `verification/proof_report.py` | Proof-carrying patch under `reports/<finding_id>/` |
| Runtime | `runtime/ebpf/` | eBPF observation + MOCK mode |
| Orchestrator | `agent/orchestrator.py` | Bounded repair loop (N=3) |
| Dashboard | `dashboard/` | React mission control UI |
| Target | `targets/demo_app/` | Synthetic vulnerable C application |

## Data flow

1. **Discovery** builds target, runs deterministic fuzz fallback, collects sanitizer crash, minimizes reproducer, emits structured `finding`.
2. **Reasoning** sends only function slice + evidence to model provider; receives JSON patch proposal.
3. **Patch workspace** applies candidate in temp dir; never overwrites baseline until verified.
4. **Verification** runs symbolic property, exploit re-test, adversarial suite, regression suite.
5. **Judge** requires ALL checks pass — LLM claim is ignored.
6. **Report** writes full evidence bundle.
7. **Runtime shield** attaches mock or real eBPF observer; emits policy events (no binary rewriting).

## Principles

- LLM is never final authority on patch correctness.
- Fallback modes are explicitly labelled (MOCK, SYMBOLIC_ENGINE_UNAVAILABLE).
- eBPF used only for supported observation/interception — not universal memory patching.
