## 2024-05-23 - [SQLModel Memory Optimization]
**Learning:** Selecting specific columns (e.g., `select(models.Player.username, ...)`) instead of fetching the full model object significantly reduces memory overhead and database I/O, yielding up to ~80% faster queries in some scenarios.
**Action:** When only specific fields are needed, especially in large loops, select those fields directly instead of the full model.
