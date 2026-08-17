"""Lightweight static-analysis hints for the demo target."""

from __future__ import annotations

import re
from pathlib import Path


def analyze_source(source_path: Path) -> list[dict]:
    """Return heuristic SAST hints (not authoritative)."""
    text = source_path.read_text()
    hints: list[dict] = []
    if re.search(r"memcpy\s*\([^)]+\)", text) and "sizeof(buf)" not in text.split("memcpy")[0][-200:]:
        for m in re.finditer(r"memcpy\s*\(", text):
            line = text[: m.start()].count("\n") + 1
            hints.append(
                {
                    "rule": "unchecked-memcpy",
                    "severity": "medium",
                    "line": line,
                    "message": "memcpy without visible destination bound check",
                }
            )
    if "Intentional training flaw" in text:
        hints.append(
            {
                "rule": "lab-marker",
                "severity": "info",
                "line": None,
                "message": "Deliberate lab vulnerability marker present",
            }
        )
    return hints
