## 2024-06-20 - Missing ARIA Labels on Icon-only Close/Toggle Buttons
**Learning:** I found that several components in this design system (`MissionPanel`, `HelpOverlay`) use custom icon-only toggle/close buttons (e.g., `\u2715` or `×`) without explicit `aria-label` attributes. This breaks accessibility for screen reader users who cannot interpret the visual meaning of the icons.
**Action:** When working on future components, explicitly search for icon-only buttons (`class=".*toggle.*"`, `class=".*close.*"`) and ensure they possess descriptive `aria-label`s.
