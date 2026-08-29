## 2024-05-15 - [Initial]
**Learning:** Initial entry.
**Action:** Let's keep optimizing.

## 2024-05-15 - [O(N^2) to O(N) Database Lookups in Nested Loops]
**Learning:** In SQLAlchemy/SQLModel loops that evaluate interactions across sets of entities (like Accord violation checks looping over all node actions per Accord), nested `session.get()` calls triggered within the loop are an O(N^2) performance bottleneck.
**Action:** Always pre-calculate the necessary relationship state maps (e.g. `hostilities` set of ID tuples) in a single O(N) pass during initial processing to enable O(1) lookups during the secondary loop.
