"""End-to-end discovery pipeline producing structured findings."""

from __future__ import annotations

import hashlib
import time
import uuid
from pathlib import Path

from discovery.crash_collector import collect_crash, save_crash
from discovery.crash_minimizer import minimize_crash
from discovery.fuzzing_adapter import fuzz_binary
from discovery.localizer import localize
from discovery.sast_adapter import analyze_source
from discovery.sanitizer_runner import run_payload
from discovery.target_builder import build_demo_app


def finding_id(payload: str, location: str) -> str:
    h = hashlib.sha256(f"{payload}:{location}".encode()).hexdigest()[:12]
    return f"AST-{h}"


def run_discovery(root: Path, *, binary: Path | None = None) -> dict:
    started = time.time()
    timeline = []

    if binary is None:
        binary_path, built, build_log = build_demo_app(root)
        timeline.append({"stage": "build", "ok": built, "log_tail": build_log[-500:]})
        if not built:
            return {
                "status": "build_failed",
                "timeline": timeline,
                "elapsed_seconds": round(time.time() - started, 3),
            }
    else:
        binary_path = binary

    source_path = root / "targets/demo_app/demo_vuln.c"
    sast_hints = analyze_source(source_path)
    timeline.append({"stage": "sast", "hints": len(sast_hints)})

    fuzz_result = fuzz_binary(str(binary_path))
    timeline.append({"stage": "fuzz", **{k: fuzz_result[k] for k in ("engine", "status", "total_inputs")}})

    if fuzz_result.get("status") != "crash_found":
        # Direct reproducer fallback
        direct = run_payload(str(binary_path), "A" * 64)
        if not direct["sanitizer_triggered"]:
            return {
                "status": "not_found",
                "timeline": timeline,
                "sast_hints": sast_hints,
                "fuzz": fuzz_result,
                "elapsed_seconds": round(time.time() - started, 3),
            }
        crash_run = direct
    else:
        crash_run = fuzz_result["crash"]

    crash = collect_crash(crash_run, binary=str(binary_path))
    crash = minimize_crash(crash, str(binary_path))
    loc = localize(crash, root)

    fid = finding_id(crash.get("reproducer", crash.get("payload", "")), loc.get("frame", ""))
    finding = {
        "finding_id": fid,
        "severity": "high",
        "reproducer": crash.get("reproducer", crash.get("payload")),
        "source_file": loc["source_path"],
        "function": loc["function"],
        "line": loc["line"],
        "sanitizer": crash.get("sanitizer", "AddressSanitizer"),
        "stack_trace": crash.get("stack_trace", crash.get("stderr_excerpt", "")),
        "source_slice": loc.get("source_slice", ""),
        "evidence": [
            {"type": "sanitizer_stderr", "content": crash.get("stderr_excerpt", "")[:2000]},
            {"type": "sast_hint", "content": str(sast_hints)},
            {"type": "frame", "content": loc.get("frame", "")},
        ],
    }

    evidence_dir = root / "reports" / ".discovery"
    save_crash(crash, evidence_dir)

    return {
        "status": "confirmed",
        "finding": finding,
        "crash": crash,
        "localization": loc,
        "sast_hints": sast_hints,
        "fuzz": fuzz_result,
        "timeline": timeline,
        "elapsed_seconds": round(time.time() - started, 3),
    }
