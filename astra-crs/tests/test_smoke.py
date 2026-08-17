from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "targets/demo_app/demo_vuln"


def test_normal_case():
    p = subprocess.run([str(BIN), "PING"], capture_output=True, text=True)
    assert p.returncode == ord("P")


def test_large_input_triggers_sanitizer():
    p = subprocess.run([str(BIN), "A" * 64], capture_output=True, text=True)
    assert "AddressSanitizer" in p.stderr
