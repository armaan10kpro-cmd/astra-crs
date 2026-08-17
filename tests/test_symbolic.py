import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verification.symbolic import verify_buffer_property


def test_symbolic_property_passes():
    result = verify_buffer_property()
    assert result["status"] == "PASS"
    assert "property" in result
    assert "engine" in result
