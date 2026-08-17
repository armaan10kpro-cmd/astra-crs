import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verification.adversarial import generate_attacks, run_adversarial
from verification.patcher import generate_candidate, PatchWorkspace


def test_generate_attacks_bounded():
    attacks = generate_attacks("A" * 64, max_cases=32)
    assert len(attacks) <= 32
    assert "A" * 64 in attacks


def test_adversarial_on_patched_binary():
    src_path = ROOT / "targets/demo_app/demo_vuln.c"
    patched = generate_candidate(src_path.read_text(), "32 bytes")
    ws = PatchWorkspace(src_path)
    try:
        ws.apply(patched)
        assert ws.compile()[0]
        result = run_adversarial(str(ws.binary), "A" * 64, max_cases=32)
        assert result["pass"] is True
        assert result["sanitizer_failures"] == 0
    finally:
        ws.cleanup()
