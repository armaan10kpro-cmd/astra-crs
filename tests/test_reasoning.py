import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reasoning.engine import propose_patch
from reasoning.model_provider import MockProvider, extract_json


def test_mock_provider_proposal():
    finding = {
        "function": "parse_message",
        "source_slice": "memcpy(buf, msg, n+1);",
        "sanitizer": "AddressSanitizer",
        "stack_trace": "parse_message demo_vuln.c:14",
        "reproducer": "A" * 64,
    }
    result = propose_patch(finding, provider=MockProvider())
    assert result["status"] == "candidate"
    assert "root_cause" in result
    assert "unified_diff" in result


def test_extract_json_rejects_incomplete():
    import pytest

    with pytest.raises(ValueError):
        extract_json('{"root_cause": "only one field"}')
