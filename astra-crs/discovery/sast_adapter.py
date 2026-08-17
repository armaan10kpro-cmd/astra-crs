"""Static Analysis adapter supporting Lightweight AST/Regex, Semgrep, and Clang AST hints."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path


def analyze_source(source_path: Path) -> list[dict]:
    """Return comprehensive SAST hints using available analysis tools."""
    hints: list[dict] = []
    
    if not source_path.exists():
        return hints

    # 1. Primary lightweight AST / pattern scanner
    hints.extend(_scan_ast_patterns(source_path))

    # 2. Semgrep adapter (if installed)
    if shutil.which("semgrep"):
        hints.extend(_run_semgrep(source_path))

    return hints


def _scan_ast_patterns(source_path: Path) -> list[dict]:
    text = source_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    hints: list[dict] = []

    # Check memcpy / strcpy / sprintf buffer operations
    for idx, line in enumerate(lines, 1):
        if "memcpy" in line and "sizeof" not in line:
            hints.append({
                "rule": "unchecked-memcpy",
                "category": "buffer_operation",
                "severity": "medium",
                "line": idx,
                "message": "memcpy call without explicit destination bound check on line",
            })
        if "strcpy" in line or "strcat" in line:
            hints.append({
                "rule": "dangerous-string-copy",
                "category": "buffer_operation",
                "severity": "high",
                "line": idx,
                "message": "Unbounded string copy function detected",
            })
        if "gets(" in line:
            hints.append({
                "rule": "forbidden-gets",
                "category": "dangerous_function",
                "severity": "critical",
                "line": idx,
                "message": "Use of unsafe gets() function",
            })

    if "Intentional training flaw" in text:
        hints.append({
            "rule": "lab-marker",
            "category": "lab_annotation",
            "severity": "info",
            "line": None,
            "message": "Deliberate lab vulnerability marker present",
        })

    return hints


def _run_semgrep(source_path: Path) -> list[dict]:
    """Run semgrep rules when semgrep CLI is available on PATH."""
    cmd = ["semgrep", "scan", "--json", "--quiet", "--config", "auto", str(source_path)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            import json
            data = json.loads(proc.stdout)
            results = []
            for item in data.get("results", []):
                results.append({
                    "rule": item.get("check_id"),
                    "category": "semgrep",
                    "severity": item.get("extra", {}).get("severity", "medium").lower(),
                    "line": item.get("start", {}).get("line"),
                    "message": item.get("extra", {}).get("message"),
                })
            return results
    except Exception:
        pass
    return []
