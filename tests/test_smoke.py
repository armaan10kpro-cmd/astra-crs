from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "targets/demo_app/demo_vuln"


def test_normal_case():
    p = subprocess.run([str(BIN), "PING"], capture_output=True, text=True)
    assert p.returncode == ord("P")


def test_large_input_triggers_sanitizer():
    from discovery.sanitizer_runner import run_payload

    binary = str(ROOT / "targets" / "demo_app" / "demo_vuln")
    payload = "A" * 32

    result = run_payload(
        binary,
        payload,
        timeout=2.0,
    )

    assert result["sanitizer_triggered"], (
        "Expected AddressSanitizer/UBSan to trigger. "
        f"stderr={result['stderr_excerpt']}"
    )

