#ifndef BUDGET_H
#define BUDGET_H

struct budgetinfo {
  int budget;
  int max;
  int refill;
  int mode;
  int n_allowed;
  int n_blocked;
  int n_refused;
};

#endif
