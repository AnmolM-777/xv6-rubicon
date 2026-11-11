#include "kernel/types.h"
#include "kernel/param.h"
#include "kernel/fcntl.h"
#include "user/user.h"

static void
check(int cond, const char *msg)
{
  if (!cond) {
    printf("bt_block FAIL: %s\n", msg);
    exit(1);
  }
}

static void
create_file(const char *name)
{
  int fd = open(name, O_CREATE | O_WRONLY);
  if (fd < 0) {
    printf("bt_block: cannot create %s\n", name);
    exit(1);
  }

  write(fd, "test", 4);
  close(fd);
}

int
main(void)
{
  const int TEST_GID = 6;
  const char *files[6] = {"btb_f0", "btb_f1", "btb_f2",
                          "btb_f3", "btb_f4", "btb_f5"};
  int results[6];
  struct budgetinfo bi;

  printf("bt_block: starting BLOCK mode refill-and-resumption test...\n");

  // Step 1: Ensure we are in group 0 and create 6 test files
  setgroup(0);
  for (int i = 0; i < 6; i++) {
    unlink(files[i]); // Clean up any existing file
    create_file(files[i]);
  }

  // Step 2: Configure group 6: max=50, refill=50 per 100 ticks, mode=BLOCK
  check(setbudget(TEST_GID, 50, 50, BUDGET_BLOCK) == 0, "setbudget failed");

  // Step 3: Enter group 6
  check(setgroup(TEST_GID) == 0, "setgroup(TEST_GID) failed");

  int start_tick = uptime();

  // Step 4: Perform first 5 unlinks (consumes entire budget of 50)
  for (int i = 0; i < 5; i++) {
    results[i] = unlink(files[i]);
  }

  int mid_tick = uptime();

  // Step 5: Perform 6th unlink - should BLOCK until 100-tick period refills
  // 50 budget, then complete
  results[5] = unlink(files[5]);

  int end_tick = uptime();

  // Step 6: Return to group 0 to safely print and verify
  setgroup(0);

  // Step 7: Verify all operations succeeded
  for (int i = 0; i < 6; i++) {
    if (results[i] != 0) {
      printf("bt_block FAIL: op %d returned %d, expected 0\n", i + 1,
             results[i]);
      exit(1);
    }
  }

  printf("bt_block: all 6 operations succeeded (PASS)\n");

  // Step 8: Verify actual blocking duration
  int elapsed_blocked = end_tick - mid_tick;
  printf("bt_block: start=%d, after_5th=%d, after_6th=%d (blocked_wait=%d "
         "ticks)\n",
         start_tick, mid_tick, end_tick, elapsed_blocked);

  // BUDGET_PERIOD is 100 ticks. The 6th op must have waited for the period
  // boundary.
  check(elapsed_blocked >= 80,
        "6th operation did not block for expected refill duration");
  printf("bt_block: actual blocking and timer wake-up verified (PASS)\n");

  // Step 9: Verify 6th file was actually unlinked
  int fd = open(files[5], O_RDONLY);
  check(fd < 0, "6th file should have been deleted after unblocking");
  printf("bt_block: filesystem operation executed successfully after refill "
         "(PASS)\n");

  // Step 10: Verify budget counters
  check(getbudget(TEST_GID, &bi) == 0, "getbudget failed");
  check(bi.n_allowed == 6, "n_allowed must be 6");
  check(bi.n_blocked == 1, "n_blocked must be 1 (counted once per blocked call)");
  check(bi.n_refused == 0, "n_refused must be 0");
  check(bi.budget == 40, "remaining budget must be 40 (50 refill - 10 cost)");

  printf("bt_block: counters verified (allowed=6, blocked=1, refused=0, "
         "budget=40) (PASS)\n");

  printf("bt_block: all tests passed\n");
  exit(0);
}
