# xv6-rubicon
Per-group irreversibility budgets for xv6-riscv. Hard-to-undo syscalls (unlink, writes, exec of foreign files) are charged to a process group before they run, then blocked or refused when the budget runs out. CSL3030, IIT Jodhpur.
