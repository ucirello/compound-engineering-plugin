# Composing the title and body: evidence and teaching gates

**You MUST read `references/pr-description-writing.md`** in full. It owns value-first framing, sizing, program altitude, related-work references, and the pre-apply audit. Preserve existing `Related:` and `Fixes` references on rewrite. Pass the PR ref when mode dispatch identified one. In Stack mode, Step 5 follows the post-submit route in `references/stack-submit.md` instead of composing one default-base body here.

**Evidence decision** before composition. Use available capture capabilities or user-supplied artifacts. Never invent or upload evidence or launch another skill for capture.

1. **User supplied** (URL, markdown image/embed, local path) — incorporate as `## Demo`, `## Screenshots`, or `## Evidence`.
2. **User asked for evidence but supplied none** — ask for the artifact or tell them to capture it and return.
3. **No material observable claim** (internal plumbing, type-only, pure refactor, inert docs) — skip without asking. Classify by runtime purpose, not extension (runtime agent instructions / config / product content / policy YAML is not auto-skippable as "docs").
4. **Otherwise** (UI, CLI, API, workflow, ranking, deploy/config behavior) — concise validation note of what was exercised; if a real run was impossible (credentials, paid services, deploy-only, hardware, missing setup), say so. Do not block PR creation for missing visuals; test/manual notes are fine — never label test output "Demo" or "Screenshots."

**Concept teaching gate** before composition. Use the workspace root gathered in Context, resolving it with `jj workspace root` when description-only or update mode skipped the Context snapshot, and apply the ordinary-key rule below.

<!-- rocketclaw-config-layers:start -->
**Resolve ordinary YAML keys from the two workspace files.**

- **Read** `<workspace-root>/.rocketclaw/config.local.yaml`, then `config.yaml` (`<workspace-root>` = `jj workspace root`). Missing files are skipped. Ignore rules do not change resolution.
- **Win** with the first active (non-commented) value. For scalars, empty is unset; an invalid value continues to the next layer, then the skill default. For lists and maps, a present key — including an empty list or map — replaces the whole key.
- **Do not** use this rule for `docs_root` — that key is `config.yaml` only.
<!-- rocketclaw-config-layers:end -->

Only an **active (non-commented)** `pr_teaching_section:` key counts — lines starting with `#` are YAML comments; matching commented template keys would silently flip the gate. Off only when the winning active value is exactly `false`; missing key or any other value → default **on**. Same cascade resolves `pr_teaching_archive:` — on only when the winning active value is exactly `true`, else **off**; per-run `archive:on|off` overrides for this invocation.

- Gate **on** — judge novelty and compose per **Step B2** of the reference. When off, skip judgment, section, Step 5 trailer/offer, and archival entirely.
- Gate **off** — compose without concept handling.

Then continue with the reference, including Step B2 when the teaching gate is on. Its final pre-apply audit must run before the body is returned.
