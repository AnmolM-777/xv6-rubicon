# Project 1 journal

## Person B implementation notes

- Each budget group has its own spinlock. The lock order is group lock, then
  `tickslock`; no filesystem lookup is performed while a group lock is held.
- Refill uses unsigned tick subtraction and advances `last_refill` by whole
  100-tick periods, preserving a partial period for the next refill.
- A blocked call increments `n_blocked` once, even when it wakes repeatedly.
  A killed process leaves the wait without being charged.
- `creator_gid` is stored in each inode. The current implementation intentionally
  leaves `setgroup` and `setbudget` available to every process, as specified by
  the assignment; this is a documented policy limitation.
- The filesystem inode layout uses the added `short creator_gid` field. The
  mkfs alignment assertion was removed because the resulting inode size is not
  an exact divisor of the block size.
