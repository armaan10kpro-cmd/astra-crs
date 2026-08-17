# eBPF Runtime Layer

`astra_uprobe.bpf.c` is intentionally conservative: it observes entry into the demo's `parse_message()` userspace function via a uprobe and emits a ring-buffer event.

The design is deliberate. eBPF is not being presented here as a universal arbitrary-user-space hot patcher. The prototype uses eBPF for runtime visibility and policy signaling, while the application-level safety boundary and permanent source repair remain separately testable.

For a production-grade deployment, the adapter should be extended only with kernel/hook capabilities that are supported on the target distribution and validated in the lab.
