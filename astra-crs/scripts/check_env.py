#!/usr/bin/env python3
import shutil
import subprocess

checks = ["clang", "bpftool", "llc", "docker", "cc"]
for name in checks:
    path = shutil.which(name)
    print(f"{name:10} {'YES: ' + path if path else 'NO'}")

try:
    import z3  # noqa: F401
    print("z3        YES")
except Exception:
    print("z3        NO")

try:
    out = subprocess.run(["clang", "-print-targets"], capture_output=True, text=True, check=True).stdout
    print("clang-bpf ", "YES" if "bpf" in out.lower() else "NO")
except Exception:
    print("clang-bpf NO")
