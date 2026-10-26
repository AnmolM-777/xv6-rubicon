#include "types.h"
#include "riscv.h"
#include "defs.h"
#include "param.h"
#include "memlayout.h"
#include "spinlock.h"
#include "proc.h"
#include "vm.h"
#include "budget.h"

uint64
sys_exit(void)
{
  int n;
  argint(0, &n);
  kexit(n);
  return 0; // not reached
}

uint64
sys_getpid(void)
{
  return myproc()->pid;
}

uint64
sys_fork(void)
{
  return kfork();
}

uint64
sys_wait(void)
{
  uint64 p;
  argaddr(0, &p);
  return kwait(p);
}

uint64
sys_sbrk(void)
{
  uint64 addr;
  int t;
  int n;

  argint(0, &n);
  argint(1, &t);
  addr = myproc()->sz;

  if (t == SBRK_EAGER || n < 0) {
    if (growproc(n) < 0) {
      return -1;
    }
  } else {
    // Lazily allocate memory for this process: increase its memory
    // size but don't allocate memory. If the processes uses the
    // memory, vmfault() will allocate it.
    if (addr + n < addr)
      return -1;
    if (addr + n > TRAPFRAME)
      return -1;
    myproc()->sz += n;
  }
  return addr;
}

uint64
sys_pause(void)
{
  int n;
  uint ticks0;

  argint(0, &n);
  if (n < 0)
    n = 0;
  acquire(&tickslock);
  ticks0 = ticks;
  while (ticks - ticks0 < n) {
    if (killed(myproc())) {
      release(&tickslock);
      return -1;
    }
    sleep_prepare(&ticks);
    release(&tickslock);
    sleep();
    acquire(&tickslock);
  }
  release(&tickslock);
  return 0;
}

uint64
sys_kill(void)
{
  int pid;

  argint(0, &pid);
  return kkill(pid);
}

// return how many clock tick interrupts have occurred
// since start.
uint64
sys_uptime(void)
{
  uint xticks;

  acquire(&tickslock);
  xticks = ticks;
  release(&tickslock);
  return xticks;
}

uint64
sys_setgroup(void)
{
  int gid;

  argint(0, &gid);
  if (gid < 0 || gid >= NGROUP)
    return -1;
  myproc()->gid = gid;
  return 0;
}

uint64
sys_setbudget(void)
{
  int gid, max, refill, mode;

  argint(0, &gid);
  argint(1, &max);
  argint(2, &refill);
  argint(3, &mode);
  return budget_set(gid, max, refill, mode);
}

uint64
sys_getbudget(void)
{
  int gid;
  uint64 user_info;
  struct budgetinfo info;

  argint(0, &gid);
  argaddr(1, &user_info);
  if (budget_get(gid, &info) < 0)
    return -1;
  if (copyout(myproc()->pagetable, myproc()->sz, user_info, (char *)&info,
              sizeof(info)) < 0)
    return -1;
  return 0;
}

uint64
sys_getgroup(void)
{
  return myproc()->gid;
}
