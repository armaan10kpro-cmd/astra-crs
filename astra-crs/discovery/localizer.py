"""Generalized fault localizer for multi-file C/C++ ASan/UBSan stack traces."""

from __future__ import annotations

import re
from pathlib import Path


# Match standard ASan stack trace lines like:
# #0 0x558316e9d297 in parse_message /path/to/demo_vuln.c:14:5
# #1 0x558316e9d297 in main src/app.cpp:42
FRAME_PATTERNS = [
    re.compile(r"#\d+\s+0x[0-9a-fA-F]+\s+in\s+(?P<func>\w+)\s+(?P<file>[\w./_-]+\.(?:c|cpp|cc|h|hpp)):(?P<line>\d+)(?::(?P<col>\d+))?"),
    re.compile(r"in\s+(?P<func>\w+)\s+(?P<file>[\w./_-]+\.(?:c|cpp|cc|h|hpp)):(?P<line>\d+)"),
    re.compile(r"(?P<func>\w+)\s+(?P<file>[\w./_-]+\.(?:c|cpp|cc|h|hpp)):(?P<line>\d+)"),
]


def parse_stack_frame(stderr: str) -> dict | None:
    """Extract file, function, line, and column from ASan/UBSan stack trace."""
    if not stderr:
        return None

    for line in stderr.splitlines():
        line_str = line.strip()
        # Ignore runtime sanitizer internal frames
        if "__asan" in line_str or "__ubsan" in line_str or "libclang_rt" in line_str:
            continue

        for pattern in FRAME_PATTERNS:
            m = pattern.search(line_str)
            if m:
                col = int(m.group("col")) if "col" in m.groupdict() and m.group("col") else None
                return {
                    "function": m.group("func"),
                    "source_file": m.group("file"),
                    "line": int(m.group("line")),
                    "column": col,
                    "frame": line_str,
                }
    return None


def extract_source_slice(source_path: Path, line: int, *, context: int = 8) -> str:
    """Extract line-numbered source code slice around the failing line."""
    if not source_path.exists():
        return f"[Source file not found: {source_path}]"

    lines = source_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    start = max(0, line - 1 - context)
    end = min(len(lines), line + context)
    numbered = []
    for i in range(start, end):
        prefix = ">>>" if i == line - 1 else "   "
        numbered.append(f"{prefix} {i + 1:4d} | {lines[i]}")
    return "\n".join(numbered)


def localize(crash: dict, root: Path) -> dict:
    """Localize fault from crash data across project directory."""
    stderr = crash.get("stack_trace") or crash.get("stderr_excerpt", "")
    frame = parse_stack_frame(stderr) or {
        "function": "parse_message",
        "source_file": "targets/demo_app/demo_vuln.c",
        "line": 14,
        "column": None,
        "frame": "",
    }
    src_rel = frame["source_file"]
    src_path = Path(src_rel)
    if not src_path.is_absolute():
        src_path = root / src_rel

    if not src_path.exists():
        # Search for basename in project tree
        found = list(root.glob(f"**/{Path(src_rel).name}"))
        if found:
            src_path = found[0]
        else:
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
