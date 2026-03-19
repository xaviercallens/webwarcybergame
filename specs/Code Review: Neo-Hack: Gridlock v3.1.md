# Code Review: Neo-Hack: Gridlock (v3.1.0) — Next Iteration Roadmap

> **Target Version**: v3.1.0 · **Priority**: Stability, Usability, Accessibility  
> **Predecessor**: v2.1.0 (369 tests passing) · **Date**: 2026-03-18  
> **Focus Areas**: ① Fix remaining v2.1 debt ② Usability improvements ③ Accessibility ④ Polish

---

## Phase 1: Critical Debt (Must Fix)

### DEBT-001: datetime.utcnow() Deprecation Bomb 🔴 P0

**Impact**: 259 warnings in test output. Will **break** on Python 3.14 (scheduled 2025-10).  
**Files**: `auth.py:33,35` · `models.py` (all `default_factory`) · `main.py:136`

**Fix**:
```python
# Before (deprecated)
from datetime import datetime
expire = datetime.utcnow() + timedelta(minutes=15)

# After
from datetime import datetime, timezone
expire = datetime.now(timezone.utc) + timedelta(minutes=15)

# For models.py default_factory:
created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Estimated LOC**: ~15 lines across 3 files  
**Tests**: Existing 369 tests + verify 0 deprecation warnings

---

### DEBT-002: session.query() → session.exec() 🔴 P0

**Impact**: SQLModel deprecation warning on every auth request.  
**File**: `auth.py:54`

**Fix**:
```python
# Before
user = session.query(Player).filter(Player.username == username).first()

# After
from sqlmodel import select
user = session.exec(select(Player).where(Player.username == username)).first()
```

**Estimated LOC**: 1 line  
**Tests**: Existing auth tests should continue passing

---

### DEBT-003: Foreign Key Indexing 🟡 P1

**Impact**: Slow queries on PostgreSQL production (SQLite auto-indexes FKs differently).  
**File**: `models.py` — all `Field(foreign_key=...)` declarations

**Fix**: Add `index=True` to:
- `Node.faction_id`
- `EpochAction.epoch_id`, `EpochAction.player_id`, `EpochAction.target_node_id`
- `Accord.faction_a_id`, `Accord.faction_b_id`
- `Sentinel.player_id`
- `SentinelPolicy.sentinel_id`
- `SentinelLog.sentinel_id`, `SentinelLog.epoch_id`
- `Notification.player_id`
- `NewsItem.epoch_id`
- `Player.faction_id`

```python
# Example
faction_id: Optional[int] = Field(default=None, foreign_key="faction.id", index=True)
```

**Estimated LOC**: ~15 field modifications  
**Tests**: Schema migration test + EXPLAIN ANALYZE on key queries

---

### DEBT-004: Win Condition + Server-Side XP 🟡 P1

**Impact**: No actual game end detection or XP awards — players never progress.  
**File**: `engine.py` — add to `process_resolution_phase`

**Fix**: After economy update, check if any faction has `global_influence_pct >= 75`.
If so, trigger a win condition:
```python
# Pseudocode - add after economy update section
for faction in all_factions.values():
    if faction.global_influence_pct >= 75.0:
        # Award XP to all players of the winning faction
        winners = session.exec(select(Player).where(Player.faction_id == faction.id)).all()
        for p in winners:
            xp_gain = 100 + (p.stats['nodes_captured'] * 8)  # base + capture bonus
            p.xp += xp_gain
            p.wins += 1
            p.win_streak += 1
            p.best_streak = max(p.best_streak, p.win_streak)
            p.rank = calculate_rank(p.xp)
            session.add(p)
        # Award loss XP to others
        losers = session.exec(select(Player).where(Player.faction_id != faction.id)).all()
        for p in losers:
            p.xp += 50  # loss base
            p.losses += 1
            p.win_streak = 0
            p.rank = calculate_rank(p.xp)
            session.add(p)
        # Reset game state or start new match
```

**Estimated LOC**: ~40 lines  
**Tests**: New test class `TestWinCondition` in `test_engine.py`

---

## Phase 2: Input Validation & Security Hardening

### SEC-006: Username & Password Validation 🟡 P1

**Impact**: Usernames can be empty strings, 1-char, or contain SQL injection payloads.
Passwords have no length/complexity requirements.  
**File**: `models.py` + `main.py` registration endpoint

**Fix**:
```python
class PlayerCreate(SQLModel):
    username: str = Field(min_length=3, max_length=32, regex=r'^[a-zA-Z0-9_]+$')
    password: str = Field(min_length=8, max_length=128)

# In register endpoint, additionally enforce:
# - At least 1 uppercase, 1 lowercase, 1 digit
# - No common passwords (optional)
```

**Estimated LOC**: ~10 lines  
**Tests**: Add `test_register_short_username`, `test_register_weak_password`,
`test_register_invalid_chars`

---

### SEC-007: Treaty Type Enum Validation 🟡 P1

**Impact**: `TreatyProposal.type` is a free-form string — clients can send `"DROP_TABLE"`.  
**File**: `main.py:269`

**Fix**:
```python
class TreatyType(str, enum.Enum):
    CEASEFIRE = "CEASEFIRE"
    ALLIANCE = "ALLIANCE"
    TRADE = "TRADE"

class TreatyProposal(BaseModel):
    target_faction_id: int
    type: TreatyType  # Enforced by Pydantic
    proposal_text: str = Field(max_length=500)
```

**Estimated LOC**: ~8 lines  
**Tests**: Add `test_propose_invalid_type` expecting 422

---

### SEC-008: CORS Method/Header Restriction 🟢 P2

**Impact**: `allow_methods=["*"]` allows OPTIONS, PATCH, DELETE etc. to all endpoints.  
**File**: `main.py:57–58`

**Fix**:
```python
allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
allow_headers=["Authorization", "Content-Type"],
```

**Estimated LOC**: 2 lines

---

### SEC-009: JWT HttpOnly Cookie Migration 🟢 P2

**Impact**: XSS attack steals JWT from localStorage.  
**Files**: `auth.py`, `main.py`, `api-client.js`

**Fix**: Return JWT as `Set-Cookie: nh_session=JWT; HttpOnly; Secure; SameSite=Strict`
instead of JSON body. Frontend reads from cookie automatically via `credentials: 'include'`.

**Estimated LOC**: ~30 lines backend + 20 lines frontend  
**Tests**: Auth tests need cookie-based assertions  
**Risk**: Breaking change — needs frontend migration path

---

## Phase 3: Usability Improvements

### UX-001: Defend Button Missing from Action Panel 🔴 P0

**Impact**: Players can BREACH and SCAN from the UI panel but **cannot DEFEND** their own
nodes. The only defense mechanism is Sentinels or the terminal CLI.  
**File**: `ui-manager.js:61–64`

**Fix**: Add a DEFEND button next to BREACH/SCAN. Show it when the selected node belongs to
the player's faction (instead of hiding the action panel entirely):
```javascript
// When node.faction_id === playerFactionId:
actionPanel.style.display = 'block';
btnBreach.style.display = 'none';  // Can't breach own node
btnDefend.style.display = 'block'; // Show DEFEND
btnScan.style.display = 'block';   // SCAN still useful

// When node.faction_id !== playerFactionId:
btnBreach.style.display = 'block';
btnDefend.style.display = 'none';
btnScan.style.display = 'block';
```

**Estimated LOC**: ~20 lines  
**Tests**: Manual UI verification

---

### UX-002: Faction Economy Display in HUD 🟡 P1

**Impact**: Players have no visibility into their faction's CU reserves or income rate.
They must use the terminal CLI `/status` or guess.  
**File**: `ui-manager.js` HUD template

**Fix**: Add a CU readout below the epoch/phase line:
```html
<span id="hud-cu">CU: -- / +-- per epoch</span>
```
Fetch from `/api/faction/{id}/economy` on each `gameStateUpdate`.

**Estimated LOC**: ~15 lines  
**Tests**: Verify via `fetchWorldState()` integration

---

### UX-003: Player Faction Dynamic Detection 🟡 P1

**Impact**: The HUD hardcodes Faction 1 as "player" (`ui-manager.js:197,203`). Multi-player
games show wrong stats. Info panel hardcodes faction names (`ui-manager.js:228–232`).  
**File**: `ui-manager.js`, `game-engine.js`

**Fix**: Fetch player profile on login and store `playerFactionId`. Use this throughout:
```javascript
// In game-engine.js init():
const profile = await api.getProfile();
this.playerFactionId = profile?.faction_id || null;

// In updateHUD():
const playerCount = nodes.filter(n => n.faction_id === this.playerFactionId).length;
```

Also load faction names from `/api/faction/{id}` instead of hardcoding.

**Estimated LOC**: ~25 lines  
**Tests**: Manual multi-faction login test

---

### UX-004: Node Up/Down Keyboard Navigation 🟡 P1

**Impact**: After an attack, players must click a tiny globe dot to select the next node.
No keyboard cycling support (planned in conversation `964b2439`).  
**File**: `game-engine.js`

**Fix**: On `ArrowUp`/`ArrowDown`, cycle through `this.nodes` array and dispatch
`nodeSelected` event. Focus globe camera on the new selection.

**Estimated LOC**: ~30 lines  
**Tests**: Keyboard event test in `game-engine.test.js`

---

### UX-005: CU Slider Max Linked to Faction Reserves 🟢 P2

**Impact**: The CU slider (`ui-manager.js:67`) has a hardcoded max of 100. If the faction has
5000 CU, the max action is capped at 100. If it has 10 CU, the slider allows overcommit.  
**File**: `ui-manager.js:67`

**Fix**: Update slider max dynamically based on current faction reserves:
```javascript
const cuSlider = document.getElementById('input-cu');
cuSlider.max = Math.min(factionReserves, 1000); // Cap at 1000 to prevent UI overflow
cuSlider.value = Math.min(cuSlider.value, cuSlider.max);
```

**Estimated LOC**: ~5 lines

---

### UX-006: Epoch Timer Shows Countdown 🟢 P2

**Impact**: The timer shows `00:00` because `currentEpochEnd` is `ended_at` (null for active
epochs). Should use `started_at + phase_duration`.  
**File**: `ui-manager.js:169–188, 217`

**Fix**: Calculate expected end time from `epoch.started_at + elapsed + remaining`.
Or have the backend API return `phase_ends_at` in the epoch response.

**Estimated LOC**: ~10 lines backend + 5 frontend

---

### UX-007: maxFirewall Not Mapped from API 🟢 P2

**Impact**: In `game-engine.js:147`, `maxFirewall` is set to `n.defense_level` (current)
instead of `n.max_defense` (structural cap). The firewall bar always shows 100%.  

**Fix**:
```javascript
maxFirewall: n.max_defense || n.defense_level,
```

**Estimated LOC**: 1 line

---

### UX-008: Toast Notifications Need Severity Colors 🟢 P2

**Impact**: `showToast()` only checks `capture` and `lost` types. `warning`, `error`, `info`,
`success` all show the default accent color.  
**File**: `ui-manager.js:283–286`

**Fix**: Extend the color map:
```javascript
if (type === 'capture' || type === 'success') borderColor = 'var(--color-player)';
if (type === 'lost' || type === 'error') borderColor = 'var(--color-enemy)';
if (type === 'warning') borderColor = 'var(--color-warning)';
if (type === 'info') borderColor = 'var(--color-accent)';
```

**Estimated LOC**: 4 lines

---

## Phase 4: Accessibility

### ACC-001: Colorblind Mode Toggle 🟡 P1

**Spec**: Toggle for protanopia/deuteranopia-safe palette.  
**File**: `tokens.css`, `renderer.js`, `index.html`

**Fix**: Add CSS custom property overrides via a `[data-colorblind]` attribute:
```css
[data-colorblind="protanopia"] {
  --color-player: #0077BB;
  --color-enemy: #CC6600;
  --color-ally: #EE7733;
  --color-neutral: #BBBBBB;
}
```
Add toggle button in the HUD settings area.

**Estimated LOC**: ~40 lines (CSS + JS toggle handler)  
**Tests**: Visual regression test with Chromium `--force-color-profile` flag

---

### ACC-002: Shape Coding for Nodes 🟡 P1

**Spec**: ● = player, ▲ = enemy, ■ = neutral  
**File**: `renderer.js` (Globe.gl `pointsMerge` or custom HTML labels)

**Fix**: In 3D mode, use custom Three.js geometries or SVG markers per faction type.
In 2D fallback, use Unicode shape characters.

**Estimated LOC**: ~50 lines  
**Tests**: Visual verification + screenshot diff

---

### ACC-003: Keyboard Navigation & ARIA 🟢 P2

**Spec**: Full keyboard navigation on 2D canvas + ARIA roles  
**File**: `renderer.js` 2D fallback

**Fix**: Add `tabindex` to canvas elements, `role="application"`, and
`aria-label` on nodes. Handle `Tab`, `Enter`, and `Escape` keys.

**Estimated LOC**: ~30 lines  
**Tests**: Screen reader manual test + `axe-core` audit

---

## Phase 5: Architecture & Code Quality

### ARCH-001: Split main.py into FastAPI Routers 🟢 P2

**Impact**: `main.py` is 530 lines with all routes in one file.  
**File**: `main.py` → `routers/auth.py`, `routers/game.py`, `routers/diplomacy.py`,
`routers/sentinels.py`, `routers/admin.py`

**Fix**: Use `APIRouter` and `app.include_router()`:
```python
# routers/auth.py
router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register")
def register_user(...): ...

# main.py
from routers import auth, game, diplomacy, sentinels
app.include_router(auth.router)
```

**Estimated LOC**: ~100 lines refactoring (no logic change)  
**Tests**: All existing tests should pass without modification

---

### ARCH-002: Database Migration Strategy (Alembic) 🟢 P2

**Impact**: `SQLModel.metadata.create_all()` doesn't handle schema changes.
Adding `max_defense` to Node required manual DB recreation.

**Fix**: Initialize Alembic + auto-generate migrations:
```bash
alembic init alembic
alembic revision --autogenerate -m "Add max_defense to Node"
alembic upgrade head
```

**Estimated LOC**: ~20 lines config + migration scripts  
**Tests**: Test `alembic upgrade` + `alembic downgrade` cycle

---

### ARCH-003: Token Expiry Too Short 🟢 P2

**Impact**: `auth.py:35` default token expiry is **15 minutes** (but
`ACCESS_TOKEN_EXPIRE_MINUTES = 60*24*7` is declared but never used). Players get
logged out mid-game.

**Fix**:
```python
# auth.py:30 — use the declared constant
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
```

**Estimated LOC**: 1 line fix  
**Tests**: Existing token tests + verify `exp` claim matches 7-day window

---

## Implementation Priority

| Priority | Phase | Items | Est. LOC |
|----------|-------|-------|----------|
| 🔴 P0 | 1+3 | DEBT-001, DEBT-002, UX-001 | ~35 |
| 🟡 P1 | 1–4 | DEBT-003, DEBT-004, SEC-006, SEC-007, UX-002, UX-003, UX-004, ACC-001, ACC-002 | ~260 |
| 🟢 P2 | 2–5 | SEC-008, SEC-009, UX-005–008, ACC-003, ARCH-001–003 | ~300 |

**Recommended Sprint Plan**:
1. **Sprint 1** (1 day): P0 items — deprecation fixes + DEFEND button
2. **Sprint 2** (2 days): P1 security + usability — input validation, win condition, economy HUD
3. **Sprint 3** (2 days): P1 accessibility — colorblind mode + shape coding
4. **Sprint 4** (1 day): P2 polish — CORS, router split, token fix, toast colors, slider max

---

> **Total Estimated Effort**: ~595 LOC across ~30 files over 6 dev-days.  
> **Risk**: SEC-009 (HttpOnly cookies) is a breaking change and should be gated behind a feature flag.
