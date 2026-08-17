"""Collect and store crash evidence from sanitizer runs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def crash_id(payload: str, stderr: str) -> str:
    digest = hashlib.sha256((payload + stderr[:500]).encode()).hexdigest()[:16]
    return f"crash-{digest}"


def collect_crash(run_result: dict, *, binary: str) -> dict:
    payload = run_result.get("payload", "")
    stderr = run_result.get("stderr", "")
    return {
        "crash_id": crash_id(payload, stderr),
        "binary": binary,
        "payload": payload,
        "payload_length": len(payload),
        "payload_preview": payload[:48],
        "returncode": run_result.get("returncode"),
        "sanitizer": "AddressSanitizer" if "AddressSanitizer" in stderr else (
            "UndefinedBehaviorSanitizer" if "UndefinedBehaviorSanitizer" in stderr else "unknown"
        ),
        "stack_trace": stderr,
        "stderr_excerpt": run_result.get("stderr_excerpt", stderr[:3000]),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def save_crash(crash: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{crash['crash_id']}.json"
    path.write_text(json.dumps(crash, indent=2))
    return path
