import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verification.patch_judge import judge


def test_judge_fix_verified():
    v = judge(
        compile_ok=True,
        patch_valid=True,
        symbolic={"status": "PASS"},
        exploit_check={"pass": True},
        adversarial={"pass": True},
        regression={"pass": True},
    )
    assert v["verdict"] == "FIX_VERIFIED"


def test_judge_rejected_on_adversarial_fail():
    v = judge(
        compile_ok=True,
        patch_valid=True,
        symbolic={"status": "PASS"},
        exploit_check={"pass": True},
        adversarial={"pass": False},
        regression={"pass": True},
    )
    assert v["verdict"] == "REJECTED"
