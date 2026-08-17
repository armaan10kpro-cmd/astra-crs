#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

struct event {
    unsigned int pid;
    unsigned int tgid;
    unsigned long long ts_ns;
};

static volatile sig_atomic_t stop = 0;

static void on_signal(int sig)
{
    (void)sig;
    stop = 1;
}

static int handle_event(void *ctx, void *data, size_t size)
{
    (void)ctx;

    if (size != sizeof(struct event)) {
        fprintf(stderr, "unexpected event size: %zu\n", size);
        return 0;
    }

    const struct event *e = data;

    printf(
        "{\"kind\":\"probe_hit\",\"pid\":%u,\"tgid\":%u,\"ts_ns\":%llu}\n",
        e->pid,
        e->tgid,
        e->ts_ns
    );
    fflush(stdout);

    stop = 1;
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "usage: %s <bpf-object> <target-binary> <offset-hex>\n", argv[0]);
        return 2;
    }

    const char *obj_path = argv[1];
    const char *target = argv[2];
char *end = NULL;
unsigned long long offset = strtoull(argv[3], &end, 0);

if (end == argv[3] || *end != '\0') {
    fprintf(stderr, "invalid offset: %s\n", argv[3]);
    return 2;
}

    libbpf_set_strict_mode(LIBBPF_STRICT_ALL);

    struct bpf_object *obj =
        bpf_object__open_file(obj_path, NULL);

    if (!obj) {
        fprintf(stderr, "bpf_object__open_file failed\n");
        return 1;
    }

    int err = bpf_object__load(obj);
    if (err) {
        fprintf(stderr, "bpf_object__load failed: %d\n", err);
        bpf_object__close(obj);
        return 1;
    }

    struct bpf_program *prog =
        bpf_object__find_program_by_name(obj, "ast_guard_entry");

    if (!prog) {
        fprintf(stderr, "ast_guard_entry not found\n");
        bpf_object__close(obj);
        return 1;
    }

    struct bpf_link *link =
    bpf_program__attach_uprobe(
        prog,
        false,
        -1,
        target,
        offset
    );   

    if (!link) {
        fprintf(stderr, "bpf_program__attach_uprobe failed\n");
        bpf_object__close(obj);
        return 1;
    }

    struct bpf_map *map =
        bpf_object__find_map_by_name(obj, "events");

    if (!map) {
        fprintf(stderr, "events map not found\n");
        bpf_link__destroy(link);
        bpf_object__close(obj);
        return 1;
    }

    int map_fd = bpf_map__fd(map);

    struct ring_buffer *rb =
        ring_buffer__new(map_fd, handle_event, NULL, NULL);

    if (!rb) {
        fprintf(stderr, "ring_buffer__new failed\n");
        bpf_link__destroy(link);
        bpf_object__close(obj);
        return 1;
    }

    signal(SIGINT, on_signal);
    signal(SIGTERM, on_signal);

    printf(
        "ATTACHED target=%s\n",
        target
    );
    fflush(stdout);

    while (!stop) {
        err = ring_buffer__poll(rb, 100);
        if (err < 0 && err != -EINTR) {
            fprintf(stderr, "ring_buffer__poll failed: %d\n", err);
            break;
        }
    }

    ring_buffer__free(rb);
    bpf_link__destroy(link);
    bpf_object__close(obj);

    return 0;
}

