# Design Synchronization Instructions

Compare the supplied Figma node with the running implementation and correct observable visual differences within the assigned scope.

1. Read the Figma node's layout, typography, spacing, colors, borders, shadows, assets, breakpoints, and interaction states; capture a reference image.
2. Open the supplied implementation URL with available browser tooling and capture desktop and mobile states.
3. Record each discrepancy with element, observed value, expected value, severity, and exact correction.
4. Apply fixes using the project's active frontend conventions and existing design system. Prefer existing tokens and components over arbitrary values.
5. Preserve responsive flow, accessibility, dark mode, and parent/child width responsibilities. Do not impose a universal layout pattern where the existing system differs.
6. Reinspect the component in surrounding pages and rerun visual comparison until remaining differences are intentional or blocked.

Do not broaden product behavior, invent missing design decisions, or modify unrelated files. Return changed paths, comparison evidence, remaining differences, and blockers. Do not describe, split, squash, rebase, bookmark, fetch, or push Jujutsu changes.
