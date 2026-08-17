"""Execute target under AddressSanitizer / UBSan and capture crashes."""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile


SANITIZER_MARKERS = (
    "AddressSanitizer",
    "UndefinedBehaviorSanitizer",
    "runtime error:",
)


def _decode(data: bytes | str | None) -> str:
    if not data:
        return ""
    if isinstance(data, bytes):
        return data.decode(errors="replace")
    return data


def _result(
    payload: str,
    returncode: int,
    stdout: str,
    stderr: str,
) -> dict:
    sanitizer_triggered = any(
        marker in stderr for marker in SANITIZER_MARKERS
    )

    return {
        "payload": payload,
        "payload_length": len(payload),
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
        "sanitizer_triggered": sanitizer_triggered,
        "stderr_excerpt": stderr[:3000],
    }


def run_payload(
    binary: str,
    payload: str,
    *,
    timeout: float = 2.0,
) -> dict:

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

    with tempfile.TemporaryFile() as stdout_file, \
         tempfile.TemporaryFile() as stderr_file:

        proc = subprocess.Popen(
            [binary, payload],
            stdout=stdout_file,
            stderr=stderr_file,
            stdin=subprocess.DEVNULL,
            env=env,
            start_new_session=True,
        )

        timed_out = False

        try:
            proc.wait(timeout=timeout)

        except subprocess.TimeoutExpired:
            timed_out = True

            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

            try:
                proc.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                try:
                    os.kill(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()

        stdout_file.flush()
        stderr_file.flush()

        stdout_file.seek(0)
        stderr_file.seek(0)

        stdout = _decode(stdout_file.read())
        stderr = _decode(stderr_file.read())

        if timed_out:
            stderr += (
                f"\nASTRA: execution timed out after {timeout:.1f}s; "
                "process group terminated.\n"
            )

            return _result(
                payload,
                124,
                stdout,
                stderr,
            )

        return _result(
            payload,
            proc.returncode if proc.returncode is not None else 1,
            stdout,
            stderr,
        )
