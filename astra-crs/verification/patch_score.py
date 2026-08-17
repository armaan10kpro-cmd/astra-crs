"""Candidate Patch Quality Scoring Engine evaluating correctness, regression, properties, adversarial resilience, and diff minimality."""

from __future__ import annotations

from typing import Any


def calculate_patch_score(
    *,
    compile_ok: bool,
    exploit_eliminated: bool,
    symbolic_passed: bool,
    adversarial_passed: bool,
    regression_passed: bool,
    diff_text: str = "",
    attacks_executed: int = 0,
    attacks_passed: int = 0,
) -> dict[str, Any]:
    """Calculate Patch Quality Score (0 to 100)."""
    score = 0.0
    breakdown = {}

    # 1. Compilation & Syntax (15 pts)
    comp_score = 15.0 if compile_ok else 0.0
    score += comp_score
    breakdown["compilation"] = comp_score

    # 2. Exploit Elimination (25 pts)
    exploit_score = 25.0 if exploit_eliminated else 0.0
    score += exploit_score
    breakdown["exploit_elimination"] = exploit_score

    # 3. Formal Property Verification (20 pts)
    prop_score = 20.0 if symbolic_passed else 0.0
    score += prop_score
    breakdown["symbolic_property"] = prop_score

    # 4. Mandatory Regression Suite (20 pts)
    reg_score = 20.0 if regression_passed else 0.0
    score += reg_score
    breakdown["regression_suite"] = reg_score

    # 5. Adversarial Resilience (10 pts)
    if attacks_executed > 0:
        adv_ratio = attacks_passed / attacks_executed
        adv_score = round(10.0 * adv_ratio, 2) if adversarial_passed else 0.0
    else:
        adv_score = 10.0 if adversarial_passed else 0.0
    score += adv_score
    breakdown["adversarial_resilience"] = adv_score

    # 6. Diff Minimality & Elegance (10 pts)
    # Prefer clean, concise patches (under 20 lines changed)
    lines_changed = len([l for l in diff_text.splitlines() if l.startswith("+") or l.startswith("-")]) if diff_text else 5
    if lines_changed <= 10:
        min_score = 10.0
    elif lines_changed <= 25:
        min_score = 7.5
    elif lines_changed <= 50:
        min_score = 5.0
    else:
        min_score = 2.5
    score += min_score
    breakdown["diff_minimality"] = min_score

    final_score = round(min(100.0, score), 1)
    grade = "A+" if final_score >= 95 else ("A" if final_score >= 85 else ("B" if final_score >= 70 else "F"))

    return {
        "score": final_score,
        "grade": grade,
        "breakdown": breakdown,
        "lines_changed": lines_changed,
        "verified": final_score >= 90.0 and compile_ok and exploit_eliminated and regression_passed and adversarial_passed,
    }
