"""Adversarial patch validator — attempt to break the repair."""

from __future__ import annotations

import random

from discovery.sanitizer_runner import run_payload


def generate_attacks(reproducer: str, *, seed: int = 2026, max_cases: int = 64) -> list[str]:
    rng = random.Random(seed)
    attacks: list[str] = []

    # Original trigger and mutations
    attacks.append(reproducer)
    if reproducer:
        attacks.append(reproducer + "X")
        attacks.append(reproducer[:-1] if len(reproducer) > 1 else reproducer)
        attacks.append(reproducer * 2)

    # Boundary around buffer size 32
    for n in [30, 31, 32, 33, 34, 48, 63, 64, 127, 255]:
        attacks.append("A" * n)
        attacks.append("B" * n)

    # Random nearby valid/invalid (no embedded nulls — argv cannot carry them)
    for _ in range(20):
        size = rng.randint(28, 80)
        attacks.append("".join(rng.choice("ABC123_-") for _ in range(size)))

    # Dedupe preserving order
    seen: set[str] = set()
    unique = []
    for a in attacks:
        if a not in seen:
            seen.add(a)
            unique.append(a)
    return unique[:max_cases]


def run_adversarial(binary: str, reproducer: str, *, max_cases: int = 64) -> dict:
    attacks = generate_attacks(reproducer, max_cases=max_cases)
    executed = []
    sanitizer_failures = 0
    crashes = 0
    safe = 0
    regression_failures = 0

    for payload in attacks:
        r = run_payload(binary, payload)
        sanitizer = r["sanitizer_triggered"]
        rc = r["returncode"]
        if sanitizer:
            sanitizer_failures += 1
        if rc < 0 and rc != -1 and rc != 255:
            crashes += 1
        if not sanitizer:
            safe += 1
        executed.append(
            {
                "payload_length": len(payload),
                "payload_preview": payload[:24],
                "returncode": rc,
                "sanitizer_triggered": sanitizer,
            }
        )

    passed = sanitizer_failures == 0 and crashes == 0
    return {
        "status": "PASS" if passed else "FAIL",
        "pass": passed,
        "attacks_generated": len(attacks),
        "attacks_executed": len(executed),
        "sanitizer_failures": sanitizer_failures,
        "crashes": crashes,
        "successful_safe_executions": safe,
        "regression_failures": regression_failures,
        "samples": executed[:10],
        "all_results": executed,
    }


def verify_original_exploit_eliminated(binary: str, reproducer: str) -> dict:
    r = run_payload(binary, reproducer)
    eliminated = not r["sanitizer_triggered"]
    return {
        "reproducer": reproducer,
        "sanitizer_triggered": r["sanitizer_triggered"],
        "returncode": r["returncode"],
        "exploit_eliminated": eliminated,
        "pass": eliminated,
    }
