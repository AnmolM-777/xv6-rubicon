#include "types.h"
#include "param.h"
#include "riscv.h"
#include "spinlock.h"
#include "proc.h"
#include "defs.h"
#include "budget.h"

struct group {
  struct spinlock lock;
  int used;
  int budget;
  int max;
  int refill;
  int mode;
  uint last_refill;
  int n_allowed;
  int n_blocked;
  int n_refused;
};

struct group groups[NGROUP];

static uint
now_ticks(void)
{
  uint now;

  acquire(&tickslock);
  now = ticks;
  release(&tickslock);
  return now;
}

void
budget_init(void)
{
  int i;

  for (i = 0; i < NGROUP; i++) {
    initlock(&groups[i].lock, "budget");
    groups[i].used = 0;
    groups[i].budget = 0;
    groups[i].max = BUDGET_UNLIMITED;
    groups[i].refill = 0;
    groups[i].mode = BUDGET_FAIL;
    groups[i].last_refill = 0;
    groups[i].n_allowed = 0;
    groups[i].n_blocked = 0;
    groups[i].n_refused = 0;
  }
}

// The caller holds g->lock. Tick arithmetic is unsigned so wraparound is safe.
static void
refill(struct group *g)
{
  uint elapsed;
  int periods;

  elapsed = now_ticks() - g->last_refill;
  periods = elapsed / BUDGET_PERIOD;
  if (periods > 0) {
    if (g->refill > 0 && periods <= (0x7fffffff - g->budget) / g->refill)
      g->budget += periods * g->refill;
    else if (g->refill > 0)
      g->budget = g->max;
    if (g->budget > g->max)
      g->budget = g->max;
    g->last_refill += periods * BUDGET_PERIOD;
  }
}

static int
wait_for_budget(struct group *g)
{
  sleep_prepare(&ticks);
  release(&g->lock);
  sleep();
  acquire(&g->lock);
  return killed(myproc()) ? -1 : 0;
}

int
charge(int gid, int cost)
{
  struct group *g;
  int counted_block = 0;

  if (cost <= 0)
    return 0;
  if (gid < 0 || gid >= NGROUP)
    return -1;

  g = &groups[gid];
  acquire(&g->lock);
  if (g->max == BUDGET_UNLIMITED) {
    release(&g->lock);
    return 0;
  }
  refill(g);
  if (cost > g->max) {
    g->n_refused++;
    release(&g->lock);
    return -1;
  }
  while (g->budget < cost) {
    if (g->mode == BUDGET_FAIL) {
      g->n_refused++;
      release(&g->lock);
      return -1;
    }
    if (!counted_block) {
      g->n_blocked++;
      counted_block = 1;
    }
    if (wait_for_budget(g) < 0) {
      release(&g->lock);
      return -1;
    }
    refill(g);
  }
  g->budget -= cost;
  g->n_allowed++;
  release(&g->lock);
  return 0;
}

int
budget_set(int gid, int max, int refill_amount, int mode)
{
  struct group *g;

  if (gid < 0 || gid >= NGROUP || max < 0 || refill_amount < 0 ||
      (mode != BUDGET_BLOCK && mode != BUDGET_FAIL))
    return -1;
  g = &groups[gid];
  acquire(&g->lock);
  g->used = 1;
  g->max = max;
  g->budget = max;
  g->refill = refill_amount;
  g->mode = mode;
  g->last_refill = now_ticks();
  release(&g->lock);
  return 0;
}

int
budget_get(int gid, struct budgetinfo *out)
{
  struct group *g;

  if (gid < 0 || gid >= NGROUP || out == 0)
    return -1;
  g = &groups[gid];
  acquire(&g->lock);
  refill(g);
  out->budget = g->budget;
  out->max = g->max;
  out->refill = g->refill;
  out->mode = g->mode;
  out->n_allowed = g->n_allowed;
  out->n_blocked = g->n_blocked;
  out->n_refused = g->n_refused;
  release(&g->lock);
  return 0;
}
