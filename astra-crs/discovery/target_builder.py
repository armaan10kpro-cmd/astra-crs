"""Build the synthetic vulnerable target with sanitizers."""

import yaml
from typing import Any
from discovery.target import TargetConfig

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
    """Compile a C source file with optional custom flags.

    Returns a tuple of (success, log_tail) where `log_tail` contains the last 4000 characters of
    stdout+stderr for debugging.
    """
    flags = list(cflags or DEFAULT_CFLAGS)
    cmd = [cc, *flags, str(source), "-o", str(output)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    log = (proc.stdout + proc.stderr)[-4000:]
    return proc.returncode == 0, log


def build_demo_app(root: Path) -> tuple[Path, bool, str]:
    """Build the default demo application.

    Returns the binary path, a success flag, and the build log.
    """
    source = root / "targets" / "demo_app" / "demo_vuln.c"
    output = root / "targets" / "demo_app" / "demo_vuln"
    ok, log = build(source, output)
    return output, ok, log


def get_target_config(target_name: str, root: Path) -> TargetConfig | None:
    """Load a target configuration by name.

    Args:
        target_name: Name of the directory under ``targets/`` containing the manifest.
        root: Repository root path.
    Returns:
        TargetConfig instance if a manifest is found, otherwise ``None``.
    """
    manifest_paths = [
        root / "targets" / target_name / "astra.yaml",
        root / "targets" / target_name / "astra.yml",
        root / "targets" / target_name / "astra.json",
    ]
    for manifest in manifest_paths:
        if manifest.is_file():
            try:
                # Use safe_load for yaml files; json fallback handled by TargetConfig.from_manifest
                if manifest.suffix.lower() in {".yaml", ".yml"}:
                    with open(manifest, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    # Convert yaml dict to a temporary file for reuse of from_manifest logic
                    # Write a temporary json representation in memory (no file I/O)
                    # Directly construct TargetConfig
                    return TargetConfig(
                        name=data.get("name", "demo_app"),
                        language=data.get("language", "c"),
                        source_file=data.get("source", data.get("source_file", "demo_vuln.c")),
                        binary=data.get("binary", "demo_vuln"),
                        build_cmd=data.get("build", data.get("build_cmd", "make build")),
                        entrypoint_function=data.get("entrypoint", data.get("entrypoint_function", "parse_message")),
                        tests_cmd=data.get("tests", data.get("tests_cmd", "bash tests/regression.sh")),
                        fuzzer_engine=data.get("fuzzer", data.get("fuzzer_engine", "auto")),
                        root_dir=manifest.parent,
                    )
                else:
                    # JSON manifest – delegate to TargetConfig.from_manifest
                    return TargetConfig.from_manifest(manifest)
            except Exception as e:
                # Log issue and continue to next candidate
                print(f"Failed to load target manifest {manifest}: {e}")
                continue
    return None


def build_target(target_config: Any, root: Path) -> tuple[Path, bool, str]:
    """Build target specified by TargetConfig."""
    source_path = target_config.abs_source_path(root)
    binary_path = target_config.abs_binary_path(root)

    import os
    # Ensure the binary path ends with .exe on Windows for execution
    win_exe_path = binary_path
    if os.name == "nt" and binary_path.suffix == "":
        win_exe_path = binary_path.with_suffix('.exe')

    if hasattr(target_config, "build_cmd") and target_config.build_cmd:
        # Adjust the build command to output the .exe extension on Windows if needed
        cmd = target_config.build_cmd
        if os.name == "nt" and binary_path.suffix == "":
            # Replace "-o <output>" with "-o <output>.exe"
            import shlex
            parts = shlex.split(cmd)
            if "-o" in parts:
                idx = parts.index("-o")
                if idx + 1 < len(parts):
                    parts[idx + 1] = parts[idx + 1] + ".exe"
                cmd = " ".join(parts)
        proc = subprocess.run(cmd, shell=True, cwd=target_config.root_dir, capture_output=True, text=True)
        log = (proc.stdout + proc.stderr)[-4000:]
        built = proc.returncode == 0
        # If the command succeeded but the expected .exe does not exist, rename the output
        # Ensure .exe exists and also provide a file without extension for compatibility
        if os.name == "nt" and binary_path.suffix == "":
            exe_path = binary_path.with_suffix('.exe')
            # If exe_path was created, copy it back to binary_path (no suffix)
            if exe_path.is_file():
                # Overwrite existing binary_path if present
                exe_path.copy(binary_path, overwrite=True)
            else:
                # If exe_path not yet created, fallback to rename logic above
                pass
        # Return appropriate path based on platform
        return (win_exe_path if os.name == "nt" else binary_path), built, log

    # Fallback to default build function
    ok, log = build(source_path, binary_path)
    # On Windows, rename if needed
    if ok and os.name == "nt" and binary_path.suffix == "":
        if binary_path.is_file():
            binary_path.rename(win_exe_path)
        return win_exe_path, ok, log
    return binary_path, ok, log
