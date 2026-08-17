"""Deterministic patch judge — LLM is never final authority."""

from __future__ import annotations

from typing import Any

from verification.patch_score import calculate_patch_score


def judge(
    *,
    compile_ok: bool,
    patch_valid: bool,
    symbolic: dict,
    exploit_check: dict,
    adversarial: dict,
    regression: dict,
    diff_text: str = "",
) -> dict[str, Any]:
    symbolic_ok = (symbolic.get("status") == "PASS") or (symbolic.get("result") == "PASS")
    exploit_ok = exploit_check.get("pass", False) or exploit_check.get("exploit_eliminated", False)
    adversarial_ok = adversarial.get("pass", False)
    regression_ok = regression.get("pass", False)

    checks = {
        "compilation_successful": compile_ok,
        "patch_syntactically_valid": patch_valid,
        "security_property_satisfied": symbolic_ok,
        "original_exploit_eliminated": exploit_ok,
        "adversarial_tests_passed": adversarial_ok,
        "regression_suite_passed": regression_ok,
    }
    all_pass = all(checks.values())
    verdict = "FIX_VERIFIED" if all_pass else "REJECTED"

    quality_score = calculate_patch_score(
        compile_ok=compile_ok,
        exploit_eliminated=exploit_ok,
        symbolic_passed=symbolic_ok,
        adversarial_passed=adversarial_ok,
        regression_passed=regression_ok,
        diff_text=diff_text,
        attacks_executed=adversarial.get("attacks_executed", 0),
        attacks_passed=adversarial.get("attacks_executed", 0) - adversarial.get("sanitizer_failures", 0),
    )

    return {
        "verdict": verdict,
        "checks": checks,
        "all_pass": all_pass,
        "score": quality_score["score"],
        "quality": quality_score,
    }
