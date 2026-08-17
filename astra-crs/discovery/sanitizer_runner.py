"""Execute target under AddressSanitizer / UBSan and capture crashes."""

from __future__ import annotations

import os
import subprocess


SANITIZER_MARKERS = ("AddressSanitizer", "UndefinedBehaviorSanitizer", "SUMMARY:")


def run_payload(binary: str, payload: str, *, timeout: float = 2.0) -> dict:
    if "\x00" in payload:
        return {
            "payload": payload,
            "payload_length": len(payload),
            "returncode": -1,
            "stdout": "",
            "stderr": "skipped: embedded null byte in argv payload",
            "sanitizer_triggered": False,
            "stderr_excerpt": "skipped: embedded null byte",
        }
    env = os.environ.copy()
    env.setdefault("ASAN_OPTIONS", "detect_leaks=0")
    proc = subprocess.run(
        [binary, payload],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    stderr = proc.stderr or ""
    return {
        "payload": payload,
        "payload_length": len(payload),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": stderr,
        "sanitizer_triggered": any(m in stderr for m in SANITIZER_MARKERS[:2]),
        "stderr_excerpt": stderr[:3000],
    }
