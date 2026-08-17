"""Fuzzing adapter with AFL++ when available, deterministic fallback otherwise."""

from __future__ import annotations

import random
import shutil
import subprocess
from pathlib import Path

from discovery.sanitizer_runner import run_payload


def afl_available() -> bool:
    return shutil.which("afl-fuzz") is not None


def deterministic_candidates(seed: int = 42) -> list[str]:
    """Bounded deterministic input corpus for offline demo."""
    seeds = ["OK", "PING", "STATUS", "HELLO", "A" * 16, "A" * 31, "A" * 32, "A" * 63]
    out = list(seeds)
    rng = random.Random(seed)
    for size in range(32, 65):
        for _ in range(3):
            out.append("".join(rng.choice("ABC123_-") for _ in range(size)))
    return out


def run_afl(binary: str, workdir: Path, *, max_seconds: int = 5) -> dict:
    """Attempt short AFL++ session; never fabricate results."""
    if not afl_available():
        return {"engine": "afl++", "status": "unavailable", "crashes": []}
    input_dir = workdir / "in"
    output_dir = workdir / "out"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "seed.txt").write_text("OK")
    cmd = [
        "afl-fuzz",
        "-i",
        str(input_dir),
        "-o",
        str(output_dir),
        "-m",
        "none",
        "--",
        binary,
        "@@",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=max_seconds)
        crashed = list((output_dir / "default" / "crashes").glob("*")) if (output_dir / "default" / "crashes").exists() else []
        return {
            "engine": "afl++",
            "status": "completed",
            "returncode": proc.returncode,
            "crashes_found": len(crashed),
            "crashes": [p.name for p in crashed[:5]],
        }
    except subprocess.TimeoutExpired:
        crashed = list((output_dir / "default" / "crashes").glob("*")) if (output_dir / "default" / "crashes").exists() else []
        return {
            "engine": "afl++",
            "status": "timeout",
            "crashes_found": len(crashed),
            "crashes": [p.name for p in crashed[:5]],
        }
    except Exception as exc:
        return {"engine": "afl++", "status": "error", "error": str(exc), "crashes": []}


def fuzz_binary(binary: str, *, seed: int = 42) -> dict:
    """Run deterministic fallback fuzz; optionally note AFL availability."""
    engine = "deterministic-fallback"
    if afl_available():
        engine = "deterministic-fallback (afl++ present but bounded demo uses fallback)"

    results = []
    for payload in deterministic_candidates(seed):
        r = run_payload(binary, payload)
        results.append(r)
        if r["sanitizer_triggered"]:
            return {
                "engine": engine,
                "status": "crash_found",
                "total_inputs": len(results),
                "crash": r,
                "all_results_count": len(results),
            }

    return {
        "engine": engine,
        "status": "no_crash",
        "total_inputs": len(results),
        "all_results_count": len(results),
    }
