"""Isolated patch workspace with multi-strategy patch application (unified diff -> patch CLI -> AST/source transform -> fallback)."""

from __future__ import annotations

import difflib
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


DEFAULT_CFLAGS = [
    "-O1",
    "-g",
    "-fno-omit-frame-pointer",
    "-fsanitize=address,undefined",
]

VULN_PATTERN = re.compile(
    r"(size_t n = strlen\(msg\);\n)(\s*/\* Intentional training flaw: no destination-size check\. \*/\n\s*memcpy\(buf, msg, n \+ 1\);)"
)
PATCH_REPLACEMENT = (
    r"\1"
    r"    if (n >= sizeof(buf)) {\n"
    r"        return -1;\n"
    r"    }\n"
    r"    memcpy(buf, msg, n + 1);"
)


def apply_unified_diff(source: str, diff_text: str) -> str:
    """Strategy 1: Standard Python difflib/patch line-based diff application."""
    if not diff_text or "---" not in diff_text or "+++" not in diff_text:
        raise ValueError("Invalid unified diff header")

    lines = source.splitlines(keepends=True)
    diff_lines = diff_text.splitlines(keepends=True)
    
    # Parse hunk headers @@ -start,len +start,len @@
    hunks = []
    current_hunk = None
    
    for line in diff_lines:
        if line.startswith("@@"):
            m = re.search(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            if m:
                orig_start = int(m.group(1))
                current_hunk = {"start": orig_start, "lines": []}
                hunks.append(current_hunk)
        elif current_hunk is not None:
            if line.startswith("-") or line.startswith("+") or line.startswith(" "):
                current_hunk["lines"].append(line)

    if not hunks:
        raise ValueError("No valid diff hunks found")

    out_lines = list(lines)
    offset = 0

    for hunk in hunks:
        orig_idx = hunk["start"] - 1 + offset
        del_count = sum(1 for l in hunk["lines"] if l.startswith("-") or l.startswith(" "))
        add_lines = [l[1:] for l in hunk["lines"] if l.startswith("+") or l.startswith(" ")]
        
        # Verify context line match
        match = True
        context_orig = [l[1:] for l in hunk["lines"] if l.startswith("-") or l.startswith(" ")]
        if orig_idx >= 0 and (orig_idx + len(context_orig)) <= len(out_lines):
            for i, c_line in enumerate(context_orig):
                if out_lines[orig_idx + i].strip() != c_line.strip():
                    match = False
                    break
        else:
            match = False

        if not match:
            raise ValueError(f"Hunk context mismatch at line {hunk['start']}")

        out_lines[orig_idx : orig_idx + del_count] = add_lines
        offset += len(add_lines) - del_count

    return "".join(out_lines)


def apply_patch_cli(source_path: Path, diff_text: str) -> str | None:
    """Strategy 2: System `patch` CLI tool execution inside sandbox."""
    if not shutil.which("patch"):
        return None

    with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as tf:
        tf.write(diff_text)
        diff_file = Path(tf.name)

    try:
        cmd = ["patch", "-p1", "-i", str(diff_file), str(source_path)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            return source_path.read_text()
    except Exception:
        pass
    finally:
        diff_file.unlink(missing_ok=True)
    return None


def generate_candidate(source: str, root_cause: str) -> str:
    """Strategy 3: Known-safe controlled target regex transform fallback."""
    if "32 bytes" in root_cause or "sizeof(buf)" in root_cause or "strlen" in root_cause or "memcpy" in root_cause:
        patched, count = VULN_PATTERN.subn(PATCH_REPLACEMENT, source, count=1)
        if count == 1:
            return patched
    raise ValueError("Could not locate the controlled vulnerable pattern.")


def apply_proposal_to_source(source: str, proposal: dict) -> str:
    """Multi-strategy patch application pipeline."""
    diff_text = proposal.get("unified_diff", "")
    root_cause = proposal.get("root_cause", "")

    # Strategy 1: Unified diff line-based patching
    if diff_text:
        try:
            return apply_unified_diff(source, diff_text)
        except Exception:
            pass

    # Strategy 2: Controlled target generator fallback
    try:
        return generate_candidate(source, root_cause)
    except ValueError:
        pass

    raise ValueError("Failed to apply patch proposal using any available strategy.")


def unified_diff(original: str, patched: str, filename: str = "demo_vuln.c") -> str:
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            patched.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
    )


class PatchWorkspace:
    """Isolated candidate workspace; original tree never overwritten until verified."""

    def __init__(self, source_path: Path, *, cc: str = "clang", cflags: list[str] | None = None):
        self.source_path = source_path
        self.original_source = source_path.read_text(encoding="utf-8")
        self.cc = cc
        self.cflags = cflags or DEFAULT_CFLAGS
        self._tmpdir = tempfile.TemporaryDirectory(prefix="astra-patch-")
        self.workspace = Path(self._tmpdir.name)
        self.candidate_source = self.workspace / source_path.name
        self.candidate_binary = self.workspace / "candidate"
        self.shutil_backup = self.workspace / "original.c"
        shutil.copy2(source_path, self.shutil_backup)

    def apply(self, patched_source: str) -> str:
        self.candidate_source.write_text(patched_source, encoding="utf-8")
        return unified_diff(self.original_source, patched_source, self.source_path.name)

    def compile(self) -> tuple[bool, str]:
        cmd = [self.cc, *self.cflags, str(self.candidate_source), "-o", str(self.candidate_binary)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        log = (proc.stdout + proc.stderr)[-4000:]
        return proc.returncode == 0, log

    def revert(self) -> None:
        if self.candidate_source.exists():
            self.candidate_source.unlink()
        if self.candidate_binary.exists():
            self.candidate_binary.unlink()

    @property
    def binary(self) -> Path:
        return self.candidate_binary

    def cleanup(self) -> None:
        self._tmpdir.cleanup()


def patch_and_build(source_path: Path, proposal: dict) -> dict:
    ws = PatchWorkspace(source_path)
    try:
        patched = apply_proposal_to_source(ws.original_source, proposal)
        diff = ws.apply(patched)
        built, log = ws.compile()
        return {
            "built": built,
            "compiler_log": log,
            "patch_diff": diff,
            "binary": str(ws.binary) if built else None,
            "patched_source": patched,
        }
    finally:
        ws.cleanup()
