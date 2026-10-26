#include "types.h"
#include "param.h"
#include "riscv.h"
#include "spinlock.h"
#include "sleeplock.h"
#include "proc.h"
#include "fs.h"
#include "file.h"
#include "defs.h"
#include "syscall.h"
#include "budget_cost.h"

static int
write_cost(struct proc *p)
{
  int fd;
  struct file *f;

  if (argfd(0, &fd, &f) < 0)
    return 0;
  if (f->type == FD_DEVICE && f->major == CONSOLE)
    return COST_CONSOLE_WRITE;
  if (f->type != FD_INODE)
    return 0;
  ilock(f->ip);
  if (f->ip->creator_gid == p->gid) {
    iunlock(f->ip);
    return COST_WRITE_OWN;
  }
  iunlock(f->ip);
  return COST_WRITE_OTHER;
}

static int
exec_cost(struct proc *p)
{
  char path[MAXPATH];
  struct inode *ip;
  int cost = COST_EXEC_FOREIGN;

  if (argstr(0, path, MAXPATH) < 0)
    return 0;
  begin_op();
  ip = namei(path);
  if (ip != 0) {
    ilock(ip);
    if (ip->creator_gid == p->gid)
      cost = 0;
    iunlockput(ip);
  }
  end_op();
  return cost;
}

int
syscall_cost(int num, struct proc *p)
{
  switch (num) {
  case SYS_unlink:
    return COST_UNLINK;
  case SYS_write:
    return write_cost(p);
  case SYS_exec:
    return exec_cost(p);
  default:
    return 0;
  }
}
