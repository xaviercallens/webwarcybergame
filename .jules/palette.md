## 2024-05-02 - Icon-Only Buttons Missing ARIA Labels
**Learning:** Icon-only close buttons (using `×` or `\u2715`) inside overlays and modals lack accessibility information for screen readers out-of-the-box in this codebase's modal templates.
**Action:** When working on modals/panels (like Settings, Diplomacy, Sentinel Lab, Help, Mission Panel), always attach `aria-label` attributes to the close buttons or any icon-only toggle buttons to preserve keyboard/screen reader accessibility.
