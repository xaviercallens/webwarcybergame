## 2024-05-24 - [ARIA labels for icon-only close buttons]
**Learning:** [Missing ARIA labels on icon-only close buttons in various UI components causes accessibility issues. These buttons were using simple text nodes like '×' or '✕' which are not descriptive for screen readers.]
**Action:** [Always add explicit `aria-label` attributes to icon-only buttons (e.g. `aria-label="Close panel"`) to maintain screen reader accessibility, matching the best practices and existing memory instructions.]
