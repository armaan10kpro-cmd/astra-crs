#!/usr/bin/env bash
# ASTRA-CRS one-click demo — full pipeline
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== ASTRA-CRS Demo ==="
echo "[1/6] Environment check"
python3 scripts/check_env.py || true

echo "[2/6] Python venv + deps"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

echo "[3/6] Clean + build baseline target"
make clean 2>/dev/null || true
make build

echo "[4/6] Legitimate behaviour (regression on vulnerable binary — valid inputs)"
make -C targets/demo_app test BIN="$ROOT/targets/demo_app/demo_vuln" || {
  echo "Note: regression on vulnerable binary tests valid-input paths only"
}

echo "[5/6] Full pipeline (discover → repair → verify → protect → report)"
python3 agent/orchestrator.py --mode mock --clean

echo "[6/6] Summary"
python3 scripts/demo.py --summary-only

if [[ "${ASTRA_LAUNCH_DASHBOARD:-0}" == "1" ]]; then
  echo "Launching dashboard..."
  (cd dashboard && npm install -q && npm run dev) &
fi

echo "=== Demo complete ==="
echo "Reports: $ROOT/reports/"
cat reports/run.md 2>/dev/null || true
