# Neo-Hack: Gridlock v3.2 — Controls Reference

## Keyboard Shortcuts (Global)

| Key | Action | Context |
|-----|--------|---------|
| `Esc` | Cancel / Close panel / Pause menu | Everywhere |
| `F1` | Open Help overlay | Everywhere |
| `` ` `` or `/` | Toggle CLI console | Game view |
| `Tab` | Cycle focus: Map → Actions → Log | Game view |
| `Space` | Confirm action / End turn | Game view |
| `L` | Toggle log panel | Game view |
| `M` | Toggle mission panel | Game view |
| `H` | Toggle hint highlights | Game view |

## Action Hotkeys (Game View — Action Panel Focused)

| Key | Action (Attacker) | Action (Defender) |
|-----|-------------------|-------------------|
| `1` | Scan Network | Monitor Logs |
| `2` | Exploit Vulnerability | Scan for Malware |
| `3` | Phishing | Apply Patch |
| `4` | Install Malware | Isolate Host |
| `5` | Elevate Privileges | Restore Backup |
| `6` | Lateral Movement | Firewall Rule |
| `7` | Exfiltrate Data | Incident Response |

## Map Navigation

| Input | Action |
|-------|--------|
| `Arrow Keys` / `WASD` | Navigate between adjacent nodes |
| `+` / `-` | Zoom in / out |
| `Click` | Select node |
| `Right-click` | Context menu (available actions) |
| `Mouse wheel` | Zoom (centered on cursor) |
| `Click-drag` (empty space) | Pan / rotate globe |

## CLI Commands

### Attacker Commands

| Command | Alias | Syntax | Description |
|---------|-------|--------|-------------|
| `scan` | `s` | `scan <target>` | Scan host for vulnerabilities |
| `exploit` | `e` | `exploit <target> [--vuln=ID]` | Exploit a found vulnerability |
| `phish` | `ph` | `phish <target>` | Social engineering attack |
| `malware` | `mw` | `malware <target>` | Install persistent malware |
| `elevate` | `el` | `elevate <target>` | Escalate to admin access |
| `move` | `mv` | `move <target>` | Lateral movement to adjacent node |
| `exfiltrate` | `ex` | `exfiltrate <target>` | Steal data from compromised host |
| `clearlogs` | `cl` | `clearlogs` | Remove evidence from logs |

### Defender Commands

| Command | Alias | Syntax | Description |
|---------|-------|--------|-------------|
| `monitor` | `mon` | `monitor` | Check system logs for anomalies |
| `scanmal` | `sm` | `scanmal <target>` | Scan host for malware |
| `patch` | `p` | `patch <target>` | Apply security patch |
| `isolate` | `iso` | `isolate <target>` | Quarantine host from network |
| `restore` | `rb` | `restore <target>` | Restore system from backup |
| `firewall` | `fw` | `firewall <target>` | Add firewall rule |
| `respond` | `ir` | `respond <target>` | Active countermeasure |

### Meta Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `status` | — | Show network status summary |
| `endturn` | `et`, `end` | End your turn |
| `help` | `h`, `?` | Show command help |
| `clear` | — | Clear terminal output |

### CLI Tips

- **Tab completion**: Press `Tab` to auto-complete commands and node names
- **History**: `↑`/`↓` arrows navigate command history
- **Target shortcuts**: If a node is selected on the map, commands without `<target>` use the selected node
- **Prefix optional**: Both `scan host` and `/scan host` work

## Gamepad Controls (Xbox / PlayStation)

| Button | Xbox | PlayStation | Action |
|--------|------|-------------|--------|
| Left Stick / D-pad | — | — | Navigate between nodes |
| A | A | × | Select node / Confirm action |
| B | B | ○ | Cancel / Back / Close |
| X | X | □ | Open action menu |
| Y | Y | △ | Toggle log panel |
| LB | LB | L1 | Previous action in list |
| RB | RB | R1 | Next action in list |
| LT | LT | L2 | Zoom out |
| RT | RT | R2 | Zoom in |
| Start | ☰ | Options | Pause menu |
| Select | ⧉ | Share | Toggle CLI console |

## Accessibility

- **Reduced motion**: Respects `prefers-reduced-motion` system setting
- **High contrast**: Enable in Settings → Accessibility
- **UI Scale**: Adjustable 0.8×–1.5× in Settings
- **Screen reader**: All interactive elements have ARIA labels; action results and turn changes announced via live regions
- **Keyboard-only**: Full gameplay possible without mouse (Tab + Arrows + Enter + Esc)
- **Focus indicators**: Visible focus ring on all focusable elements
