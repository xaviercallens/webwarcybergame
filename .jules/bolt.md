## 2024-05-18 - Avoid lazy dictionary caches for SQLModel loops
**Learning:** Adding a local dictionary caching wrapper around `session.get()` inside loops avoids redundant Identity Map lookups but fails to solve the underlying N+1 query issue, because initial cache misses still emit single `SELECT` statements.
**Action:** Always pre-fetch required data before loops using `.where(Model.id.in_(list_of_ids))` to explicitly bulk load data into dictionaries to guarantee O(1) query time complexity inside loops.
