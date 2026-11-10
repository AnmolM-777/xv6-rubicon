#include "kernel/types.h"
#include "kernel/param.h"
#include "kernel/fcntl.h"
#include "user/user.h"

static void
check(int cond, const char *msg)
{
  if (!cond) {
    printf("bt_fail FAIL: %s\n", msg);
    exit(1);
  }
}
static void
create_file(const char *name)
{
  int fd = open(name, O_CREATE | O_WRONLY);
  if (fd < 0) {
    printf("bt_fail: cannot create %s\n", name);
    exit(1);
  }
  write(fd, "test", 4);
  close(fd);
}

int
main(void)
{
  const int TEST_GID = 5;
  const char *files[6] = {
    "btf_f0", "btf_f1", "btf_f2", "btf_f3", "btf_f4", "btf_f5"
  };
  int results[6];
  struct budgetinfo bi;

  printf("bt_fail: starting FAIL mode budget exhaustion test...\n");

  // Step 1: Ensure we are in group 0 and create 6 test files
  setgroup(0);
  for (int i = 0; i < 6; i++) {
    unlink(files[i]); // Clean up any existing file from prior runs
    create_file(files[i]);
  }

  // Step 2: Configure group 5 with budget=50, refill=0, mode=FAIL
  check(setbudget(TEST_GID, 50, 0, BUDGET_FAIL) == 0, "setbudget failed");

  // Step 3: Enter group 5
  check(setgroup(TEST_GID) == 0, "setgroup(TEST_GID) failed");

  // Step 4: Perform 6 unlink operations without printf (to avoid burning budget on console writes)
  for (int i = 0; i < 6; i++) {
    results[i] = unlink(files[i]);
  }

  // Step 5: Switch back to group 0 to safely print and verify
  setgroup(0);

  // Step 6: Verify return values
  for (int i = 0; i < 5; i++) {
    if (results[i] != 0) {
      printf("bt_fail FAIL: op %d returned %d, expected 0\n", i + 1, results[i]);
      exit(1);
    }
  }
  if (results[5] != -1) {
    printf("bt_fail FAIL: 6th op returned %d, expected -1\n", results[5]);
    exit(1);
  }
  printf("bt_fail: first 5 operations succeeded, 6th operation rejected (PASS)\n");

  // Step 7: Verify filesystem persistence - the 6th file must NOT have been unlinked
  int fd = open(files[5], O_RDONLY);
  check(fd >= 0, "6th file should still exist on disk");
  close(fd);
  unlink(files[5]); // cleanup
  printf("bt_fail: filesystem state preserved for rejected call (PASS)\n");

  // Step 8: Verify budget counters
  check(getbudget(TEST_GID, &bi) == 0, "getbudget failed");
  check(bi.budget == 0, "remaining budget must be 0");
  check(bi.n_allowed == 5, "n_allowed must be 5");
  check(bi.n_refused == 1, "n_refused must be 1");
  check(bi.n_blocked == 0, "n_blocked must be 0");
  printf("bt_fail: counters verified (allowed=5, refused=1, blocked=0) (PASS)\n");

  printf("bt_fail: all tests passed\n");
  exit(0);
}
