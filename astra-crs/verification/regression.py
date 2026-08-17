"""Mandatory regression suite for legitimate behaviour."""

from __future__ import annotations

import subprocess


NORMAL_CASES = [
    ("OK", ord("O")),
    ("PING", ord("P")),
    ("STATUS", ord("S")),
    ("HELLO", ord("H")),
    ("A" * 31, ord("A")),
]


def run(binary: str, payload: str) -> subprocess.CompletedProcess:
    return subprocess.run([binary, payload], capture_output=True, text=True, timeout=2)


def verify(binary: str) -> dict:
    results = []
    for payload, expected_rc in NORMAL_CASES:
        p = run(binary, payload)
        ok = p.returncode == expected_rc and "AddressSanitizer" not in (p.stderr or "")
        results.append(
            {
                "input": payload[:32] + ("..." if len(payload) > 32 else ""),
                "input_length": len(payload),
                "expected_returncode": expected_rc,
                "returncode": p.returncode,
                "sanitizer_error": "AddressSanitizer" in (p.stderr or ""),
                "pass": ok,
            }
        )

    all_pass = all(r["pass"] for r in results)
    return {
        "status": "PASS" if all_pass else "FAIL",
        "pass": all_pass,
        "mandatory_tests": len(results),
        "passed": sum(1 for r in results if r["pass"]),
        "results": results,
    }
