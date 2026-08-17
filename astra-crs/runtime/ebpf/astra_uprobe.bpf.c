/*
 * ASTRA-CRS Linux eBPF observation probe.
 *
 * Purpose: demonstrate supported userspace function interception/telemetry.
 * It does NOT rewrite arbitrary user-space memory or kernel state.
 * The user-space controller may consume these events and apply a safe policy
 * at an application-controlled boundary.
 */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct event {
    __u32 pid;
    __u32 tgid;
    __u64 ts_ns;
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 20);
} events SEC(".maps");

SEC("uprobe/parse_message")
int BPF_KPROBE(ast_guard_entry)
{
    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;

    __u64 id = bpf_get_current_pid_tgid();
    e->pid = (__u32)id;
    e->tgid = (__u32)(id >> 32);
    e->ts_ns = bpf_ktime_get_ns();

    bpf_ringbuf_submit(e, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
