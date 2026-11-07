#include "kernel/types.h"
#include "user/user.h"

int
main(int argc, char *argv[])
{
    if (argc != 2) {
        printf("Usage: marktaint filename\n");
        exit(1);
    }

    if (taintfile(argv[1]) < 0) {
        printf("Failed to mark file as tainted\n");
        exit(1);
    }

    printf("File marked as tainted: %s\n", argv[1]);
    exit(0);
}
