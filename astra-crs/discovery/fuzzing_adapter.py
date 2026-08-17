"""Fuzzing adapter with AFL++ coverage-guided fuzzing when available, DETERMINISTIC FALLBACK FUZZING otherwise."""

from __future__ import annotations

import random
import shutil
import subprocess
import tempfile
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
    """Run coverage-guided AFL++ session; capture crashing inputs without fabricating results."""
    if not afl_available():
        return {"engine": "DETERMINISTIC FALLBACK FUZZING", "status": "unavailable", "crashes": []}

    input_dir = workdir / "in"
    output_dir = workdir / "out"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "seed.txt").write_text("OK\nSTATUS\n", encoding="utf-8")

    cmd = [
        "afl-fuzz",
        "-i",
        str(input_dir),
        "-o",
        str(output_dir),
        "-m",
        "none",
        "-V",
        str(max_seconds),
        "--",
        binary,
        "@@",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=max_seconds + 2)
        crashed = list((output_dir / "default" / "crashes").glob("*")) if (output_dir / "default" / "crashes").exists() else []
        crashes_list = [p.name for p in crashed if p.name != "README.txt"]
        
        crash_payload = None
        if crashes_list:
            first_crash = (output_dir / "default" / "crashes" / crashes_list[0])
            try:
                crash_payload = first_crash.read_text(errors="ignore").strip()
            except Exception:
                pass

        return {
            "engine": "AFL++ Coverage-Guided Fuzzer",
            "status": "crash_found" if crashes_list else "completed",
            "returncode": proc.returncode,
            "crashes_found": len(crashes_list),
            "crashes": crashes_list[:5],
            "crash_payload": crash_payload,
        }
    except subprocess.TimeoutExpired:
        crashed = list((output_dir / "default" / "crashes").glob("*")) if (output_dir / "default" / "crashes").exists() else []
        crashes_list = [p.name for p in crashed if p.name != "README.txt"]
        return {
            "engine": "AFL++ Coverage-Guided Fuzzer",
            "status": "timeout",
            "crashes_found": len(crashes_list),
            "crashes": crashes_list[:5],
        }
    except Exception as exc:
        return {"engine": "AFL++ Coverage-Guided Fuzzer", "status": "error", "error": str(exc), "crashes": []}


def fuzz_binary(binary: str, *, seed: int = 42) -> dict:
    """Run fuzzing session using AFL++ if available, otherwise DETERMINISTIC FALLBACK FUZZING."""
    if afl_available():
        with tempfile.TemporaryDirectory(prefix="astra-afl-") as tmp:
            afl_res = run_afl(binary, Path(tmp), max_seconds=3)
            if afl_res.get("crashes_found", 0) > 0 and afl_res.get("crash_payload"):
                payload = afl_res["crash_payload"]
                r = run_payload(binary, payload)
                return {
                    "engine": "AFL++ Coverage-Guided Fuzzer",
                    "status": "crash_found",
                    "total_inputs": afl_res.get("crashes_found"),
                    "crash": r,
                    "all_results_count": afl_res.get("crashes_found"),
                }

    # Explicit visible deterministic fallback report
    engine = "DETERMINISTIC FALLBACK FUZZING"

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
