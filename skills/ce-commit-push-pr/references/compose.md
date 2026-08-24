# Composition gates

Read `references/pr-description-writing.md` in full. Pass a supplied or discovered PR URL so PR mode uses the exact base, head, and existing body. In Stack mode, compose each newly created PR from its own immediate-parent range after submit.

## Evidence

Use user-supplied or harness-captured evidence when it changes confidence in a material observable claim. If evidence was requested but absent, ask for it or report what is needed. For changes without an observable runtime claim, omit evidence. Otherwise state what was exercised and any real limitation; never invent or upload evidence, and never label test output as a visual demo.

## Teaching

Resolve the workspace with `jj workspace root`. Read ordinary settings from `<workspace-root>/.rocketclaw/config.local.yaml`, then `<workspace-root>/.rocketclaw/config.yaml`; the first active valid scalar wins, while a present list or map replaces the lower layer. Missing files are skipped. `docs_root` remains config-only as defined in `SKILL.md`.

Only active YAML keys count. `pr_teaching_section` defaults on and is off only for the winning exact boolean `false`. `pr_teaching_archive` defaults off and is on only for the winning exact boolean `true`; `archive:on|off` overrides it for this run. When teaching is off, skip concept judgment, archival, and the concept trailer.

## Actor fields

Do not append creator identity or product-marketing material. When a project-required field asks for a neutral actor identity, use `ai:assistant` for a machine value or `AI Assistant` for prose. Preserve any runtime-required model, provider, or harness disclosure exactly as the project's active contract requires; neutral actor values do not replace those mechanics.

Continue through every step in `references/pr-description-writing.md`, including its final coverage audit.
