## 2024-05-30 - [Missing ARIA labels on modal close buttons]
**Learning:** Found a recurring accessibility issue where icon-only close buttons in various modals/overlays (Settings, Diplomacy, Sentinel, Help, Mission Panel) lacked `aria-label` attributes.
**Action:** Always ensure that icon-only buttons, especially those using symbols like '×' or '\u2715', include descriptive `aria-label` attributes for screen readers. Added ARIA labels to the close buttons across the app.
