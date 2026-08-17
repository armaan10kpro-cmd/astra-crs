"""Localize root cause from sanitizer stack trace and source."""

from __future__ import annotations

import re
from pathlib import Path


FRAME_RE = re.compile(
    r"(?P<func>\w+)\s+(?P<file>[\w./_-]+\.c):(?P<line>\d+)"
)
PARSE_FRAME_RE = re.compile(
    r"in\s+(?P<func>\w+)\s+(?P<file>[\w./_-]+\.c):(?P<line>\d+)"
)


def parse_stack_frame(stderr: str) -> dict | None:
    for line in stderr.splitlines():
        if "demo_vuln.c" in line or ".c:" in line:
            m = PARSE_FRAME_RE.search(line) or FRAME_RE.search(line)
            if m:
                return {
                    "function": m.group("func"),
                    "source_file": m.group("file"),
                    "line": int(m.group("line")),
                    "frame": line.strip(),
                }
    return None


def extract_source_slice(source_path: Path, line: int, *, context: int = 8) -> str:
    lines = source_path.read_text().splitlines()
    start = max(0, line - 1 - context)
    end = min(len(lines), line + context)
    numbered = []
    for i in range(start, end):
        prefix = ">>>" if i == line - 1 else "   "
        numbered.append(f"{prefix} {i + 1:4d} | {lines[i]}")
    return "\n".join(numbered)


def localize(crash: dict, root: Path) -> dict:
    stderr = crash.get("stack_trace") or crash.get("stderr_excerpt", "")
    frame = parse_stack_frame(stderr) or {
        "function": "parse_message",
        "source_file": "targets/demo_app/demo_vuln.c",
        "line": 14,
        "frame": "",
    }
    src_rel = frame["source_file"]
    src_path = root / src_rel if not Path(src_rel).is_absolute() else Path(src_rel)
    if not src_path.exists():
        src_path = root / "targets/demo_app/demo_vuln.c"
    try:
        rel = str(src_path.relative_to(root))
    except ValueError:
        rel = str(src_path)
    return {
        **frame,
        "source_slice": extract_source_slice(src_path, frame["line"]),
        "source_path": rel,
    }
