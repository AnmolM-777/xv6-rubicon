#include "kernel/types.h"
#include "kernel/fcntl.h"
#include "kernel/param.h"
#include "user/user.h"

int
main(void)
{
  int fd, truncated;
  char buf[20];

  printf("Creating file in group 0...\n");

  fd = open("budgetfile", O_CREATE | O_WRONLY);
  if (fd < 0) {
    printf("Cannot create file\n");
    exit(1);
  }

  write(fd, "important data", 14);
  close(fd);

  setbudget(1, 0, 0, BUDGET_FAIL);

  setgroup(1);
  fd = open("budgetfile", O_WRONLY | O_TRUNC);

  truncated = (fd >= 0);

  if (fd >= 0)
    close(fd);

  setgroup(0);

  if (truncated)
    printf("BUG CONFIRMED: truncation was allowed\n");
  else
    printf("PASS: truncation was blocked\n");

  setbudget(1, -1, 0, BUDGET_FAIL);

  fd = open("budgetfile", O_RDONLY);
  if (fd >= 0) {
    int n = read(fd, buf, sizeof(buf));
    close(fd);
    printf("Remaining file bytes: %d\n", n);
  }

  exit(0);
}
