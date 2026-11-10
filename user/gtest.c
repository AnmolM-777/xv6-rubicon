#include "kernel/types.h"
#include "kernel/param.h"
#include "user/user.h"

static void
check(int cond, const char *msg)
{
  if (!cond) {
    printf("gtest FAIL: %s\n", msg);
    exit(1);
  }
}
int
main(int argc, char *argv[])
{
  // If invoked as the exec child target
  if (argc > 1 && strcmp(argv[1], "exec_child") == 0) {
    int g = getgroup();
    if (g != 1) {
      printf("gtest FAIL: exec child expected gid 1, got %d\n", g);
      exit(1);
    }
    printf("gtest: exec child successfully verified gid 1\n");
    exit(0);
  }

  printf("gtest: starting process group tests...\n");

  // 1. Initial group ID must be 0
  int initial_gid = getgroup();
  check(initial_gid == 0, "initial process gid must be 0");
  printf("gtest: initial gid is 0 (PASS)\n");

  // 2. Modifying group ID via setgroup
  check(setgroup(1) == 0, "setgroup(1) should succeed");
  check(getgroup() == 1, "getgroup() should return 1 after setgroup(1)");
  printf("gtest: group change to 1 (PASS)\n");

  // 3. Inheritance across fork()
  int pid = fork();
  check(pid >= 0, "fork failed");
  if (pid == 0) {
    int child_gid = getgroup();
    if (child_gid != 1) {
      printf("gtest child FAIL: expected gid 1, got %d\n", child_gid);
      exit(1);
    }
    exit(0);
  }
  int status = 0;
  wait(&status);
  check(status == 0, "child process fork inheritance check failed");
  printf("gtest: fork inheritance (PASS)\n");

  // 4. Preservation across exec()
  pid = fork();
  check(pid >= 0, "fork for exec failed");
  if (pid == 0) {
    char *args[] = { "gtest", "exec_child", 0 };
    exec("gtest", args);
    printf("gtest FAIL: exec failed\n");
    exit(1);
  }
  wait(&status);
  check(status == 0, "exec preservation check failed");
  printf("gtest: exec preservation (PASS)\n");

  // 5. Invalid group IDs must be rejected and current gid preserved
  check(setgroup(-1) == -1, "setgroup(-1) must return -1");
  check(setgroup(NGROUP) == -1, "setgroup(NGROUP) must return -1");
  check(setgroup(NGROUP + 5) == -1, "setgroup(>NGROUP) must return -1");
  check(getgroup() == 1, "gid must remain 1 after rejected setgroup calls");
  printf("gtest: invalid gid rejection (PASS)\n");

  // Restore group 0
  check(setgroup(0) == 0, "setgroup(0) restore failed");
  check(getgroup() == 0, "getgroup() after restore must be 0");

  printf("gtest: all tests passed\n");
  exit(0);
}
