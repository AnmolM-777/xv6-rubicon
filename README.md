# xv6-rubicon
Per-group irreversibility budgets for xv6-riscv. Hard-to-undo syscalls (unlink, writes, exec of foreign files) are charged to a process group before they run, then blocked or refused when the budget runs out. CSL3030, IIT Jodhpur.

The project-1 kernel interface is:

- `setgroup(gid)` and `getgroup()` select and inspect a process group.
- `setbudget(gid, max, refill, mode)` configures a group. `mode` is
  `BUDGET_BLOCK` or `BUDGET_FAIL`, and refill is measured per 100 ticks.
- `getbudget(gid, &info)` reads the counters used by `budgetstat`.

The budget decision is made in `syscall()` before the syscall handler runs.
The xv6 toolchain and QEMU are required to build and boot the tree; use
`make qemu` from the repository root.
