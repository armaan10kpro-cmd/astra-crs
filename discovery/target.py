"""Target abstraction and manifest loader (astra.yaml / astra.json)."""

from __future__ import annotations

import os

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TargetConfig:
    name: str
    language: str
    source_file: str
    binary: str
    build_cmd: str
    entrypoint_function: str = "parse_message"
    tests_cmd: str = "bash tests/regression.sh"
    fuzzer_engine: str = "auto"
    root_dir: Path = field(default_factory=lambda: Path("."))

    @classmethod
    def from_manifest(cls, manifest_path: Path) -> TargetConfig:
        manifest_path = manifest_path.resolve()
        content = manifest_path.read_text(encoding="utf-8")
        
        # Simple JSON parser fallback for .json or custom lightweight key: value parser for .yaml without PyYAML dependency
        if manifest_path.suffix.lower() == ".json":
            data = json.loads(content)
        else:
            data = cls._parse_simple_yaml(content)

        root = manifest_path.parent
        return cls(
            name=data.get("name", "demo_app"),
            language=data.get("language", "c"),
            source_file=data.get("source", data.get("source_file", "demo_vuln.c")),
            binary=data.get("binary", "demo_vuln"),
            build_cmd=data.get("build", data.get("build_cmd", "make build")),
            entrypoint_function=data.get("entrypoint", data.get("entrypoint_function", "parse_message")),
            tests_cmd=data.get("tests", data.get("tests_cmd", "bash tests/regression.sh")),
            fuzzer_engine=data.get("fuzzer", data.get("fuzzer_engine", "auto")),
            root_dir=root,
        )

    @classmethod
    def _parse_simple_yaml(cls, text: str) -> dict[str, Any]:
        """Simple line-based YAML parser for key: value pairs."""
        data: dict[str, Any] = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                val = val.strip().strip("\"'")
                data[key.strip()] = val
        return data

    def abs_source_path(self, repo_root: Path) -> Path:
        p = Path(self.source_file)
        if p.is_absolute():
            return p
        if (self.root_dir / p).exists():
            return self.root_dir / p
        return repo_root / p

    def abs_binary_path(self, repo_root: Path) -> Path:
        p = Path(self.binary)
        if p.is_absolute():
            return p
        # On Windows, binaries may need .exe extension
        if os.name == "nt" and p.suffix == "":
            # Check if .exe exists in the same location
            candidate = (self.root_dir / p).with_suffix('.exe')
            if candidate.is_file():
                return candidate
            candidate2 = (repo_root / p).with_suffix('.exe')
            if candidate2.is_file():
                return candidate2
        if (self.root_dir / p).exists():
            return self.root_dir / p
        return repo_root / p

    def rel_source_path(self, repo_root: Path) -> str:
        try:
            return str(self.abs_source_path(repo_root).relative_to(repo_root))
        except ValueError:
            return str(self.abs_source_path(repo_root))
