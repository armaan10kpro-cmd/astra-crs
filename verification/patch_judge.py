"""Deterministic patch judge — LLM is never final authority."""

from __future__ import annotations

from typing import Any


def judge(
    *,
    compile_ok: bool,
    patch_valid: bool,
    symbolic: dict,
    exploit_check: dict,
    adversarial: dict,
    regression: dict,
) -> dict[str, Any]:
    checks = {
        "compilation_successful": compile_ok,
        "patch_syntactically_valid": patch_valid,
        "security_property_satisfied": symbolic.get("status") == "PASS",
        "original_exploit_eliminated": exploit_check.get("pass", False),
        "adversarial_tests_passed": adversarial.get("pass", False),
        "regression_suite_passed": regression.get("pass", False),
    }
    all_pass = all(checks.values())
    verdict = "FIX_VERIFIED" if all_pass else "REJECTED"
    return {
        "verdict": verdict,
        "checks": checks,
        "all_pass": all_pass,
    }
