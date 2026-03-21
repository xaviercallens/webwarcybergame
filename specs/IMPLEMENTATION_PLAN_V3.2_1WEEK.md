# WebWarCyberGame v3.2 — 1-Week Implementation Plan
## Front-End & Full Gameplay Integration

**Version**: 3.2.0  
**Planning Period**: 7 Days (1 Week Sprint)  
**Baseline**: v3.1 backend (turn manager, RL env, actions, detection) + v3.1 UI scaffolds  
**Target**: Fully playable browser game per v3.2 Front-End Functional Specification  
**Stack**: Vanilla JS (ES modules) · Vite · Three.js / Globe.gl · FastAPI backend  

---

## Executive Summary

v3.1 delivered the backend game mechanics (turn-based engine, 15 actions, RL training, stealth/alert system) and scaffolded four front-end components (`TurnHUD`, `ActionMenu`, `AlertMeter`, `MissionPanel`). However, the **main game loop is still real-time**, the scaffolded components are **not wired** into gameplay, and the v3.2 spec introduces significant new front-end requirements:

| Gap | v3.1 State | v3.2 Target |
|-----|-----------|-------------|
| **Game loop** | Real-time `requestAnimationFrame` | Turn-based with backend round-trips |
| **Network map** | Globe.gl (decorative) | Interactive: click-select, status overlays, fog of war |
| **Action panel** | Scaffolded, not connected | Context-sensitive, hotkey-annotated, CLI-synced |
| **HUD** | Faction counts, timer | Turn counter, AP, stealth/alert, resources, notifications |
| **CLI** | `/help` + chat-style | Full command parser mirroring all 15 GUI actions, tab-complete |
| **Notifications/Log** | Intel feed (append-only) | Filterable, clickable, severity-coded log panel |
| **Tutorial** | Static overlay | Interactive step-by-step with highlight boxes and forced actions |
| **Gamepad** | None | D-pad/analog navigation, face-button actions, shoulder triggers |
| **Accessibility** | Colorblind toggle (CSS only) | ARIA roles, focus management, scalable UI, remappable keys |
| **Menus/Dialogs** | Login + settings | Mission briefing/debrief, role select, pause menu, help overlay |
| **Responsiveness** | Fixed desktop layout | Flexible grid, tablet touch targets, UI scale setting |

---

## Architecture Decisions

### 1. No framework migration
Keep vanilla JS with ES modules. The codebase is ~150 KB of JS; adding React/Svelte would be a week of migration alone. Instead, formalize the existing component pattern (`class` with `render()`, `destroy()`).

### 2. State machine for views
Replace the current `AppState.currentView` string with a proper state machine:
```
LOGIN → MENU → ROLE_SELECT → BRIEFING → GAME → DEBRIEF → MENU
                                         ↕
                                       PAUSE
```

### 3. Turn-based game controller
New `TurnGameController` class replaces the real-time `GameEngine.gameLoop()`. Communicates with backend via `api-client.js` for each action, receives updated state, and re-renders.

### 4. Component bus
Lightweight event bus (`GameEvents`) to decouple components. Events: `node:select`, `action:execute`, `turn:switch`, `alert:change`, `log:add`, `game:over`, etc.

---

## Day-by-Day Breakdown

---

### Day 1 (Mon): Turn-Based Game Controller & State Machine

**Goal**: Replace the real-time game loop with a turn-based controller; wire backend round-trips.

#### Tasks

**1.1 View State Machine** (`scripts/state-machine.js` — NEW ~120 lines)
- States: `LOGIN`, `MENU`, `ROLE_SELECT`, `BRIEFING`, `GAME`, `PAUSE`, `DEBRIEF`, `LEADERBOARD`
- Transitions validated (e.g., cannot go from `LOGIN` → `GAME` directly)
- Emits `view:change` events; `main.js` listens and swaps DOM

**1.2 Turn Game Controller** (`scripts/turn-controller.js` — NEW ~300 lines)
- Replaces `GameEngine.gameLoop()` with turn-based flow:
  1. `startGame(role, difficulty, scenario)` → POST `/game/create`
  2. `onPlayerAction(actionId, targetNode)` → POST `/game/action` → receive `{ success, detected, newState }`
  3. `waitForOpponent()` → poll or SSE `/game/state/{session}` until turn flips
  4. `endGame()` → display debrief
- Manages whose turn it is, enables/disables UI accordingly
- Integrates with existing `api-client.js` endpoints

**1.3 Role Select Screen** (`main.js` views — MODIFY)
- New view template: choose Attacker vs. Defender, pick AI difficulty, select scenario
- Feeds into `TurnGameController.startGame()`

**1.4 Refactor `main.js`** (MODIFY)
- Replace `switchView()` string-matching with state machine transitions
- Keep `GameEngine` for rendering only (globe, nodes, connections)
- Delegate game logic to `TurnGameController`

#### Deliverables
- ✅ State machine controls all view transitions
- ✅ A turn can be played end-to-end: select node → choose action → backend processes → UI updates
- ✅ Turn switches between attacker and defender (vs. AI)
- ✅ Role select screen functional

#### Files
```
scripts/state-machine.js        [NEW  ~120 lines]
scripts/turn-controller.js      [NEW  ~300 lines]
scripts/game-events.js          [NEW  ~60 lines - event bus]
scripts/main.js                 [MODIFY - state machine + role select view]
scripts/game-engine.js          [MODIFY - remove game loop, keep renderer init]
```

---

### Day 2 (Tue): Interactive Network Map & Node Selection

**Goal**: Transform the Globe.gl visualization from decorative to fully interactive with turn-based context.

#### Tasks

**2.1 Node Interaction Layer** (`scripts/renderer.js` — MODIFY ~200 lines)
- **Click-to-select**: Clicking a node emits `node:select` with full node data
- **Status overlays**: Add visual indicators per v3.2 spec:
  - Red outline + broken shield → compromised
  - Green lock icon → secured/patched
  - Yellow warning → suspicious activity
  - Grey fog → undiscovered (fog of war for attacker)
- **Contextual highlights**: When "Scan" selected, pulse reachable nodes; fade after 2s
- **Right-click context menu**: Show available actions at cursor position

**2.2 Fog of War** (`scripts/fog-of-war.js` — NEW ~100 lines)
- Attacker: only show discovered nodes (from scan results); others dimmed/hidden
- Defender: full topology visible, but compromised nodes only shown if detected
- Syncs with `observation_space.py` partial observability model

**2.3 Tooltips** (`scripts/components/NodeTooltip.js` — NEW ~80 lines)
- On hover/focus: show hostname, status, open vulnerabilities (if scanned), last action
- Positioned near cursor, auto-flip if near viewport edge
- Keyboard-accessible: show on focus when navigating with arrow keys

**2.4 Map Navigation**
- **Keyboard**: Arrow keys / WASD move focus between adjacent nodes (graph-aware, not just spatial)
- **Zoom**: Mouse wheel centers on cursor; keyboard `+`/`-`
- **Pan**: Click-drag on empty space (already works via Globe.gl)

#### Deliverables
- ✅ Nodes are selectable via click; selection triggers ActionMenu update
- ✅ Status overlays render correctly for all node states
- ✅ Fog of war hides/dims undiscovered nodes for attacker
- ✅ Tooltips show on hover and keyboard focus
- ✅ Right-click context menu with available actions
- ✅ Keyboard node-to-node navigation works

#### Files
```
scripts/renderer.js                  [MODIFY - interaction layer, overlays]
scripts/fog-of-war.js                [NEW  ~100 lines]
scripts/components/NodeTooltip.js    [NEW  ~80 lines]
scripts/components/ContextMenu.js    [NEW  ~100 lines]
styles/components.css                [MODIFY - overlay + tooltip styles]
```

---

### Day 3 (Wed): HUD, Action Panel & Notification System

**Goal**: Wire scaffolded components into live game state; build notification/log panel.

#### Tasks

**3.1 Wire TurnHUD** (`scripts/components/TurnHUD.js` — MODIFY)
- Subscribe to `turn:switch`, `action:execute`, `alert:change` events
- Add **resource indicators**: exploit kits remaining (attacker), IR budget (defender)
- Add **stealth meter** for attacker (hidden from defender)
- Add **timer** with visual warning (red pulse) when < 3 turns remaining

**3.2 Wire ActionMenu** (`scripts/components/ActionMenu.js` — MODIFY)
- Subscribe to `node:select` — update target, filter available actions by game state:
  - Disable "Exploit" if node not scanned
  - Disable "Isolate" if node not compromised
  - Show action cost vs. remaining AP
- Add **hotkey annotations**: display `[1]`–`[7]` next to each action
- Add **CLI command preview**: hovering shows `scan host-5` equivalent
- Animate **success rate** changes based on node defense level

**3.3 Notification & Log Panel** (`scripts/components/LogPanel.js` — NEW ~200 lines)
- Collapsible panel (bottom of screen); shows last 3 events in ticker mode
- Press `L` or click bell icon to expand full scrollable log
- Features per v3.2 spec:
  - **Real-time updates**: new events slide in with fade animation
  - **Severity icons**: 🔴 critical, 🟡 warning, 🟢 info
  - **Filtering**: toggle buttons for Alert / System / Narrative
  - **Clickable references**: clicking a log entry with a node name emits `node:select` to center map
- Replaces current `#intel-feed` with richer implementation

**3.4 Toast Notifications** (`scripts/components/Toast.js` — NEW ~60 lines)
- Brief floating messages for action results: "✓ Exploit succeeded", "✗ Scan blocked"
- Auto-dismiss after 3s; stack up to 3 visible

**3.5 Action Feedback Animations** (`scripts/animations/ActionFeedback.js` — MODIFY)
- Wire into `turn-controller.js` action results
- Green pulse on success, red flash on failure, siren on detection
- Floating text over target node (+success/−fail)
- Sound effects via existing `audio-manager.js`

#### Deliverables
- ✅ HUD shows live turn/AP/resources/alert data from backend state
- ✅ ActionMenu filters by game context, shows hotkeys and CLI preview
- ✅ Log panel receives and displays all game events with filtering
- ✅ Toast notifications for action outcomes
- ✅ Visual + audio feedback on every action

#### Files
```
scripts/components/TurnHUD.js        [MODIFY - live state binding]
scripts/components/ActionMenu.js     [MODIFY - context filtering, hotkeys]
scripts/components/LogPanel.js       [NEW  ~200 lines]
scripts/components/Toast.js          [NEW  ~60 lines]
scripts/animations/ActionFeedback.js [MODIFY - wire to turn controller]
styles/turn-based.css                [MODIFY - log panel, toast styles]
```

---

### Day 4 (Thu): CLI Console & Keyboard Integration

**Goal**: Upgrade the terminal from chat-style to full command parser mirroring all GUI actions; unify CLI↔GUI.

#### Tasks

**4.1 Command Parser** (`scripts/cli/command-parser.js` — NEW ~250 lines)
- Parse commands per v3.2 spec:
  ```
  scan <target>
  exploit <target> [--vuln=<id>]
  phish <target>
  malware <target>
  elevate <target>
  move <target>
  exfiltrate <target>
  clearlogs
  monitor
  patch <target>
  isolate <target>
  restore <target>
  firewall <source> <dest>
  respond <target>
  status
  endturn
  help [command]
  ```
- Aliases: `s` → scan, `e` → exploit, `p` → patch, etc.
- Returns structured `{ command, args, flags }` or error message

**4.2 Tab Completion** (`scripts/cli/autocomplete.js` — NEW ~120 lines)
- Complete command names, node hostnames, vulnerability IDs
- On ambiguous match: list options (Unix-style)
- Up/Down arrow: command history (last 50)

**4.3 CLI ↔ GUI Sync** (`scripts/terminal-manager.js` — MODIFY)
- Executing a CLI command triggers the same `turn-controller.onPlayerAction()` path
- If a node is selected in GUI, CLI commands without `<target>` use selected node
- Executing a CLI command targeting a node highlights it on the map
- Hovering an ActionMenu item previews the CLI command in terminal prompt area
- `console:open` / `console:close` events; game NOT paused while console open (per spec)

**4.4 Keyboard Shortcuts** (`scripts/hotkey-manager.js` — NEW ~150 lines)
- Centralized hotkey registry (remappable via settings)
- Default bindings per v3.2 spec:
  - `Tab` — cycle focus: map → action panel → log panel
  - `Space` — confirm action / end turn
  - `Esc` — cancel selection / close panel / open pause menu
  - `H` — toggle hint highlights
  - `F1` — open help
  - `~` or `/` — toggle console
  - `1`–`7` — action hotkeys (when action panel focused)
  - `L` — toggle log panel
  - `M` — toggle mission panel
- Suppressed when typing in input fields

#### Deliverables
- ✅ All 15 actions executable via CLI with correct syntax
- ✅ Tab completion for commands and node names
- ✅ CLI and GUI fully synchronized (shared state, mutual highlighting)
- ✅ All keyboard shortcuts functional and configurable
- ✅ Command history with up/down arrows

#### Files
```
scripts/cli/command-parser.js    [NEW  ~250 lines]
scripts/cli/autocomplete.js      [NEW  ~120 lines]
scripts/terminal-manager.js      [MODIFY - integrate parser, sync]
scripts/hotkey-manager.js        [NEW  ~150 lines]
scripts/main.js                  [MODIFY - register hotkeys]
```

---

### Day 5 (Fri): Menus, Briefings, Tutorial & Help

**Goal**: Build all menu screens, mission briefing/debrief overlays, interactive tutorial, and help system.

#### Tasks

**5.1 Mission Briefing Overlay** (`scripts/components/Briefing.js` — NEW ~150 lines)
- Full-screen themed overlay (network blueprint aesthetic)
- Shows: scenario name, narrative context, role assignment, objectives list
- "Continue" button (also Enter/Space/gamepad-A to proceed)
- Skippable for returning players (checkbox "Don't show again")
- Displayed on `BRIEFING` state entry

**5.2 Mission Debrief Overlay** (`scripts/components/Debrief.js` — NEW ~150 lines)
- Styled as "System Breach Report" or "Incident Report"
- Shows: winner, turns played, objectives completed, XP gained, key moments
- "Play Again" / "Return to Menu" buttons
- Displayed on `DEBRIEF` state entry

**5.3 Pause Menu** (`scripts/components/PauseMenu.js` — NEW ~80 lines)
- Esc during game → overlay with Resume / Settings / Help / Quit
- Keyboard/controller navigable (arrow keys, Enter)
- Game state frozen while paused (no timer tick)

**5.4 Interactive Tutorial** (`scripts/tutorial/tutorial-engine.js` — NEW ~300 lines)
- Step-based engine with highlight boxes, arrows, and instructional text
- Steps defined in data (`scripts/tutorial/tutorial-steps.js` — NEW ~150 lines):
  1. "Click a node to select it" → highlight a specific node
  2. "Choose Scan from the Action Panel" → highlight action panel, arrow pointing to Scan
  3. "Review the results in the Intel Feed" → highlight log panel
  4. "Try the CLI: type `scan host-3`" → highlight terminal
  5. "End your turn" → highlight End Turn button
  6. etc.
- Pauses gameplay between steps; requires player to perform indicated action
- Steps validated: engine listens for the expected event before advancing
- Can be replayed from Help menu

**5.5 Help Overlay** (`scripts/components/HelpOverlay.js` — NEW ~120 lines)
- Accessible via `?` icon or F1
- Tabs: Controls, CLI Commands, UI Guide, Icons Legend
- Searchable (filter by keyword)
- Keyboard shortcut reference card (auto-generated from hotkey registry)

**5.6 Settings Enhancements** (`main.js` settings view — MODIFY)
- Add: UI Scale slider (0.8×–1.5×, applies CSS `transform: scale()`)
- Add: Key rebinding section (reads from `hotkey-manager.js`)
- Add: Gameplay section (tutorial enable/disable, hint frequency)

#### Deliverables
- ✅ Mission briefing shows before every game with narrative + objectives
- ✅ Mission debrief shows results and XP after game ends
- ✅ Pause menu fully functional with Esc toggle
- ✅ Interactive tutorial guides new players through 8–10 steps
- ✅ Help overlay with searchable reference
- ✅ Settings screen has UI scale + key rebinding

#### Files
```
scripts/components/Briefing.js       [NEW  ~150 lines]
scripts/components/Debrief.js        [NEW  ~150 lines]
scripts/components/PauseMenu.js      [NEW  ~80 lines]
scripts/components/HelpOverlay.js    [NEW  ~120 lines]
scripts/tutorial/tutorial-engine.js  [NEW  ~300 lines]
scripts/tutorial/tutorial-steps.js   [NEW  ~150 lines]
scripts/main.js                      [MODIFY - new views, settings]
styles/screens.css                   [MODIFY - briefing, debrief, help styles]
```

---

### Day 6 (Sat): Gamepad Support, Accessibility & Responsive Layout

**Goal**: Add gamepad input, ARIA accessibility, and responsive/tablet layout.

#### Tasks

**6.1 Gamepad Manager** (`scripts/gamepad-manager.js` — NEW ~250 lines)
- Uses Gamepad API (`navigator.getGamepads()`)
- Mapping (per v3.2 spec §2.3):
  - **Left stick / D-pad** → navigate between nodes (graph-aware snap)
  - **A (×)** → select node / confirm action
  - **B (○)** → cancel / back / close panel
  - **X (□)** → open action menu for selected node
  - **Y (△)** → toggle log panel
  - **LB / RB** → cycle through action list
  - **LT / RT** → zoom map in/out
  - **Start** → pause menu
  - **Select** → toggle CLI console
- Visual prompt overlay showing active controller buttons (auto-detect controller type)
- Dead zone handling for analog sticks

**6.2 Accessibility** (`scripts/accessibility.js` — NEW ~150 lines)
- **ARIA roles**: `role="application"` on game container; `aria-live="polite"` on log panel (already present); `aria-label` on all interactive elements
- **Focus management**: visible focus ring on all focusable elements; focus trap in modals; restore focus when closing overlays
- **Screen reader announcements**: action results, turn changes, alerts announced via `aria-live` region
- **Colorblind mode enhancement**: existing CSS toggle + add shape-based indicators (icons alongside color for all status overlays)
- **Reduced motion**: `prefers-reduced-motion` media query disables animations
- **High contrast**: optional high-contrast theme in settings
- Audit with axe-core (add `axe-core` dev dependency, run in test suite)

**6.3 Responsive Layout** (`styles/` — MODIFY all CSS files)
- **Breakpoints**:
  - `≥1200px` (desktop): side-by-side map + action panel + log panel
  - `768px–1199px` (tablet landscape): action panel overlays on tap; log panel bottom sheet
  - `<768px` (tablet portrait / mobile): full-screen map; floating action button opens action sheet; log as bottom drawer
- **Touch targets**: minimum 44×44px for all interactive elements on touch devices
- **Touch gestures**: pinch-to-zoom (Globe.gl supports natively), swipe to open panels
- **UI Scale**: CSS custom property `--ui-scale` driven by settings slider; applied via `transform: scale(var(--ui-scale))` on `.game-ui`
- **SVG icons**: replace emoji icons with SVG for crisp rendering at all scales (use inline SVG sprite)

#### Deliverables
- ✅ Full game playable with Xbox/PlayStation controller
- ✅ All interactive elements have ARIA labels and roles
- ✅ Keyboard-only navigation works end-to-end (Tab, arrows, Enter, Esc)
- ✅ Colorblind mode uses shapes + colors
- ✅ Layout adapts at 3 breakpoints; touch targets ≥44px
- ✅ UI scale slider works 0.8×–1.5×

#### Files
```
scripts/gamepad-manager.js       [NEW  ~250 lines]
scripts/accessibility.js         [NEW  ~150 lines]
styles/tokens.css                [MODIFY - add breakpoints, --ui-scale]
styles/base.css                  [MODIFY - responsive utilities]
styles/components.css            [MODIFY - responsive panels, touch targets]
styles/screens.css               [MODIFY - responsive menus]
styles/turn-based.css            [MODIFY - responsive HUD/action panel]
scripts/renderer.js              [MODIFY - SVG icon sprites for overlays]
```

---

### Day 7 (Sun): Integration Testing, Polish & Full Playthrough

**Goal**: End-to-end testing of all gameplay modes, performance optimization, and final polish.

#### Tasks

**7.1 End-to-End Playthrough Tests** (`tests/` — MODIFY/NEW)
- **Scenario A**: Human attacker vs. AI defender — full game from login → role select → briefing → 10 turns → debrief
- **Scenario B**: Human defender vs. AI attacker — verify defender-specific UI (alert meter, detection actions)
- **Scenario C**: Tutorial flow — verify all 8–10 steps complete without errors
- **Scenario D**: Gamepad-only playthrough — verify all game functions accessible
- **Scenario E**: Keyboard-only playthrough — verify Tab/arrow/Enter navigation
- **Scenario F**: CLI-only playthrough — every action via typed commands

**7.2 Cross-Input Consistency Test**
- Perform same action via mouse click, keyboard hotkey, CLI command, and gamepad
- Verify identical backend result and UI feedback in all 4 cases

**7.3 Performance Optimization**
- Profile with Chrome DevTools:
  - Target: 60fps during map interaction (Three.js)
  - Target: <100ms UI response to action results
  - Target: <16ms per render frame
- Optimize: lazy-load tutorial assets, debounce tooltip rendering, use `requestIdleCallback` for log panel updates
- Bundle size audit: ensure no unnecessary imports

**7.4 Visual Polish**
- Consistent animation timing (200ms for panels, 300ms for overlays)
- Loading states: spinner while waiting for backend response
- Error states: "Connection lost" banner with retry
- Empty states: "No events yet" in log panel

**7.5 Accessibility Audit**
- Run axe-core on all screens; fix critical/serious violations
- Test with NVDA/VoiceOver on at least login + game screen
- Verify color contrast ratios ≥4.5:1 for text

**7.6 Documentation**
- Update `README.md` with v3.2 gameplay instructions
- Add `CONTROLS.md` with full keyboard/CLI/gamepad reference
- Screenshot gallery of new UI states

#### Deliverables
- ✅ 6 E2E scenarios pass without errors
- ✅ All 4 input methods produce identical results
- ✅ 60fps during gameplay; <100ms action response
- ✅ Zero critical accessibility violations
- ✅ Documentation updated

#### Files
```
tests/e2e_v32_playthrough.js     [NEW  ~400 lines]
tests/test_input_parity.js       [NEW  ~150 lines]
README.md                        [MODIFY]
docs/CONTROLS.md                 [NEW  ~100 lines]
```

---

## File Summary

### New Files (17)

| File | Lines | Day |
|------|------:|-----|
| `scripts/state-machine.js` | ~120 | 1 |
| `scripts/turn-controller.js` | ~300 | 1 |
| `scripts/game-events.js` | ~60 | 1 |
| `scripts/fog-of-war.js` | ~100 | 2 |
| `scripts/components/NodeTooltip.js` | ~80 | 2 |
| `scripts/components/ContextMenu.js` | ~100 | 2 |
| `scripts/components/LogPanel.js` | ~200 | 3 |
| `scripts/components/Toast.js` | ~60 | 3 |
| `scripts/cli/command-parser.js` | ~250 | 4 |
| `scripts/cli/autocomplete.js` | ~120 | 4 |
| `scripts/hotkey-manager.js` | ~150 | 4 |
| `scripts/components/Briefing.js` | ~150 | 5 |
| `scripts/components/Debrief.js` | ~150 | 5 |
| `scripts/components/PauseMenu.js` | ~80 | 5 |
| `scripts/components/HelpOverlay.js` | ~120 | 5 |
| `scripts/tutorial/tutorial-engine.js` | ~300 | 5 |
| `scripts/tutorial/tutorial-steps.js` | ~150 | 5 |
| `scripts/gamepad-manager.js` | ~250 | 6 |
| `scripts/accessibility.js` | ~150 | 6 |
| **Total new** | **~2,940** | |

### Modified Files (12)

| File | Changes | Day |
|------|---------|-----|
| `scripts/main.js` | State machine, role select, hotkey wiring | 1, 4, 5 |
| `scripts/game-engine.js` | Remove game loop, keep renderer | 1 |
| `scripts/renderer.js` | Interaction layer, overlays, SVGs | 2, 6 |
| `scripts/terminal-manager.js` | CLI parser integration, GUI sync | 4 |
| `scripts/components/TurnHUD.js` | Live state binding, resources | 3 |
| `scripts/components/ActionMenu.js` | Context filtering, hotkeys, CLI preview | 3 |
| `scripts/animations/ActionFeedback.js` | Wire to turn controller | 3 |
| `styles/tokens.css` | Breakpoints, --ui-scale | 6 |
| `styles/base.css` | Responsive utilities | 6 |
| `styles/components.css` | Overlays, tooltips, touch targets | 2, 6 |
| `styles/screens.css` | Briefing, debrief, responsive menus | 5, 6 |
| `styles/turn-based.css` | Log panel, toast, responsive HUD | 3, 6 |

---

## Dependency Changes

```json
{
  "devDependencies": {
    "axe-core": "^4.8.0"
  }
}
```

No other new dependencies. Gamepad API is browser-native. SVG icons are inline.

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Globe.gl click events unreliable | Medium | High | Fallback to Three.js raycaster directly |
| Backend API not matching expected schema | Medium | Medium | Mock API responses for frontend-first dev |
| Gamepad dead zones vary by controller | Low | Low | Configurable dead zone in settings |
| Tutorial step validation too rigid | Medium | Medium | Allow "skip step" after 30s timeout |
| Performance drop with fog-of-war rendering | Low | Medium | Use GPU instancing for node overlays |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Full game playable (login → debrief) | ✅ Human vs. AI both roles |
| All 15 actions via GUI | ✅ Context-filtered |
| All 15 actions via CLI | ✅ Parsed + synced |
| Keyboard-only playthrough | ✅ No mouse required |
| Gamepad playthrough | ✅ No keyboard required |
| Tutorial completion | ✅ 8–10 steps, no errors |
| Accessibility (axe-core) | 0 critical violations |
| Frame rate during gameplay | ≥60fps |
| Action response time (UI) | <100ms |
| Responsive at 768px | ✅ Usable on tablet |

---

## Daily Standup Checklist

Each day ends with:
1. Run `npm run dev` — game loads without console errors
2. Play 3 turns as attacker and 3 as defender
3. Verify the day's specific deliverables listed above
4. Commit with message: `feat(v3.2): day N — [summary]`

---

**Last Updated**: March 19, 2026  
**Plan Version**: 3.2.0  
**Status**: ✅ COMPLETE — All 7 Days Delivered  

### Implementation Summary

| Day | Status | Key Deliverables |
|-----|--------|-----------------|
| 1 | ✅ Done | `state-machine.js`, `turn-controller.js`, `game-events.js`, API extensions |
| 2 | ✅ Done | `fog-of-war.js`, `NodeTooltip.js`, `ContextMenu.js` |
| 3 | ✅ Done | `TurnHUD.js` wired, `ActionMenu.js` wired, `LogPanel.js`, `Toast.js` |
| 4 | ✅ Done | `command-parser.js`, `autocomplete.js`, `hotkey-manager.js` |
| 5 | ✅ Done | `Briefing.js`, `Debrief.js`, `PauseMenu.js`, `HelpOverlay.js`, Tutorial engine |
| 6 | ✅ Done | `gamepad-manager.js`, `accessibility.js`, responsive CSS |
| 7 | ✅ Done | Role Select view, scenario system, 172 unit + 29 E2E tests, CONTROLS.md, README |

### Test Results
- **Unit tests**: 172/172 passing (Vitest)
- **E2E tests**: 29/29 passing (Playwright)
- **Total new modules**: 19 files, ~3,200 lines
- **Scenario**: Operation Crimson Tide (asymmetric 16-node) fully designed
