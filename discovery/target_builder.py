"""Build the synthetic vulnerable target with sanitizers."""

from __future__ import annotations

import subprocess
from pathlib import Path


DEFAULT_CFLAGS = [
    "-O1",
    "-g",
    "-fno-omit-frame-pointer",
    "-fsanitize=address,undefined",
]


def build(
    source: Path,
    output: Path,
    *,
    cc: str = "clang",
    cflags: list[str] | None = None,
) -> tuple[bool, str]:
    flags = list(cflags or DEFAULT_CFLAGS)
    cmd = [cc, *flags, str(source), "-o", str(output)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    log = (proc.stdout + proc.stderr)[-4000:]
    return proc.returncode == 0, log


def build_demo_app(root: Path) -> tuple[Path, bool, str]:
    source = root / "targets/demo_app/demo_vuln.c"
    output = root / "targets/demo_app/demo_vuln"
    ok, log = build(source, output)
    return output, ok, log
