## 2026-05-02 - Pre-calculate dictionary to avoid O(N^2) DB queries in arrays
**Learning:** In the `backend/src/backend/engine.py` logic handling nested relationship queries inside large loops, I encountered an N+1 query vulnerability when iterating over subsets.
**Action:** Always extract relationship keys required out of lists early on. Then use `in_` queries in SQLAlchemy to bulk retrieve models and pre-calculate lookup dictionary maps for O(1) relationship and membership lookups within heavily nested iteration structures.
