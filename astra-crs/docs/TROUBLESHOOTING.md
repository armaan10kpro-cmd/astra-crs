# Troubleshooting

## pytest not found

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make test
```

## clang / sanitizers missing

Install build-essential and clang:

```bash
sudo apt install clang build-essential
```

## Demo returns NO_FINDING

Ensure target builds with ASan:

```bash
make build
./targets/demo_app/demo_vuln $(python3 -c "print('A'*64)")  # should ASan-error
```

## FIX_VERIFIED fails / NO_VERIFIED_FIX

Check `reports/run.json` → `attempts` array for failure reasons.

Common causes:

- Compilation error in candidate patch
- Adversarial sanitizer failure on patched binary
- Regression failure on valid inputs

## Z3 not used

Install in venv: `pip install z3-solver`. Fallback checker still runs but reports `SYMBOLIC_ENGINE_UNAVAILABLE`.

## eBPF always MOCK

Expected without bpftool/libbpf. Run `python3 scripts/check_env.py`.

Use `--mode dry-run` to test BPF object compilation only.

## Dashboard shows NO DATA

```bash
make demo
make dashboard-export
cd dashboard && npm install && npm run dev
```

## WSL / path issues

Run all commands inside WSL Ubuntu:

```bash
cd ~/projects/astra-crs
make demo
```

## Git identity for commits

If commits fail due to missing user.name/email, configure locally (not done automatically by agent).
