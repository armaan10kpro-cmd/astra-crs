#!/usr/bin/env python3
"""Demo helper — summary, benchmark, dashboard data export."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def summary() -> int:
    run = ROOT / "reports/run.json"
    if not run.exists():
        print("No run.json — run scripts/demo.sh first", file=sys.stderr)
        return 1
    data = json.loads(run.read_text())
    print(f"Final status: {data.get('final_status')}")
    print(f"Finding: {data.get('finding_id', '-')}")
    print(f"Report: {data.get('report_dir', '-')}")
    if data.get("resources"):
        print(f"Elapsed: {data['resources'].get('elapsed_seconds')}s")
    return 0


def benchmark() -> int:
    started = time.time()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "agent/orchestrator.py"), "--mode", "mock", "--clean"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    elapsed = time.time() - started
    print(json.dumps({"exit_code": proc.returncode, "wall_seconds": round(elapsed, 3)}, indent=2))
    return proc.returncode


def export_dashboard_data() -> Path:
    run = ROOT / "reports/run.json"
    out = ROOT / "dashboard/public/run.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if run.exists():
        out.write_text(run.read_text())
        fid = json.loads(run.read_text()).get("finding_id")
        if fid:
            proof_dir = ROOT / "reports" / fid
            for name in (
                "finding.json",
                "adversarial_tests.json",
                "regression_results.json",
                "symbolic_results.json",
                "final_verdict.json",
                "proof_of_fix.md",
                "patch.diff",
            ):
                src = proof_dir / name
                if src.exists():
                    (out.parent / name).write_text(src.read_text())
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary-only", action="store_true")
    ap.add_argument("--benchmark", action="store_true")
    ap.add_argument("--export-dashboard", action="store_true")
    args = ap.parse_args()

    if args.benchmark:
        raise SystemExit(benchmark())
    if args.export_dashboard:
        p = export_dashboard_data()
        print(p)
        raise SystemExit(0)
    raise SystemExit(summary())


if __name__ == "__main__":
    main()
