from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from discovery.localizer import parse_stack_frame, extract_source_slice


def test_parse_stack_frame():
    stderr = "#1 0x558316e9d297 in parse_message targets/demo_app/demo_vuln.c:14"
    frame = parse_stack_frame(stderr)
    assert frame is not None
    assert frame["function"] == "parse_message"
    assert frame["line"] == 14


def test_extract_source_slice():
    src = ROOT / "targets/demo_app/demo_vuln.c"
    text = extract_source_slice(src, 14, context=2)
    assert "memcpy" in text
    assert ">>>" in text
