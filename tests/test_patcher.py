from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verification.patcher import generate_candidate, unified_diff


def test_generate_candidate():
    src = (ROOT / "targets/demo_app/demo_vuln.c").read_text()
    patched = generate_candidate(src, "Destination buffer is 32 bytes")
    assert "if (n >= sizeof(buf))" in patched
    assert "Intentional training flaw" not in patched or "memcpy" in patched
    diff = unified_diff(src, patched)
    assert "---" in diff and "+++" in diff


def test_reject_unknown_root_cause():
    import pytest

    with pytest.raises(ValueError):
        generate_candidate("int x;", "unknown bug")
