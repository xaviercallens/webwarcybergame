## 2025-02-20 - O(1) Treaty Violation Lookups
**Learning:** Checking treaty violations in the epoch loop used a nested loop iterating over all nodes and their actions for every single active treaty (O(Accords * Nodes * Actions)). Since combat already processes all breach actions, the engine was performing massive redundant database lookups per node inside the Accords processing step.
**Action:** By pre-calculating a `hostilities = set()` during the combat resolution step (where breach actions are already iterated), treaty checking becomes an O(1) lookup: `(fa.id, fb.id) in hostilities`.
