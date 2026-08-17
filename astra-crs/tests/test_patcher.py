from pathlib import Path
import pytest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verification.patcher import generate_candidate, unified_diff, apply_proposal_to_source, apply_unified_diff


def test_generate_candidate():
    src = (ROOT / "targets/demo_app/demo_vuln.c").read_text()
    patched = generate_candidate(src, "Destination buffer is 32 bytes")
    assert "if (n >= sizeof(buf))" in patched
    assert "Intentional training flaw" not in patched or "memcpy" in patched
    diff = unified_diff(src, patched)
    assert "---" in diff and "+++" in diff


def test_reject_unknown_root_cause():
    with pytest.raises(ValueError):
        generate_candidate("int x;", "unknown bug")


def test_apply_valid_proposal_to_source():
    src = (ROOT / "targets/demo_app/demo_vuln.c").read_text()
    proposal = {
        "root_cause": "Destination buffer is 32 bytes",
        "unified_diff": (
            "--- a/demo_vuln.c\n"
            "+++ b/demo_vuln.c\n"
            "@@ -11,6 +11,9 @@ int parse_message(const char *msg) {\n"
            "     char buf[32];\n"
            "     size_t n = strlen(msg);\n"
            "+    if (n >= sizeof(buf)) {\n"
            "+        return -1;\n"
            "+    }\n"
            "     memcpy(buf, msg, n + 1);\n"
        ),
    }
    patched = apply_proposal_to_source(src, proposal)
    assert "if (n >= sizeof(buf))" in patched


def test_apply_invalid_diff_fallback():
    src = (ROOT / "targets/demo_app/demo_vuln.c").read_text()
    proposal = {
        "root_cause": "Destination buffer is 32 bytes",
        "unified_diff": "invalid malformed diff content",
    }
    patched = apply_proposal_to_source(src, proposal)
    assert "if (n >= sizeof(buf))" in patched
