
## 2025-02-12 - Eliminate N+1 Database Queries in Game Engine
**Learning:** Found an extreme N+1 query and O(N^2) loop bottleneck in `engine.py`'s `process_transition_phase_async`. Calling `session.get()` inside nested iterations for combat and treaty logic triggers excessive queries and slows down the backend considerably.
**Action:** When handling complex entity relationships in SQLModel/SQLAlchemy loops, always iterate over the actions first to build a unique set of IDs, perform a single bulk fetch using `.where(Model.id.in_(list_of_ids))`, and cache the results in a local dictionary (`entity_map`) for O(1) lookups. Additionally, pre-calculate interactions into sets (like a `hostilities` set of attacker/victim ID pairs) to reduce O(N^2) nested logic to O(1) checks.
