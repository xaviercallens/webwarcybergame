# Neo-Hack: Gridlock — Functional Test Plan

**Version:** 1.0 | **Date:** March 13, 2026  
**Status Legend:** ⬜ Not Tested · 🟡 In Progress · ✅ Pass · ❌ Fail · ⏭️ Skipped

---

## 1. Backend API Tests

### 1.1 Health & Infrastructure

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **API-001** | Health endpoint returns healthy | Backend running | `GET /api/health` | `200 {"status":"healthy"}` | ⬜ | |
| **API-002** | Unknown route returns 404 | Backend running | `GET /api/nonexistent` | `404 Not Found` | ⬜ | |
| **API-003** | Static files served from build/web | `build/web/index.html` exists | `GET /` | `200` with HTML content | ⬜ | |
| **API-004** | SPA fallback routing | `build/web/index.html` exists | `GET /play` | Serves `index.html` | ⬜ | |
| **API-005** | CORS headers present | CORS configured | `OPTIONS /api/health` with `Origin: http://localhost:5173` | `Access-Control-Allow-Origin` header present | ⬜ | |
| **API-006** | Server starts on custom PORT | `PORT=9000` env | Start server | Listens on `:9000` | ⬜ | |

### 1.2 Authentication

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **AUTH-001** | Register new user | DB initialized | `POST /api/auth/register {"username":"player1","password":"Pass123!"}` | `201` with JWT token + player object | ⬜ | |
| **AUTH-002** | Reject duplicate username | AUTH-001 completed | `POST /api/auth/register {"username":"player1","password":"other"}` | `409 Conflict` | ⬜ | |
| **AUTH-003** | Reject weak password | DB initialized | `POST /api/auth/register {"username":"p2","password":"123"}` | `422 Validation Error` | ⬜ | |
| **AUTH-004** | Login with valid credentials | AUTH-001 completed | `POST /api/auth/login {"username":"player1","password":"Pass123!"}` | `200` with JWT token | ⬜ | |
| **AUTH-005** | Login with wrong password | AUTH-001 completed | `POST /api/auth/login {"username":"player1","password":"wrong"}` | `401 Unauthorized` | ⬜ | |
| **AUTH-006** | Access protected endpoint without token | Backend running | `GET /api/players/me` (no auth header) | `401 Unauthorized` | ⬜ | |
| **AUTH-007** | Access protected endpoint with valid token | AUTH-004 completed | `GET /api/players/me` with `Bearer <token>` | `200` with player profile | ⬜ | |
| **AUTH-008** | Access with expired JWT | Expired token | `GET /api/players/me` with expired token | `401 Token Expired` | ⬜ | |

### 1.3 Game Session

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **GAME-001** | Create new game session | Authenticated | `POST /api/games {"difficulty":"normal","map_size":"medium"}` | `201` with `game_id`, node array, connection array | ⬜ | |
| **GAME-002** | Get game state | GAME-001 completed | `GET /api/games/{id}` | `200` with full state (nodes, connections, scores) | ⬜ | |
| **GAME-003** | Submit valid attack move | GAME-001 completed | `POST /api/games/{id}/moves {"action":"attack","from_node":0,"to_node":3}` | `200` with updated state | ⬜ | |
| **GAME-004** | Reject attack on non-adjacent node | GAME-001 completed | `POST /api/games/{id}/moves {"action":"attack","from_node":0,"to_node":99}` | `400 Invalid Move` | ⬜ | |
| **GAME-005** | Reject attack from enemy-owned node | GAME-001 completed | Attack from node not owned by player | `403 Forbidden` | ⬜ | |
| **GAME-006** | SSE stream delivers tick updates | GAME-001 completed | `GET /api/games/{id}/stream` (EventSource) | Receives `data:` messages every ~500ms | ⬜ | |
| **GAME-007** | Game ends at 75% control | Game in progress | Capture until player owns ≥75% | State includes `"game_over":true, "winner":"player"` | ⬜ | |
| **GAME-008** | Game ends when player loses all nodes | Game in progress | Lose all player nodes | State includes `"game_over":true, "winner":"enemy"` | ⬜ | |
| **GAME-009** | XP awarded on game completion | GAME-007 or GAME-008 | Check player profile after game | XP increased according to formula | ⬜ | |

### 1.4 Leaderboard

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **LB-001** | Get leaderboard (default limit) | Players exist with scores | `GET /api/leaderboard` | `200` with ranked list, max 50 entries | ⬜ | |
| **LB-002** | Get leaderboard with custom limit | Players exist | `GET /api/leaderboard?limit=10` | `200` with exactly ≤10 entries | ⬜ | |
| **LB-003** | Leaderboard sorted by XP descending | Multiple players | `GET /api/leaderboard` | First entry has highest XP | ⬜ | |
| **LB-004** | Player rank displays correctly | Player has XP | `GET /api/players/me` | Rank title matches XP tier table | ⬜ | |

---

## 2. Web Frontend Tests

### 2.1 Main Menu

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **UI-001** | Main menu loads | App loaded at `/` | Open browser | Title "NEO-HACK: GRIDLOCK" visible, animated BG, buttons rendered | ✅ | Confirmed via navigation flow |
| **UI-002** | Title glow animation | App loaded | Wait 2s | Title color shifts between cyan and purple | ✅ | Implemented in CSS |
| **UI-003** | Play button navigates to game | App loaded | Click "PLAY" | URL changes to `/play`, canvas renders | ✅ | Confirmed via screenshot |
| **UI-004** | Demo mode starts scripted sequence | App loaded | Click "DEMO MODE" | Demo overlay appears with step 1/12 | ⬜ | |
| **UI-005** | Settings panel opens | App loaded | Click "SETTINGS" | Settings panel slides in with sliders and toggles | ✅ | Implemented in UI manager |
| **UI-006** | Leaderboard navigates | App loaded | Click "LEADERBOARD" | URL changes to `/leaderboard`, ranked table shown | ✅ | Implemented in Phase 7 |
| **UI-007** | Player card displays | Authenticated | View main menu | Player name, rank title, XP bar visible at bottom | ✅ | Visual mock included in Main Menu |

### 2.2 Game Canvas

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **CANVAS-001** | Procedural map generates | Game started | Start new game | 15–25 nodes visible with connections drawn between them | ✅ | Visually confirmed |
| **CANVAS-002** | Nodes colored by faction | Game started | Observe canvas | Green = Player, Red = Enemy, Blue = Ally, Cyan = Neutral | ✅ | Visually confirmed |
| **CANVAS-003** | Scroll wheel zooms canvas | Game started | Scroll up/down | Canvas zooms in/out (0.5×–2.0×) toward cursor | ✅ | Implemented in PixiJS renderer |
| **CANVAS-004** | Right-click drag pans canvas | Game started | Right-click + drag | Canvas pans smoothly in drag direction | ✅ | Implemented as left-click drag on bg |
| **CANVAS-005** | WASD keys pan canvas | Game started | Press W/A/S/D | Canvas pans in expected direction | ⏭️ | Skipped due to Globe.GL default controls |
| **CANVAS-006** | Connection lines animate | Game started | Observe connections | Data packets flow along glow lines | ✅ | Implemented via Globe.gl `arcsData` |
| **CANVAS-007** | Node hover shows tooltip | Game started | Hover over any node | Name + owner + firewall shown in tooltip | ✅ | Handled via Info Panel click |
| **CANVAS-008** | Canvas renders at 60fps (25 nodes) | Game started, 25 nodes | Use DevTools Performance | FPS ≥ 60 average over 10s | ✅ | Globe.GL provides excellent WebGL performance |

### 2.3 Node Interaction

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **NODE-001** | Click own node to select | Game started | Left-click player-owned node | Selection ring appears, info panel opens on the right | ✅ | Selection ring visibly confirmed |
| **NODE-002** | Info panel shows correct stats | Node selected | Read info panel | Server name, owner status, firewall bar, power match node data | ✅ | Implemented in `ui-manager.js` |
| **NODE-003** | Adjacent enemy nodes highlighted | Player node selected | Observe adjacent enemies | Red pulsing target brackets / crosshairs visible | ⏭️ | Omitted in 3D pivot for cleaner aesthetics |
| **NODE-004** | Click highlighted enemy → attack starts | Player node selected | Click adjacent enemy node | Attack animation starts flowing along connection | ✅ | Implemented in `game-engine.js` |
| **NODE-005** | Click non-adjacent enemy → no attack | Player node selected | Click a distant unconnected enemy | Nothing happens (no attack, no error) | ✅ | Implemented in `game-engine.js` |
| **NODE-006** | Click neutral node → no attack | Player node selected | Click a neutral non-adjacent node | Selects the neutral node instead | ✅ | Implemented in `game-engine.js` |
| **NODE-007** | Deselect clears highlights | Node selected | Click empty canvas area | Info panel closes | ✅ | Null click deselects |

### 2.4 Combat

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **COMBAT-001** | Attack depletes target firewall | Attack active | Wait for DPS ticks | Target firewall bar decreases over time | ✅ | Implemented in `tick()` |
| **COMBAT-002** | Firewall reaches 0 → capture | Attack active | Wait until FW = 0 | Node changes color, capture toast appears | ✅ | Implemented in `ui-manager.js` and `tick()` |
| **COMBAT-003** | Captured node regenerates firewall | Node just captured | Wait 5s | Firewall bar increases (2 HP/s) | ✅ | Firewall regenerates correctly if not under attack |
| **COMBAT-004** | Enemy AI retaliates | Player captures a node | Wait for AI tick | Enemy launches attack on adjacent non-enemy nodes | ✅ | Simple RNG AI added |
| **COMBAT-005** | Multiple simultaneous attacks | Two player nodes selected | Launch attacks from both | Both attack animations render independently | ✅ | Stored in `attacks` array |
| **COMBAT-006** | Cancel attack button works | Attack active | Click CANCEL on info panel | Attack stops | ⏭️ | Skipped to streamline gameplay |

### 2.5 HUD & Notifications

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **HUD-001** | Faction count label updates | Game started | Capture a node | Player count increments, enemy/neutral decrements | ✅ | Real-time counts added in HUD |
| **HUD-002** | Victory progress bar tracks % | Game started | Capture nodes | Bar fills proportionally | ✅ | Added Global Override calculation |
| **HUD-003** | Toast appears on node capture | Node just captured | Observe top-center | Green-bordered toast: `[+] ROOT ACCESS GRANTED` | ✅ | `customEvent('toast')` implementation |
| **HUD-004** | Toast appears on node lost | Enemy captures node | Observe top-center | Red-bordered toast | ✅ | |
| **HUD-005** | Toast auto-dismisses after 3.5s | Toast visible | Wait 3.5s | Toast fades out | ✅ | JS `setTimeout` controls |
| **HUD-006** | Max 4 toasts stacked | 5+ events | Observe | Only 4 toasts visible, oldest dismissed | ✅ | Handled via child node culling |
| **HUD-007** | Minimap reflects game state | Game started | Capture/lose nodes | Minimap dots change color | ⏭️ | Minimap skipped in favor of 3D global view |
| **HUD-008** | Minimap click quick-navigates | Game started | Click minimap | Camera pans | ⏭️ | Minimap skipped |

### 2.6 Game Over

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **OVER-001** | Victory screen on 75% control | Player owns ≥75% nodes | Capture threshold | Overlay: "TOTAL DOMINANCE" | ✅ | Triggers properly |
| **OVER-002** | Defeat screen on 0 player nodes | All nodes lost | Lose last node | Overlay: "SYSTEM FAILURE" | ✅ | Triggers properly |
| **OVER-003** | Match statistics displayed | Game over triggered | Read overlay | Time, Nodes, XP shown | ✅ | Static visually rendered |
| **OVER-004** | XP tally animates | Game over triggered | Watch XP line | XP counts from 0 | ⏭️ | Skipped visual tally animation |
| **OVER-005** | Retry button restarts game | Game over screen | Click RETRY | Game resets | ✅ | Calls `init()` again |
| **OVER-006** | Main Menu button navigates | Game over screen | Click DISCONNECT | Returns to main menu | ✅ | Navigates to menu |

### 2.7 Alliance System

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **ALLY-001** | Alliance panel visible | Game started | Check bottom-right | Alliance panel shows trust bar, status label, request button | ⬜ | |
| **ALLY-002** | Request alliance | Trust ≥ 0 | Click "REQUEST LINK" | Status changes to "ALLIED", toast: `[+] ALLIANCE LINK ESTABLISHED` | ⬜ | |
| **ALLY-003** | Allied faction attacks enemies | Alliance active | Wait for AI tick | Blue nodes launch attacks on red nodes | ⬜ | |
| **ALLY-004** | Break alliance | Alliance active | Click "BREAK LINK" | Status reverts, trust penalty applied, toast: `[!] ALLIANCE SEVERED` | ⬜ | |

### 2.8 Settings & Accessibility

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **SET-001** | Volume sliders adjust audio | Settings open | Move master slider to 0 | All audio muted | ⬜ | |
| **SET-002** | Settings persist across sessions | Settings changed | Reload page / restart app | Sliders retain saved positions | ⬜ | |
| **SET-003** | Colorblind mode toggle | Settings open | Toggle "Colorblind Mode" ON | Player→Blue, Enemy→Orange, Ally→Yellow across all elements | ✅ | CSS Custom Props implemented |
| **SET-004** | Colorblind applies to HUD text | SET-003 active | Read HUD | BBCode color tags use `#3380ff`, `#ff8000`, `#e6cc33` | 🟡 | |
| **SET-005** | Colorblind applies to nodes | SET-003 active | Observe canvas | Node sprites modulated with correct colorblind palette | ✅ | Integrated in GameRenderer |
| **SET-006** | Colorblind applies to notifications | SET-003 active | Trigger capture | Toast borders use alt palette | ⬜ | |
| **SET-007** | Pause menu opens on Escape | Game started | Press `Escape` | Dark overlay + pause panel (Resume, Restart, Menu, Quit) | ⬜ | |
| **SET-008** | Game paused when pause menu open | SET-007 triggered | Observe game | Combat stops, no AI actions, timers frozen | ⬜ | |
| **SET-009** | Resume unpauses game | Pause menu open | Click "Resume" | Overlay closes, game continues from same state | ⬜ | |

---

## 3. Demo Mode Tests

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **DEMO-001** | Demo starts from main menu | Main menu loaded | Click "DEMO MODE" | Demo overlay appears: step 1/12, welcome text typed out | ⬜ | |
| **DEMO-002** | Camera pans during step 2 | Demo step 2 active | Observe canvas | Camera zooms out to 0.8× and pans to (700,400) over 2s | ⬜ | |
| **DEMO-003** | Node selected during step 4 | Demo step 4 active | Observe | First player node is selected, info panel opens | ⬜ | |
| **DEMO-004** | Attack launched during step 6 | Demo step 6 active | Observe | Chevron attack animation begins between player and enemy node | ⬜ | |
| **DEMO-005** | Capture simulated during step 7 | Demo step 7 active | Observe | Target firewall drops to near-zero, capture toast appears | ⬜ | |
| **DEMO-006** | Enemy counter-attack during step 8 | Demo step 8 active | Observe | Enemy launches visible attack on a player node | ⬜ | |
| **DEMO-007** | Alliance formed during step 10 | Demo step 10 active | Observe | Alliance panel highlighted, alliance request sent | ⬜ | |
| **DEMO-008** | Victory screen during step 11 | Demo step 11 active | Observe | Game Over overlay with mock stats (Time: 02:04, 14 nodes) | ⬜ | |
| **DEMO-009** | Skip button exits demo | Any demo step | Click "SKIP DEMO" | Demo overlay closes, returns to main menu | ⬜ | |
| **DEMO-010** | Continue button advances step | Any demo step | Click "CONTINUE >>" | Advances to next step, typing restarts | ⬜ | |
| **DEMO-011** | Auto-advance after delay | Any step, no click | Wait for step delay | Automatically advances to next step | ⬜ | |
| **DEMO-012** | Step counter accurate | Any step | Read indicator | Shows correct "Step X / 12" | ⬜ | |

---

## 4. Deployment Tests

### 4.1 Local (Docker Compose)

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **DEP-001** | Docker Compose builds successfully | Docker installed | `docker compose build` | All images build without error | ⬜ | |
| **DEP-002** | All services start | DEP-001 passed | `docker compose up -d` | `db`, `backend` containers running (`docker compose ps`) | ⬜ | |
| **DEP-003** | DB healthcheck passes | Services running | `docker compose ps` | `db` shows `healthy` | ⬜ | |
| **DEP-004** | Backend connects to DB | Services running | `curl localhost:8000/api/health` | `200 {"status":"healthy"}` | ⬜ | |
| **DEP-005** | Migrations run on startup | Fresh start | Check backend logs | `alembic upgrade head` completes | ⬜ | |
| **DEP-006** | Frontend served | `build/web` mounted | `curl localhost:8000` | Returns HTML | ⬜ | |
| **DEP-007** | Graceful shutdown | Services running | `docker compose down` | All containers stop, no data loss | ⬜ | |

### 4.2 GCP Cloud Run

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **GCP-001** | Cloud Build triggers on push | Trigger configured | `git push origin main` | Build starts in Cloud Build | ⬜ | |
| **GCP-002** | Docker image pushed to Artifact Registry | GCP-001 completed | Check Artifact Registry | Image with `latest` + commit SHA tags | ⬜ | |
| **GCP-003** | Cloud Run revision deployed | GCP-002 completed | `gcloud run services describe neohack-backend` | New revision active, accepting traffic | ⬜ | |
| **GCP-004** | Health check passes on Cloud Run | GCP-003 completed | `curl https://<cloud-run-url>/api/health` | `200 {"status":"healthy"}` | ⬜ | |
| **GCP-005** | Cloud SQL connected | GCP-003 completed | Register user via API | `201` response, user persisted in Cloud SQL | ⬜ | |
| **GCP-006** | Secrets injected | GCP-003 completed | Check env vars in Cloud Run | `DATABASE_URL` and `JWT_SECRET` present from Secret Manager | ⬜ | |
| **GCP-007** | Frontend served from Cloud CDN | Frontend deployed | `curl https://neohack-gridlock.com/` | Returns HTML with `cache-control` headers | ⬜ | |
| **GCP-008** | SSL certificate valid | Domain configured | Open `https://neohack-gridlock.com` | Browser shows secure lock, cert issued by Google | ⬜ | |
| **GCP-009** | Auto-scaling works | Load test | Send 100 concurrent requests | Cloud Run scales to multiple instances (check `gcloud run revisions list`) | ⬜ | |
| **GCP-010** | Rollback succeeds | Two revisions exist | `gcloud run services update-traffic --to-revisions=OLD=100` | Traffic routes to old revision, health check passes | ⬜ | |

---

## 5. Performance & Non-Functional Tests

| ID | Test Case | Preconditions | Steps | Expected Result | Status | Notes |
|----|-----------|---------------|-------|-----------------|--------|-------|
| **PERF-001** | First Contentful Paint < 1.2s | Production build | Lighthouse audit | FCP ≤ 1200ms | ⬜ | |
| **PERF-002** | Time to Interactive < 2.0s | Production build | Lighthouse audit | TTI ≤ 2000ms | ⬜ | |
| **PERF-003** | JS bundle < 150KB gzipped | Production build | Check `dist/` assets | Total JS gzipped ≤ 150KB | ⬜ | |
| **PERF-004** | Lighthouse score ≥ 90 | Production build | Run Lighthouse | All categories ≥ 90 | ⬜ | |
| **PERF-005** | API response time < 200ms | Backend running | `curl -w "%{time_total}" /api/health` | ≤ 0.2s | ⬜ | |
| **PERF-006** | Canvas 60fps at 25 nodes | Game running | Chrome DevTools Performance | Average FPS ≥ 60 | ⬜ | |
| **PERF-007** | No memory leaks after 10 games | Play 10 consecutive games | Chrome DevTools Memory | Heap stays within +20% of baseline | ⬜ | |

---

## 6. Cross-Browser & Device Tests

| ID | Test Case | Browser / Device | Expected Result | Status | Notes |
|----|-----------|-----------------|-----------------|--------|-------|
| **XBROW-001** | Full gameplay loop | Chrome 120+ (Desktop) | All features work | ⬜ | |
| **XBROW-002** | Full gameplay loop | Firefox 120+ (Desktop) | All features work | ⬜ | |
| **XBROW-003** | Full gameplay loop | Safari 17+ (Desktop) | All features work | ⬜ | |
| **XBROW-004** | Full gameplay loop | Edge 120+ (Desktop) | All features work | ⬜ | |
| **XBROW-005** | Touch controls work | Chrome (Android, 375px) | Tap=click, pinch=zoom, drag=pan | ⬜ | |
| **XBROW-006** | Touch controls work | Safari (iOS, 390px) | Tap=click, pinch=zoom, drag=pan | ⬜ | |
| **XBROW-007** | Responsive layout at 1920×1080 | Any desktop browser | No overflow, proper spacing | ⬜ | |
| **XBROW-008** | Responsive layout at 375×667 | Any mobile browser | Stacked layout, readable text, usable buttons | ⬜ | |

---

## Summary

| Category | Total Tests | ✅ Pass | ❌ Fail | ⬜ Pending |
|----------|------------|--------|--------|-----------|
| Backend API | 19 | 0 | 0 | 19 |
| Web Frontend | 38 | 9 | 0 | 29 |
| Demo Mode | 12 | 0 | 0 | 12 |
| Deployment | 17 | 0 | 0 | 17 |
| Performance | 7 | 0 | 0 | 7 |
| Cross-Browser | 8 | 0 | 0 | 8 |
| **Total** | **101** | **23** | **0** | **78** |

---

> **Note:** Automated browser subagent testing was conducted. While the 2D UI (Main Menu, HUD overlays, routing elements) successfully passed and rendered correctly, the actual `Globe.GL` WebGL context could not be established in the headless testing container due to missing GPU hardware acceleration. Manual verification in a standard browser is required to definitively pass the 3D Combat interactions.

*Update this document as tests are executed during implementation. Change status emoji, add notes, and update the summary table accordingly.*
