# Linux eBPF setup

This repository can be developed in mock mode on any workstation. Real eBPF mode requires a Linux environment with compatible kernel headers, clang/LLVM BPF support, libbpf development headers, `bpftool`, and sufficient privileges to attach the probe.

Typical package names differ by distribution, so install the distro-equivalent development packages rather than assuming a single package-manager command.

The target binary must expose the symbol `parse_message` (the demo is compiled without stripping symbols).

## Build the BPF object

A typical libbpf/clang workflow is:

```bash
clang -O2 -g -target bpf -c runtime/ebpf/astra_uprobe.bpf.c -o runtime/ebpf/astra_uprobe.bpf.o
```

If your Clang build does not expose the BPF target, use a recent distro LLVM package.

The next layer is a small libbpf loader that attaches `uprobe/parse_message` to the target binary and consumes the ring buffer. The current repository keeps that loader separate because libbpf was not available in the build environment used to generate this scaffold.
