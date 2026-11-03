---
name: ce-compound-refresh
description: Old name for refreshing learnings, which now lives in `ce-compound`. Use only when a prompt or standing instruction names `ce-compound-refresh`; use `ce-compound` for every other learnings audit.
argument-hint: "[optional: scope hint — directory, filename, module, or keyword] [mode:non-interactive] "
---

# Learnings Refresh (deprecated alias)

This name still works, so existing prompts and schedules keep running. The refresh itself now lives in `ce-compound`.

**Done:** the notice was shown before and after the refresh, and the refresh ran with the scope and mode it was asked for.

Render the invocations in the notice using OpenCode's `/skill-name` form.

Do these in order:

1. Print this notice, unchanged apart from the rendering:

   > ⚠️ `/ce-compound-refresh` has merged into `/ce-compound` and will go away in an upcoming release. This run continues as normal. Next time, use `/ce-compound refresh`.

   If your arguments contain `mode:non-interactive` or `mode:headless`, end the notice with this instead, because nobody is present and the plain word would run a capture: Next time, use `/ce-compound mode:refresh mode:non-interactive`.

2. Load and follow the `ce-compound` skill in the current OpenCode session with `mode:refresh` followed by every argument you received, unchanged. This alias forwards to a skill, not a separate agent or another harness. `mode:refresh` must be present: without it, an unattended run does a capture rather than a refresh. Preserve the target skill's permission, model-selection, and nesting-capacity requirements if its workflow delegates work; this alias grants no additional permission.
3. When that finishes, print the notice again as your last line. A refresh report is long, and a scheduled run may show only its final message.
