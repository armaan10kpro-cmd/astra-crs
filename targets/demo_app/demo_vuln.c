#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
 * Controlled lab target.
 * The bug is deliberately small: a fixed-size stack buffer receives more
 * bytes than it can hold. This is ONLY for local defensive testing.
 */

int parse_message(const char *msg) {
    char buf[32];
    size_t n = strlen(msg);
    /* Intentional training flaw: no destination-size check. */
    memcpy(buf, msg, n + 1);
    return (int)buf[0];
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s <message>\n", argv[0]);
        return 2;
    }
    return parse_message(argv[1]);
}
