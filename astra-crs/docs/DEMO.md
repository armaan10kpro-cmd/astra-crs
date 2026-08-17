# Demo Guide

## One-command demo

```bash
make demo
```

Or directly:

```bash
bash scripts/demo.sh
```

## What the demo does

1. Checks environment (`scripts/check_env.py`)
2. Creates Python venv and installs dependencies
3. Builds baseline vulnerable target with ASan/UBSan
4. Runs legitimate-input regression on valid paths
5. Executes full pipeline via `agent/orchestrator.py --clean`
6. Prints summary and report locations

## Expected outcome

- `reports/run.json` with `"final_status": "FIX_VERIFIED"`
- Proof-carrying report at `reports/<finding_id>/`
- Files: `finding.json`, `patch.diff`, `proof_of_fix.md`, `final_verdict.json`, etc.

## Dashboard

```bash
make demo
make dashboard-export
cd dashboard && npm install && npm run dev
```

Open http://localhost:5173

Set `ASTRA_LAUNCH_DASHBOARD=1 make demo` to auto-launch after pipeline.

## Benchmark mode

```bash
make benchmark
```

## Model providers

```bash
ASTRA_MODEL_PROVIDER=mock make demo          # default, offline
ASTRA_MODEL_PROVIDER=local make demo         # Ollama/local endpoint
ASTRA_MODEL_PROVIDER=openai OPENAI_API_KEY=... make demo
```

## eBPF modes

```bash
python3 agent/orchestrator.py --mode mock      # DEMO / MOCK MODE (default)
python3 agent/orchestrator.py --mode dry-run   # BPF compile only
python3 agent/orchestrator.py --mode ebpf      # real observer when toolchain present
```

## Competition walkthrough (5 min)

1. Show vulnerable source: `targets/demo_app/demo_vuln.c`
2. Trigger bug: `./targets/demo_app/demo_vuln $(python3 -c "print('A'*64)")`
3. Run `make demo` — narrate pipeline stages on dashboard
4. Open `reports/<id>/proof_of_fix.md`
5. Show runtime shield MOCK events (or real eBPF if available)
6. Emphasize: verdict from deterministic judge, not LLM
