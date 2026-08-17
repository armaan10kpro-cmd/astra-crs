import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verification.proof_report import write_proof_report


def test_proof_report_generation(tmp_path):
    finding = {
        "finding_id": "AST-test123",
        "severity": "high",
        "reproducer": "A" * 64,
        "source_file": "targets/demo_app/demo_vuln.c",
        "function": "parse_message",
        "line": 14,
        "sanitizer": "AddressSanitizer",
        "stack_trace": "",
        "evidence": [],
    }
    out = write_proof_report(
        tmp_path,
        finding,
        discovery={"status": "confirmed"},
        proposal={"root_cause": "test", "proposed_change": "fix"},
        patch_result={"patch_diff": "diff", "compiler_log": ""},
        symbolic={"status": "PASS", "property": "p", "engine": "test"},
        exploit_check={"pass": True},
        adversarial={"status": "PASS", "attacks_executed": 10},
        regression={"status": "PASS", "passed": 5, "mandatory_tests": 5},
        verdict={"verdict": "FIX_VERIFIED", "checks": {}},
        attempts=[],
        runtime={"backend": "mock", "mode": "mock"},
        resources={"elapsed_seconds": 1.0},
    )
    assert (out / "proof_of_fix.md").exists()
    assert (out / "final_verdict.json").exists()
    latest = json.loads((tmp_path / "reports/latest.json").read_text())
    assert latest["verdict"] == "FIX_VERIFIED"
