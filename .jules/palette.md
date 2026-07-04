## 2024-10-27 - Icon-Only Button ARIA Labels
**Learning:** Found several "close" buttons in modal/panel headers (Settings, Diplomacy, Sentinel Lab) that only used the `×` character without any accessible text (`aria-label`).
**Action:** When adding new panels or overlays in the future, always ensure icon-only buttons include an `aria-label` describing the action (e.g., "Close Settings").
