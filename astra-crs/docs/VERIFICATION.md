# Verification Philosophy

## Core rule

**The LLM never decides whether a patch is correct.**

Only deterministic stages can produce `FIX_VERIFIED`:

1. Compilation succeeds in isolated workspace
2. Explicit security property check passes (Z3 or labelled fallback)
3. Original reproducer no longer triggers sanitizer
4. Adversarial mutation suite passes (bounded deterministic cases)
5. Mandatory regression tests pass
6. Patch judge aggregates all checks → `FIX_VERIFIED` or `REJECTED`

## Symbolic verification

Property for demo vulnerability (buffer size B=32):

- If length `n` is accepted (`n < B`), then copy length `n+1 ≤ B`
- If `n ≥ B`, input is rejected before copy

When Z3 unavailable:

- Status may still PASS via arithmetic fallback
- Report includes `symbolic_engine_unavailable: true` and `SYMBOLIC_ENGINE_UNAVAILABLE` note
- We do **not** claim universal mathematical proof of software security

## Adversarial validation

After patch passes original reproducer:

- Mutations of triggering input
- Boundary cases (30–255 bytes)
- Random nearby inputs
- All executed under sanitizers on **patched** binary

Metrics recorded: attacks generated/executed, sanitizer failures, crashes, safe executions.

## Auto-fix loop

Maximum **N = 3** attempts. Failed attempts stored in `attempts.json` — never hidden.

## Proof-carrying patch

Every accepted repair creates `reports/<finding_id>/` with full evidence chain.

## Installing Z3

```bash
pip install z3-solver
```

Verify: `python3 -c "import z3; print(z3.get_version_string())"`
