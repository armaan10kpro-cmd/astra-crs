"""Minimize crashing input while preserving sanitizer trigger."""

from __future__ import annotations

from discovery.sanitizer_runner import run_payload


def minimizes(payload: str, binary: str) -> str:
    """Greedy byte/char deletion minimizer (deterministic)."""
    if not payload:
        return payload

    current = payload
    changed = True
    while changed and len(current) > 1:
        changed = False
        for i in range(len(current)):
            candidate = current[:i] + current[i + 1 :]
            r = run_payload(binary, candidate)
            if r["sanitizer_triggered"]:
                current = candidate
                changed = True
                break

    # Try shrinking repeated chars at boundaries
    if len(set(current)) == 1 and len(current) > 32:
        for n in range(len(current) - 1, 31, -1):
            trial = current[0] * n
            r = run_payload(binary, trial)
            if r["sanitizer_triggered"]:
                current = trial
                break
    return current


def minimize_crash(crash: dict, binary: str) -> dict:
    original = crash.get("payload", "")
    minimized = minimizes(original, binary)
    out = dict(crash)
    out["original_payload_length"] = len(original)
    out["minimized_payload"] = minimized
    out["minimized_payload_length"] = len(minimized)
    out["reproducer"] = minimized
    return out
