"""Proof-carrying patch report generation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def write_proof_report(
    root: Path,
    finding: dict,
    *,
    discovery: dict,
    proposal: dict,
    patch_result: dict,
    symbolic: dict,
    exploit_check: dict,
    adversarial: dict,
    regression: dict,
    verdict: dict,
    attempts: list[dict],
    runtime: dict,
    resources: dict,
) -> Path:
    fid = finding["finding_id"]
    out_dir = root / "reports" / fid
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "finding.json").write_text(json.dumps(finding, indent=2))
    (out_dir / "root_cause.md").write_text(
        f"# Root Cause\n\n{proposal.get('root_cause', 'n/a')}\n\n"
        f"## Proposed change\n\n{proposal.get('proposed_change', 'n/a')}\n"
    )
    (out_dir / "patch.diff").write_text(patch_result.get("patch_diff", proposal.get("unified_diff", "")))
    (out_dir / "compiler.log").write_text(patch_result.get("compiler_log", ""))
    (out_dir / "original_reproducer.log").write_text(
        json.dumps(exploit_check, indent=2)
    )
    (out_dir / "adversarial_tests.json").write_text(json.dumps(adversarial, indent=2))
    (out_dir / "regression_results.json").write_text(json.dumps(regression, indent=2))
    (out_dir / "symbolic_results.json").write_text(json.dumps(symbolic, indent=2))
    (out_dir / "final_verdict.json").write_text(json.dumps(verdict, indent=2))
    (out_dir / "attempts.json").write_text(json.dumps(attempts, indent=2))

    proof_md = _proof_of_fix_md(
        finding, proposal, symbolic, exploit_check, adversarial, regression, verdict, runtime, resources
    )
    (out_dir / "proof_of_fix.md").write_text(proof_md)

    summary = {
        "finding_id": fid,
        "verdict": verdict["verdict"],
        "report_dir": str(out_dir.relative_to(root)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "attempts": len(attempts),
    }
    (root / "reports" / "latest.json").write_text(json.dumps(summary, indent=2))
    return out_dir


def _proof_of_fix_md(finding, proposal, symbolic, exploit_check, adversarial, regression, verdict, runtime, resources) -> str:
    return f"""# ASTRA-CRS Proof of Fix

**Finding:** `{finding.get('finding_id')}`  
**Verdict:** `{verdict.get('verdict')}`  
**Generated:** {datetime.now(timezone.utc).isoformat()}

## 1. What failed?

Stack buffer overflow in `{finding.get('function')}()` at `{finding.get('source_file')}:{finding.get('line')}`.
Sanitizer: {finding.get('sanitizer')}.

## 2. Why did it fail?

{proposal.get('root_cause', 'n/a')}

## 3. What code changed?

{proposal.get('proposed_change', 'n/a')}

See `patch.diff` for unified diff.

## 4. Which property was verified?

{symbolic.get('property', 'n/a')}

Engine: `{symbolic.get('engine')}` — Status: `{symbolic.get('status')}`

## 5. Did the original exploit disappear?

{'Yes' if exploit_check.get('pass') else 'No'} — reproducer no longer triggers sanitizer: `{exploit_check.get('exploit_eliminated')}`

## 6. Did mutated attacks succeed?

Adversarial status: `{adversarial.get('status')}`  
Attacks executed: {adversarial.get('attacks_executed', 0)}  
Sanitizer failures: {adversarial.get('sanitizer_failures', 0)}

## 7. Did legitimate functionality survive?

Regression: `{regression.get('status')}` — {regression.get('passed', 0)}/{regression.get('mandatory_tests', 0)} mandatory tests passed.

## 8. Why was the patch accepted or rejected?

Judge checks:

```json
{json.dumps(verdict.get('checks', {}), indent=2)}
```

## Runtime protection

Backend: `{runtime.get('backend')}`  
Mode: `{runtime.get('mode')}`  
Policy: {runtime.get('policy', 'n/a')}

## Resource use

```json
{json.dumps(resources, indent=2)}
```

> A patch is accepted only when deterministic property check, rebuild, regression, adversarial suite, and exploit elimination all pass.
"""


def write_run_summary(root: Path, payload: dict) -> None:
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "run.json").write_text(json.dumps(payload, indent=2))
    md_lines = [
        "# ASTRA-CRS Run Summary",
        "",
        f"**Final status:** `{payload.get('final_status')}`",
        f"**Finding:** `{payload.get('finding_id', '-')}`",
        "",
        "See proof-carrying report under `reports/<finding_id>/`.",
    ]
    (reports / "run.md").write_text("\n".join(md_lines) + "\n")
