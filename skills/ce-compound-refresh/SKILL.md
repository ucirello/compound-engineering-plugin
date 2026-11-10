---
name: ce-compound-refresh
description: Old name for refreshing learnings, which now lives in `ce-compound`. Use only when a prompt or standing instruction names `ce-compound-refresh`; use `ce-compound` for every other learnings audit.
argument-hint: "[optional: scope hint — directory, filename, module, or keyword] [mode:non-interactive] "
---

# Compound Refresh (deprecated)

This name still works, so existing prompts and schedules keep running. The refresh itself now lives in `ce-compound`.

**Done:** the notice was shown before and after the refresh, and the refresh ran with the scope and mode it was asked for.

Render invocations in the notice as OpenCode commands: `/skill-name`. Output one form only.

Do these in order:

1. Print this notice, unchanged apart from the rendering:

   > ⚠️ `/ce-compound-refresh` has merged into `/ce-compound` and will go away in an upcoming release. This run continues as normal. Next time, use `/ce-compound refresh`.

   If your arguments contain `mode:non-interactive` or `mode:headless`, end the notice with this instead, because nobody is present and the plain word would run a capture: Next time, use `/ce-compound mode:refresh mode:non-interactive`.

2. Load the `ce-compound` skill through OpenCode's native skill tool and follow it with `mode:refresh` followed by every argument you received, unchanged. `mode:refresh` must be present: without it, an unattended run does a capture rather than a refresh. This alias does not launch a separate harness or override the delegated skill's permission, model, or depth requirements.
3. When that finishes, print the notice again as your last line. A refresh report is long, and a scheduled run may show only its final message.
