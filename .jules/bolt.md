
## 2024-05-24 - [SQLAlchemy N+1 Queries in Loops]
**Learning:** Using `session.get(Model, id)` inside a loop (like resolving actions or iterating Accords) triggers N+1 database queries. Even though `session.get` uses the identity map, the initial fetch for each unique entity still incurs a database roundtrip.
**Action:** Always pre-fetch all required entities outside the loop using `session.exec(select(Model).where(Model.id.in_(list_of_ids)))` and store them in a local dictionary (`{model.id: model}`). Then, replace `session.get` inside the loop with `local_dict.get(id)`. This converts O(N) database queries into a single bulk fetch and O(N) memory lookups.
