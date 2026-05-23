
## 2023-10-27 - [Engine] N+1 Query Fix via O(1) Pre-Calculated Maps
**Learning:** In SQLAlchemy/SQLModel apps, loops calling `session.get()` inside nested loops cause severe N+1 query and execution scaling problems. Relying on nested loops over raw DB accesses is particularly catastrophic.
**Action:** When evaluating multiple interactions among identical sets of entities over an epoch (e.g., combat & treaty violation), pre-calculate a relationship state map (like a `hostility_map` set) in a single O(N) pass, enabling O(1) checks during subsequent logic phases.
