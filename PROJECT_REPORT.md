# Project 1: xv6 Rubicon

## 1. Objective and implementation

This project adds per-process-group irreversibility budgets to xv6-riscv.
Processes can select a group with `setgroup(gid)`, configure a group with
`setbudget(gid, max, refill, mode)`, inspect it with `getbudget`, and read
their current group with `getgroup`. The `budgetstat` user program displays
the counters.

Each group has a protected budget record. A system call is charged in
`syscall()` before its handler runs. The cost model charges destructive
operations such as unlink, writes to files owned by another group, and
execution of a foreign file. Console writes and operations on files created
by the same group use lower or zero cost. Two policies are supported:

- **BLOCK** waits until refill makes enough budget available.
- **FAIL** returns `-1` immediately when the call cannot be charged.

Budget refill is based on xv6 ticks and advances in complete 100-tick periods.
The implementation protects group state with spinlocks and avoids holding a
group lock during filesystem lookup. The inode stores its creator group so
the write and exec cost decisions can distinguish local and foreign files.

The merged tree also contains the agent bridge and taint-tracking work from
the second branch. The Python agent validates requests, selects only
predefined tools, and communicates with xv6 through a socket bridge. The
third branch contributes the `gtest`, `bt_fail`, and `bt_block` user-level
budget tests.

## 2. Design diagram

```text
                  user programs
        setbudget / setgroup / budgetstat
             gtest / bt_fail / bt_block
                         |
                         v
                 xv6 system-call trap
                         |
                         v
       syscall() -> syscall_cost(num, process)
                         |
              +----------+----------+
              |                     |
       charge(group, cost)      handler executes
              |                     |
       +------+-------+             |
       |              |             |
   BLOCK waits     FAIL returns     |
       |              |             |
       +-------+------+             |
               v                    v
      group budget + refill   filesystem operation
      (spinlock, counters)   (creator_gid checks)

 Python agent -> validator -> bridge socket -> xv6 shell
```

## 3. Challenges and decisions

The main integration challenge was combining changes that touched the same
Makefile and syscall interfaces. The final Makefile includes all user
programs from all three branches and places the third branch's test sources
under `user/`, where xv6's existing user-program build rules can find them.

Filesystem accounting required an inode ownership field and careful locking.
The implementation records the creator group when an inode is created and
uses that value for later write and exec decisions. Refill logic preserves a
partial tick period rather than discarding it, and blocked calls count once
even if they wake repeatedly.

An additional portability issue appeared because the repository path contains
spaces. The deterministic compiler flag is now quoted so valid checkout paths
are accepted by the shell.

## 4. Validation

The Python bridge, planner, and validator tests were run from `agentic`.
19 tests passed. Three tool tests require a live xv6 bridge socket and could
not run without a booted QEMU instance.

The complete RISC-V build and boot test could not be completed on the current
machine because `riscv64-*-gcc` and `qemu-system-riscv64` are not installed.
On a standard xv6 toolchain host, run:

```sh
make clean
make
make qemu
```

Then run `gtest`, `bt_fail`, and `bt_block` from the xv6 shell, followed by
the existing `usertests` suite.
