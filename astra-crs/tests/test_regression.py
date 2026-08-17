import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verification.patcher import generate_candidate, PatchWorkspace
from verification.regression import verify


def _ensure_built():
    bin_path = ROOT / "targets/demo_app/demo_vuln"
    if not bin_path.exists():
        subprocess.run(
            ["clang", "-O1", "-g", "-fsanitize=address,undefined", str(ROOT / "targets/demo_app/demo_vuln.c"), "-o", str(bin_path)],
            check=True,
        )
    return bin_path


def test_regression_on_patched_binary():
    src_path = ROOT / "targets/demo_app/demo_vuln.c"
    src = src_path.read_text()
    patched = generate_candidate(src, "32 bytes")
    ws = PatchWorkspace(src_path)
    try:
        ws.apply(patched)
        built, _ = ws.compile()
        assert built
        result = verify(str(ws.binary))
        assert result["pass"] is True
    finally:
        ws.cleanup()
