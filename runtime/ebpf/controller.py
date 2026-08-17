"""eBPF runtime layer — real attach when supported, labelled mock otherwise."""

from __future__ import annotations

import json
import re
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable


class PolicyMode(str, Enum):
    OBSERVE = "observe"
    SIGNAL = "signal"
    DENY_BOUNDARY = "deny-boundary"


class RuntimeMode(str, Enum):
    REAL = "real"
    DRY_RUN = "dry-run"
    MOCK = "mock"


@dataclass
class RuntimeEvent:
    ts: float
    kind: str
    message: str
    pid: int | None = None

    def to_dict(self) -> dict:
        return {"ts": self.ts, "kind": self.kind, "message": self.message, "pid": self.pid}


@dataclass
class RuntimeShield:
    root: Path
    mode: RuntimeMode = RuntimeMode.MOCK
    policy: PolicyMode = PolicyMode.SIGNAL
    attached: bool = False
    events: list[RuntimeEvent] = field(default_factory=list)
    _fail_safe: bool = True

    @property
    def backend(self) -> str:
        if self.mode == RuntimeMode.MOCK:
            return "DEMO / MOCK MODE — not kernel enforcement"
        if self.mode == RuntimeMode.DRY_RUN:
            return "eBPF dry-run (compile-only)"
        return "eBPF uprobe observer"

    def ebpf_available(self) -> bool:
        bpf_c = self.root / "runtime/ebpf/astra_uprobe.bpf.c"
        clang = shutil.which("clang")
        if not bpf_c.exists() or not clang:
            return False
        try:
            out = subprocess.run(["clang", "-print-targets"], capture_output=True, text=True, check=True)
            return "bpf" in out.stdout.lower()
        except Exception:
            return False

    def compile_bpf(self) -> tuple[bool, str]:
        src = self.root / "runtime/ebpf/astra_uprobe.bpf.c"
        obj = self.root / "runtime/ebpf/astra_uprobe.bpf.o"
        cmd = [
            "clang",
            "-O2",
            "-g",
            "-target",
            "bpf",
            "-I/usr/include/x86_64-linux-gnu",
            "-c",
            str(src),
            "-o",
            str(obj),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode == 0, (proc.stdout + proc.stderr)[-2000:]

    def _probe_offset(self, target_binary: str) -> int:
        proc = subprocess.run(
            ["readelf", "-Ws", target_binary],
            capture_output=True,
            text=True,
            check=True,
        )

        pattern = re.compile(
    r"^\s*\d+:\s*([0-9a-fA-F]+)\s+\d+\s+FUNC\s+"
    r"GLOBAL\s+DEFAULT\s+\d+\s+main$"
)

        for line in proc.stdout.splitlines():
            match = pattern.match(line)
            if match:
                return int(match.group(1), 16)

        raise RuntimeError("main symbol not found")

    def attach(self, target_binary: str, *, function: str = "main") -> dict:
        if self.mode == RuntimeMode.MOCK:
            self.attached = True
            self.events.append(
                RuntimeEvent(time.time(), "mock_attach", f"[MOCK] Would attach uprobe on {function} in {target_binary}")
            )
            return {"status": "attached", "backend": self.backend, "mock": True}

        if self.mode == RuntimeMode.DRY_RUN:
            ok, log = self.compile_bpf()
            self.events.append(RuntimeEvent(time.time(), "dry_run", f"BPF compile ok={ok}"))
            return {"status": "dry-run", "compile_ok": ok, "log": log, "backend": self.backend}

        ok, log = self.compile_bpf()
        if not ok:
            self.mode = RuntimeMode.MOCK
            self.events.append(RuntimeEvent(time.time(), "fallback", "BPF compile failed; using MOCK"))
            return self.attach(target_binary, function=function)

        loader = self.root / "runtime/ebpf/astra_loader"
        loader_source = self.root / "runtime/ebpf/astra_loader.c"

        if not loader.exists():
            try:
                loader_flags = subprocess.check_output(
                    ["pkg-config", "--cflags", "--libs", "libbpf"],
                    text=True,
                ).split()

                loader_build = subprocess.run(
                    [
                        "gcc",
                        "-O2",
                        "-Wall",
                        str(loader_source),
                        "-o",
                        str(loader),
                        *loader_flags,
                    ],
                    capture_output=True,
                    text=True,
                )
            except Exception as exc:
                self.attached = False
                self.events.append(
                    RuntimeEvent(
                        time.time(),
                        "real_loader_error",
                        f"Loader build setup failed: {exc}",
                    )
                )
                return {
                    "status": "error",
                    "backend": self.backend,
                    "error": str(exc),
                }

            if loader_build.returncode != 0:
                self.attached = False
                self.events.append(
                    RuntimeEvent(
                        time.time(),
                        "real_loader_error",
                        loader_build.stderr[-1000:],
                    )
                )
                return {
                    "status": "error",
                    "backend": self.backend,
                    "error": "libbpf loader build failed",
                }

        try:
            offset = self._probe_offset(target_binary)

            sudo_check = subprocess.run(
                ["sudo", "-n", "true"],
                capture_output=True,
                text=True,
            )
            if sudo_check.returncode != 0:
                raise RuntimeError(
                    "sudo credentials are not cached; run 'sudo -v' first"
                )

            proc = subprocess.Popen(
                [
                    "sudo",
                    "-n",
                    str(loader),
                    str(self.root / "runtime/ebpf/astra_uprobe.bpf.o"),
                    target_binary,
                    hex(offset),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            attached_line = (
                proc.stdout.readline().strip()
                if proc.stdout
                else ""
            )

            if attached_line.startswith("ATTACHED"):
                self.attached = True
                self.events.append(
                    RuntimeEvent(
                        time.time(),
                        "kernel_attach",
                        attached_line,
                        pid=None,
                    )
                )
            else:
                self.attached = False
                error_line = (
                    proc.stderr.readline().strip()
                    if proc.stderr
                    else attached_line
                )
                self.events.append(
                    RuntimeEvent(
                        time.time(),
                        "real_loader_error",
                        error_line or "Kernel loader did not attach",
                    )
                )
                proc.terminate()
                return {
                    "status": "error",
                    "backend": self.backend,
                    "error": error_line or "Kernel loader did not attach",
                }

            target_run = subprocess.run(
                [target_binary, "OK"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            event_line = (
                proc.stdout.readline().strip()
                if proc.stdout
                else ""
            )

            real_event = False

            if event_line.startswith("{"):
                try:
                    event_data = json.loads(event_line)

                    self.events.append(
                        RuntimeEvent(
                            time.time(),
                            "probe_hit",
                            "Real kernel uprobe event received",
                            pid=event_data.get("pid"),
                        )
                    )
                    real_event = True

                except json.JSONDecodeError:
                    self.events.append(
                        RuntimeEvent(
                            time.time(),
                            "real_loader_output",
                            event_line,
                        )
                    )

            if proc.poll() is None:
                proc.terminate()

            return {
                "status": "attached",
                "backend": self.backend,
                "compile_log": log,
                "target_returncode": target_run.returncode,
                "real_event": real_event,
            }

        except Exception as exc:
            self.attached = False
            self.events.append(
                RuntimeEvent(
                    time.time(),
                    "real_loader_error",
                    str(exc),
                )
            )
            return {
                "status": "error",
                "backend": self.backend,
                "error": str(exc),
            }

    def detach(self) -> dict:
        self.attached = False
        self.events.append(RuntimeEvent(time.time(), "detach", "Runtime shield detached"))
        return {"status": "detached"}

    def simulate_suspicious_call(self, msg_len: int) -> RuntimeEvent:
        """Demo: emit protective event for oversized input observation."""
        suspicious = msg_len >= 32
        kind = "policy_alert" if suspicious else "observe_ok"
        message = (
            f"Suspicious input length {msg_len} — protective signal emitted (no memory rewrite)"
            if suspicious
            else f"Normal input length {msg_len}"
        )
        ev = RuntimeEvent(time.time(), kind, message)
        self.events.append(ev)
        return ev

    def event_stream(self) -> list[dict]:
        return [e.to_dict() for e in self.events]

    def status(self) -> dict:
        return {
            "backend": self.backend,
            "mode": self.mode.value,
            "policy": self.policy.value,
            "attached": self.attached,
            "fail_safe": self._fail_safe,
            "events_count": len(self.events),
            "ebpf_kernel_support": self.ebpf_available(),
            "bpftool_available": shutil.which("bpftool") is not None,
        }


def create_shield(root: Path, mode: str = "mock") -> RuntimeShield:
    mode_map = {
        "mock": RuntimeMode.MOCK,
        "ebpf": RuntimeMode.REAL,
        "dry-run": RuntimeMode.DRY_RUN,
    }
    return RuntimeShield(root=root, mode=mode_map.get(mode, RuntimeMode.MOCK))
