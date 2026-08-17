#!/usr/bin/env python3
"""Generate markdown report from latest run.json (legacy helper)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
run_json = ROOT / "reports/run.json"
if run_json.exists():
    data = json.loads(run_json.read_text())
    fid = data.get("finding_id", "")
    proof = ROOT / "reports" / fid / "proof_of_fix.md"
    if proof.exists():
        print(proof)
    else:
        print(ROOT / "reports/run.md")
else:
    print("No run.json found")
