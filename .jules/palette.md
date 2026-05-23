## 2024-05-24 - Accessibility for Icon-only Modal Controls
**Learning:** Found a recurring pattern in the application where modal close and toggle buttons (using characters like '×' or '\u2715') lack accessible labels. This makes them essentially invisible or confusing for screen reader users, who will just hear "button" or the generic character name.
**Action:** When adding new modals, side panels, or overlays, always ensure that icon-only interactive controls include a descriptive `aria-label` (e.g., `aria-label="Close settings"`).
