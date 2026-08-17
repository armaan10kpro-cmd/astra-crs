#!/usr/bin/env python3
"""ASTRA-CRS main orchestrator — full DISCOVER → REPAIR → VERIFY → PROTECT → REPORT pipeline."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from discovery.pipeline import run_discovery
from reasoning.engine import propose_patch
from reasoning.model_provider import get_provider
from runtime.ebpf.controller import create_shield
from verification.adversarial import run_adversarial, verify_original_exploit_eliminated
from verification.patch_judge import judge
from verification.patcher import PatchWorkspace, apply_proposal_to_source
from verification.proof_report import write_proof_report, write_run_summary
from verification.regression import verify as verify_regression
from verification.symbolic import verify_for_finding

MAX_REPAIR_ATTEMPTS = 3
PIPELINE = [
    "discover",
    "localize",
    "reason",
    "repair",
    "verify",
    "adversarial-test",
    "protect",
    "report",
]


from discovery.target import TargetConfig


def measure_resources(start: float, peak_mem: int | None = None) -> dict:
    return {
        "elapsed_seconds": round(time.time() - start, 3),
        "peak_rss_mb": round(peak_mem / (1024 * 1024), 2) if peak_mem else None,
    }


def run_pipeline(
    *,
    root: Path,
    mode: str = "mock",
    provider_name: str | None = None,
    clean: bool = False,
    target: str | Path | None = None,
) -> dict:
    if clean:
        import shutil

        for p in (root / "reports").glob("*"):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            elif p.name not in (".gitkeep",):
                p.unlink(missing_ok=True)

    tracemalloc.start()
    started = time.time()
    provider = get_provider(provider_name)

    target_config = None
    target_binary = None
    if target:
        tp = Path(target)
        if not tp.is_absolute():
            tp = root / tp
        if tp.suffix in (".yaml", ".yml", ".json"):
            target_config = TargetConfig.from_manifest(tp)
        elif tp.is_file():
            target_binary = tp

    # 1. DISCOVER + LOCALIZE

    # Determine target name for discovery
    target_name = None
    if target_config is not None:
        target_name = target_config.name
    # Run discovery with appropriate parameters
    discovery = run_discovery(root, binary=target_binary, target_name=target_name or "demo_app")
    # Determine the path to the binary for runtime protection
    if target_binary is not None:
        protected_binary = target_binary
    else:
        # Use the binary path from the target configuration
        protected_binary = target_config.abs_binary_path(root) if target_config is not None else None
    if discovery.get("status") != "confirmed":
        result = {
            "project": "ASTRA-CRS",
            "pipeline": PIPELINE,
            "final_status": "NO_FINDING" if discovery.get("status") == "not_found" else discovery.get("status", "FAILED").upper(),
            "discovery": discovery,
        }
        write_run_summary(root, result)
        return result


    finding = discovery["finding"]
    reproducer = finding["reproducer"]
    source_path = root / finding["source_file"]

    # 2. REASON + REPAIR loop (max N=3)
    attempts: list[dict] = []
    final_verdict = None
    final_patch_result = None
    final_proposal = None
    symbolic = verify_for_finding(finding)
    exploit_check = {"pass": False}
    adversarial = {"pass": False}
    regression = {"pass": False}
    feedback = ""

    for attempt in range(1, MAX_REPAIR_ATTEMPTS + 1):
        proposal = propose_patch(finding, provider=provider, feedback=feedback, attempt=attempt)
        attempt_record = {"attempt": attempt, "proposal_status": proposal.get("status"), "provider": proposal.get("provider")}

        if proposal.get("status") != "candidate":
            attempt_record["error"] = proposal.get("error")
            attempts.append(attempt_record)
            feedback = proposal.get("error", "malformed output")
            continue

        ws = PatchWorkspace(source_path)
        try:
            patched = apply_proposal_to_source(ws.original_source, proposal)
            diff = ws.apply(patched)
            built, compiler_log = ws.compile()
            attempt_record["built"] = built
            attempt_record["patch_diff"] = diff[:500]

            if not built:
                attempt_record["verdict"] = "REJECTED"
                attempt_record["reason"] = "compilation_failed"
                attempts.append(attempt_record)
                feedback = f"Compilation failed:\n{compiler_log[-800:]}"
                continue

            exploit_check = verify_original_exploit_eliminated(str(ws.binary), reproducer)
            adversarial = run_adversarial(str(ws.binary), reproducer)
            regression = verify_regression(str(ws.binary))

            verdict = judge(
                compile_ok=built,
                patch_valid=True,
                symbolic=symbolic,
                exploit_check=exploit_check,
                adversarial=adversarial,
                regression=regression,
            )
            attempt_record["verdict"] = verdict["verdict"]
            attempt_record["checks"] = verdict["checks"]
            attempts.append(attempt_record)

            final_verdict = verdict
            final_patch_result = {
                "built": built,
                "compiler_log": compiler_log,
                "patch_diff": diff,
                "binary": str(ws.binary),
                "patched_source": patched,
            }
            final_proposal = proposal

            if verdict["verdict"] == "FIX_VERIFIED":
                break
            feedback = json.dumps({k: v for k, v in verdict["checks"].items() if not v})
        finally:
            ws.cleanup()

    # 3. RUNTIME PROTECTION
    shield = create_shield(root, mode=mode)
    attach_result = shield.attach(str(protected_binary))
    shield.simulate_suspicious_call(len(reproducer))
    if len(reproducer) <= 31:
        shield.simulate_suspicious_call(64)
    runtime = {
        **shield.status(),
        "attach": attach_result,
        "policy": "signal/deny-at-safe-boundary; no arbitrary memory rewriting",
        "events": shield.event_stream()[-20:],
    }

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    resources = measure_resources(started, peak)

    final_status = final_verdict["verdict"] if final_verdict else "NO_VERIFIED_FIX"
    if final_verdict and final_verdict["verdict"] != "FIX_VERIFIED":
        final_status = "NO_VERIFIED_FIX"

    report_dir = None
    if final_proposal and final_patch_result and final_verdict:
        report_dir = write_proof_report(
            root,
            finding,
            discovery=discovery,
            proposal=final_proposal,
            patch_result=final_patch_result,
            symbolic=symbolic,
            exploit_check=exploit_check,
            adversarial=adversarial,
            regression=regression,
            verdict=final_verdict,
            attempts=attempts,
            runtime=runtime,
            resources=resources,
        )

    result = {
        "project": "ASTRA-CRS",
        "mode": mode,
        "provider": provider.name,
        "pipeline": PIPELINE,
        "finding_id": finding["finding_id"],
        "discovery": discovery,
        "symbolic_verification": symbolic,
        "attempts": attempts,
        "exploit_check": exploit_check,
        "adversarial": adversarial,
        "regression": regression,
        "runtime_layer": runtime,
        "resources": resources,
        "report_dir": str(report_dir.relative_to(root)) if report_dir else None,
        "final_status": final_status,
    }
    write_run_summary(root, result)
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="ASTRA-CRS orchestrator")
    ap.add_argument("--target", help="Target manifest path (astra.yaml/json) or binary")
    ap.add_argument("--mode", choices=["mock", "ebpf", "dry-run"], default="mock")
    ap.add_argument("--provider", default=os.environ.get("ASTRA_MODEL_PROVIDER", "mock"))
    ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()

    result = run_pipeline(root=ROOT, mode=args.mode, provider_name=args.provider, clean=args.clean, target=args.target)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
