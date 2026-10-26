#include "kernel/types.h"
#include "kernel/param.h"
#include "user/user.h"

static void
print_group(int gid, struct budgetinfo *bi)
{
  if (bi->max == -1)
    printf("group %d budget unlimited refill %d mode %s allowed %d blocked %d refused %d\n",
           gid, bi->refill, bi->mode == BUDGET_BLOCK ? "BLOCK" : "FAIL",
           bi->n_allowed, bi->n_blocked, bi->n_refused);
  else
    printf("group %d budget %d/%d refill %d mode %s allowed %d blocked %d refused %d\n",
           gid, bi->budget, bi->max, bi->refill,
           bi->mode == BUDGET_BLOCK ? "BLOCK" : "FAIL",
           bi->n_allowed, bi->n_blocked, bi->n_refused);
}

int
main(void)
{
  int gid;
  struct budgetinfo bi;

  for (gid = 0; gid < NGROUP; gid++)
    if (getbudget(gid, &bi) == 0 &&
        (bi.max != -1 || bi.n_allowed != 0 || bi.n_blocked != 0 ||
         bi.n_refused != 0))
      print_group(gid, &bi);
  exit(0);
}
