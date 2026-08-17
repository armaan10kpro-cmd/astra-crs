import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _ensure_binary():
    bin_path = ROOT / "targets/demo_app/demo_vuln"
    if not bin_path.exists():
        subprocess.run(
            [
                "clang",
                "-O1",
                "-g",
                "-fsanitize=address,undefined",
                str(ROOT / "targets/demo_app/demo_vuln.c"),
                "-o",
                str(bin_path),
            ],
            check=True,
        )
    return bin_path


def test_discovery_finds_vulnerability():
    from discovery.pipeline import run_discovery

    _ensure_binary()
    result = run_discovery(ROOT)
    assert result["status"] == "confirmed"
    finding = result["finding"]
    assert finding["finding_id"].startswith("AST-")
    assert finding["function"] == "parse_message"
    assert len(finding["reproducer"]) >= 32


def test_e2e_pipeline_fix_verified():
    from agent.orchestrator import run_pipeline

    _ensure_binary()
    result = run_pipeline(root=ROOT, mode="mock", provider_name="mock", clean=True)
    assert result["final_status"] == "FIX_VERIFIED"
    assert result.get("report_dir")
    report = ROOT / result["report_dir"] / "proof_of_fix.md"
    assert report.exists()
